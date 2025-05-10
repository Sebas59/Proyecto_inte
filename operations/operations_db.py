from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import List
from data.models import Vehiculo
from data.schemas import VehiculoCreate

async def crear_vehiculo(vehiculo:VehiculoCreate, session:AsyncSession)->Vehiculo:
    nuevo_vehiculo = Vehiculo(**vehiculo.dict())
    session.add(nuevo_vehiculo)
    try:
        await session.commit()
        await session.refresh(nuevo_vehiculo)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Error al crear el vehiculo")