from functools import lru_cache
from sqlalchemy import MetaData
from app.db.session import engine  # AsyncEngine instance


@lru_cache()
class Tables:
    def __init__(self):
        self.metadata = MetaData()

    async def reflect_metadata(self):
        # Reflect metadata from the DB using a synchronous call wrapped in run_sync
        async with engine.connect() as conn:
            await conn.run_sync(self.metadata.reflect)

    @property
    def users(self):
        return self.metadata.tables.get("users")

    @property
    def journal_entries(self):
        return self.metadata.tables.get("journal_entries")

    @property
    def daily_checkins(self):
        return self.metadata.tables.get("daily_checkins")

    @property
    def user_streaks(self):
        return self.metadata.tables.get("user_streaks")

    @property
    def goals(self):
        return self.metadata.tables.get("goals")
