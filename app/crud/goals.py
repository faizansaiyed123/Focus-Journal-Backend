from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from db.tables import Tables
from sqlalchemy import select, insert, update
from fastapi import HTTPException, status
from schemas.goals import GoalInout
from datetime import date
from uuid import uuid4


async def create_or_update_goal_data(
    request: GoalInout, user_id: str, db: AsyncSession
) -> dict:
    goals = Tables().goals
    today = date.today()

    query = select(goals).where(goals.c.user_id == user_id, goals.c.created_at == today)

    try:
        result = await db.execute(query)
        existing_goal = result.fetchone()

        if existing_goal:
            update_query = (
                update(goals)
                .where(goals.c.id == existing_goal.id)
                .values(
                    goal=request.goal,
                    target_days=request.target_days,
                    status="in_progress",
                )
                .returning(goals)
            )
            result = await db.execute(update_query)
            updated_goal = result.fetchone()
            await db.commit()
            message = "Goal updated successfully."
            final_goal = updated_goal
        else:
            new_goal = {
                "id": str(uuid4()),
                "user_id": user_id,
                "goal": request.goal,
                "target_days": request.target_days,
                "completed_days": 0,
                "status": "in_progress",
                "created_at": today,
            }
            insert_query = insert(goals).values(**new_goal).returning(goals)
            result = await db.execute(insert_query)
            await db.commit()
            final_goal = result.fetchone()
            message = "Goal set successfully."

        data = {
            "goal": final_goal.goal,
            "target_days": final_goal.target_days,
            "created_at": final_goal.created_at.isoformat(),
            "completed_days": final_goal.completed_days,
            "status": final_goal.status,
        }

        return {"message": message, "data": data}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create or update goal: {str(e)}",
        )


async def get_user_goal_data(user_id: UUID, db: AsyncSession) -> dict:
    goals = Tables().goals

    query = (
        select(goals)
        .where(goals.c.user_id == user_id)
        .order_by(goals.c.created_at.desc())
        .limit(1)
    )

    try:
        result = await db.execute(query)
        goal = result.fetchone()

        if not goal:
            return {"message": "No goal set yet.", "data": None}

        data = {
            "goal": goal.goal,
            "target_days": goal.target_days,
            "created_at": goal.created_at.isoformat(),
            "completed_days": goal.completed_days,
            "status": goal.status,
        }

        return {"message": "Goal fetched successfully.", "data": data}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch goal: {str(e)}",
        )
