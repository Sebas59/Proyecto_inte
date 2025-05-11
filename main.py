from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status,Form
from utils.connection_db import init_db
from utils.connection_db import init_db, get_session
from data.models import Vehiculo
from data.schemas import VehiculoCreate, VehiculoRead

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from typing import List,Optional
from operations.operations_db import *
from data.models import *
from sqlmodel import Field, SQLModel,Session,select

@asynccontextmanager
async def lifespan(app:FastAPI):
    await init_db()
    yield
app = FastAPI(lifespan=lifespan)

@app.post("/vehiculos/", response_model=Vehiculo,tags=["Vehiculos"])
async def crear_vehiculo(vehiculo:VehiculoCreate=Depends(vehiculo_create_form), session:AsyncSession=Depends(get_session))->Vehiculo:
    return await crear_vehiculo_db(vehiculo,session)

@app.get("/vehiculos/", response_model=List[Vehiculo], tags=["Vehiculos"])
async def obtener_vehiculos(session:AsyncSession=Depends(get_session))->List[Vehiculo]:
    return await obtener_vehiculos_db(session)

@app.put("/vehiculos/{id}", response_model=Vehiculo, tags=["Vehiculos"])
async def actualizar_vehiculo(id:int, vehiculo:VehiculoCreate=Depends(vehiculo_create_form), session:AsyncSession=Depends(get_session))->Vehiculo:
    return await actualizar_vehiculo_db(id,vehiculo,session)

@app.delete("/vehiculos/{id}", response_model=Vehiculo, tags=["Vehiculos"])
async def eliminar_vehiculo(id:int, session:AsyncSession=Depends(get_session))->Vehiculo:
    return await eliminar_vehiculo_db(id,session)