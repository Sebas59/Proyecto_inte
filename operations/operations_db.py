from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import List, Optional
from data.models import Vehiculo, Tipo_combustibleEnum
from data.schemas import VehiculoCreate
from fastapi import Form

def vehiculo_create_form(
    marca: str = Form(...),
    modelo: Optional[str] = Form(...),
    Tipo_combustible: Optional[Tipo_combustibleEnum] = Form(None),
    Tan_size: Optional[float] = Form(0.0),
    year: Optional[int] = Form(...)
) -> VehiculoCreate:
    return VehiculoCreate(
        marca=marca,
        modelo=modelo,
        Tipo_combustible=Tipo_combustible,
        Tan_size=Tan_size,
        year=year
    )

async def crear_vehiculo_db(vehiculo:VehiculoCreate, session:AsyncSession)->Vehiculo:
    nuevo_vehiculo = Vehiculo(**vehiculo.dict())
    session.add(nuevo_vehiculo)
    try:
        await session.commit()
        await session.refresh(nuevo_vehiculo)
        return nuevo_vehiculo
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al crear el vehiculo")
    
async def obtener_vehiculos_db(session:AsyncSession)->List[Vehiculo]:
    result = await session.execute(select(Vehiculo))
    vehiculos = result.scalars().all()
    return vehiculos
