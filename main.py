from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from utils.connection_db import init_db
from utils.connection_db import init_db, get_session
from data.models import Vehiculo
from data.schemas import VehiculoCreate

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from typing import List
from operations.operations_db import *

@asynccontextmanager
async def lifespan(app:FastAPI):
    await init_db()
    yield
app = FastAPI(lifespan=lifespan)

@app.post("/vehiculos/", response_model=Vehiculo,tags=["Vehiculos"])
async def crear_vehiculo(vehiculo:VehiculoCreate, session:AsyncSession=Depends(get_session))->Vehiculo:
    return await crear_vehiculo_db(vehiculo, session)