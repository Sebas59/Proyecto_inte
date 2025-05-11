from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from typing import List, Optional
from data.models import *
from data.schemas import *
from fastapi import Form

def vehiculo_create_form(
    marca: str = Form(...),
    modelo: Optional[str] = Form(...),
    year: Optional[int] = Form(...),
    Tipo_combustible: Optional[Tipo_combustibleEnum] = Form(None),
    Tan_size: Optional[float] = Form(0.0)
    
) -> VehiculoCreate:
    return VehiculoCreate(
        marca=marca,
        modelo=modelo,
        year=year,
        Tipo_combustible=Tipo_combustible,
        Tan_size=Tan_size
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
    
async def obtener_vehiculos_db(session:AsyncSession)->List[VehiculoRead]:
    result = await session.execute(select(Vehiculo))
    vehiculos = result.scalars().all()
    return vehiculos

async def actualizar_vehiculo_db(id:int, vehiculo:VehiculoCreate, session:AsyncSession)->Vehiculo:
    vehiculo_actualizado = await session.get(Vehiculo, id)
    if not vehiculo_actualizado:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    for key, value in vehiculo.dict(exclude_unset=True).items():
        setattr(vehiculo_actualizado, key, value)
    session.add(vehiculo_actualizado)
    try:
        await session.commit()
        await session.refresh(vehiculo_actualizado)
        return vehiculo_actualizado
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al actualizar el vehiculo")
    
async def eliminar_vehiculo_db(id:int, session:AsyncSession)->Vehiculo:
    vehiculo_a_eliminar = await session.get(Vehiculo, id)
    if not vehiculo_a_eliminar:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    await session.delete(vehiculo_a_eliminar)
    try:
        await session.commit()
        return vehiculo_a_eliminar
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al eliminar el vehiculo")
    

async def obtener_vehiculo_por_marca_modelo_db(marca:str,modelo:str, session:AsyncSession)->List[Vehiculo]:
    result = await session.execute(
        select(Vehiculo).where(
            and_(Vehiculo.marca.ilike(f"%{marca}%"), Vehiculo.modelo.ilike(f"%{modelo}%"))
        )
    )
    vehiculos = result.scalars().all()
    if not vehiculos:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    return vehiculos

def combustible_create_form(
    ciudad: str = Form(...),
    Tipo_combustible: Tipo_combustibleEnum = Form(...),
    precio_por_galon: float = Form(...)
    
) -> CombustibleCreate:
    return CombustibleCreate(
        ciudad=ciudad,
        Tipo_combustible=Tipo_combustible,
        precio_por_galon=precio_por_galon
    )

async def crear_combustible_precio_db(combustible:CombustibleCreate, session:AsyncSession)->Combustible:
    nuevo_precio = Combustible(ciudad=combustible.ciudad, tipo_combustible=combustible.Tipo_combustible, precio_por_galon=combustible.precio_por_galon)
    session.add(nuevo_precio)
    try:
        await session.commit()
        await session.refresh(nuevo_precio)
        return nuevo_precio
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al crear el precio del combustible") 
    
async def obtener_precio_combustible_db(session:AsyncSession)->List[CombustibleRead]:
    result = await session.execute(select(Combustible))
    precio_combustible = result.scalars().all()
    return precio_combustible

async def actualizar_precio_combustible_db(id:int, combustible:CombustibleCreate, session:AsyncSession)->Combustible:
    nuevo_precio = await session.get(Combustible, id)
    if not nuevo_precio:
        raise HTTPException(status_code=404, detail="Precio de combustible no encontrado")
    for key, value in combustible.dict(exclude_unset=True).items():
        setattr(nuevo_precio, key, value)
    session.add(nuevo_precio)
    try:
        await session.commit()
        await session.refresh(nuevo_precio)
        return nuevo_precio
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al actualizar el precio del combustible")
