from functools import lru_cache

from sqlalchemy import MetaData
from db.session import engine


@lru_cache()
class Tables:
    def __init__(self):
        self.metadata = MetaData()

    async def reflect_metadata(self):
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

    @property
    def focus_sessions(self):
        return self.metadata.tables.get("focus_sessions")
