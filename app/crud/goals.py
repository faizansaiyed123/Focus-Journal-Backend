from datetime import date
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.tables import Tables
from schemas.goals import GoalInout

tables = Tables()


def _serialize_goal(goal) -> dict:
    return {
        "id": str(goal["id"]),
        "goal": goal["goal"],
        "target_days": goal["target_days"],
        "created_at": goal["created_at"].isoformat(),
        "completed_days": goal["completed_days"],
        "status": goal["status"],
    }


async def create_or_update_goal_data(
    request: GoalInout,
    user_id: UUID,
    db: AsyncSession,
    today: date,
) -> dict:
    goals = tables.goals
    goal_text = request.goal.strip()
    if not goal_text:
        raise HTTPException(status_code=422, detail="Goal must not be blank")

    result = await db.execute(
        select(goals).where(
            goals.c.user_id == user_id,
            goals.c.created_at == today,
        )
    )
    existing = result.mappings().first()

    try:
        if existing:
            updated = await db.execute(
                update(goals)
                .where(
                    goals.c.id == existing["id"],
                    goals.c.user_id == user_id,
                )
                .values(
                    goal=goal_text,
                    target_days=request.target_days,
                    status="in_progress",
                )
                .returning(goals)
            )
            row = updated.mappings().one()
            await db.commit()
            return {
                "message": "Goal updated successfully",
                "data": _serialize_goal(row),
            }

        inserted = await db.execute(
            insert(goals)
            .values(
                id=uuid4(),
                user_id=user_id,
                goal=goal_text,
                target_days=request.target_days,
                completed_days=0,
                status="in_progress",
                created_at=today,
            )
            .returning(goals)
        )
        row = inserted.mappings().one()
        await db.commit()
        return {"message": "Goal set successfully", "data": _serialize_goal(row)}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Goal could not be saved because it conflicts with existing data",
        ) from None


async def get_user_goal_data(
    user_id: UUID,
    db: AsyncSession,
    today: date,
) -> dict:
    goals = tables.goals
    result = await db.execute(
        select(goals)
        .where(
            goals.c.user_id == user_id,
            goals.c.created_at <= today,
        )
        .order_by(goals.c.created_at.desc())
        .limit(1)
    )
    row = result.mappings().first()
    if row is None:
        return {"message": "No goal set yet", "data": None}
    return {"message": "Goal fetched successfully", "data": _serialize_goal(row)}
