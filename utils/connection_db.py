import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from data.models import Vehiculo


CLEVER_DB = "postgresql+asyncpg://proyecto_yd8z_user:GP1h1h5Uc1QkPO8QOwtlMewbaTU7z5vM@dpg-d0uedu6mcj7s739jqui0-a.oregon-postgres.render.com/proyecto_yd8z"

engine: AsyncEngine = create_async_engine(CLEVER_DB, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with async_session() as session:
        yield session



