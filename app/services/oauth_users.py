from fastapi import HTTPException
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables

tables = Tables()
PROVIDER_COLUMNS = {
    "google": "google_id",
    "github": "github_id",
    "linkedin": "linkedin_id",
}


async def resolve_oauth_user(
    db: AsyncSession,
    *,
    provider: str,
    provider_id: str,
    email: str,
    full_name: str | None,
) -> dict:
    provider_column_name = PROVIDER_COLUMNS[provider]
    provider_column = getattr(tables.users.c, provider_column_name)
    normalized_email = email.strip().lower()
    if not normalized_email or not provider_id:
        raise HTTPException(
            status_code=400,
            detail="The provider did not return a usable identity",
        )

    by_provider = await db.execute(
        select(tables.users).where(provider_column == provider_id)
    )
    existing = by_provider.mappings().first()

    if existing is None:
        by_email = await db.execute(
            select(tables.users).where(tables.users.c.email.ilike(normalized_email))
        )
        existing = by_email.mappings().first()

    try:
        if existing is not None:
            user = dict(existing)
            if not user.get("is_active", False):
                raise HTTPException(status_code=403, detail="This account is inactive")
            linked_id = user.get(provider_column_name)
            if linked_id and linked_id != provider_id:
                raise HTTPException(
                    status_code=409,
                    detail="This email is already linked to a different provider account",
                )

            values = {provider_column_name: provider_id}
            if not user.get("full_name") and full_name:
                values["full_name"] = full_name.strip()[:255]
            updated = await db.execute(
                update(tables.users)
                .where(tables.users.c.id == user["id"])
                .values(**values)
                .returning(tables.users)
            )
            await db.commit()
            return dict(updated.mappings().one())

        created = await db.execute(
            insert(tables.users)
            .values(
                email=normalized_email,
                full_name=(full_name or "").strip()[:255] or None,
                is_active=True,
                **{provider_column_name: provider_id},
            )
            .returning(tables.users)
        )
        await db.commit()
        return dict(created.mappings().one())
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this identity already exists",
        ) from None
