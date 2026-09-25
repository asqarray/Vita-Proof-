import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./vitaproof_telemetry.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"
    id = Column(Integer, primary_key=True, index=True)
    cert_id = Column(String(64), index=True, nullable=False)
    state_hash = Column(String(64), nullable=False)
    cpu_cycles = Column(Integer, nullable=False)
    tx_signature = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(32), default="INGESTED")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
