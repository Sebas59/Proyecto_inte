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

@app.get("/vehiculos/", response_model=List[VehiculoRead], tags=["Vehiculos"])
async def obtener_vehiculos(session:AsyncSession=Depends(get_session))->List[VehiculoRead]:
    return await obtener_vehiculos_db(session)

@app.put("/vehiculos/{id}", response_model=Vehiculo, tags=["Vehiculos"])
async def actualizar_vehiculo(id:int, vehiculo:VehiculoCreate=Depends(vehiculo_create_form), session:AsyncSession=Depends(get_session))->Vehiculo:
    return await actualizar_vehiculo_db(id,vehiculo,session)

@app.delete("/vehiculos/{id}", response_model=Vehiculo, tags=["Vehiculos"])
async def eliminar_vehiculo(id:int, session:AsyncSession=Depends(get_session))->Vehiculo:
    return await eliminar_vehiculo_db(id,session)

@app.get("/vehiculos/{marca}/{modelo}", response_model=List[Vehiculo], tags=["Vehiculos"])
async def obtener_vehiculos_por_marca_modelo(marca:str,modelo:str, session:AsyncSession=Depends(get_session))->List[Vehiculo]:
    return await obtener_vehiculo_por_marca_modelo_db(marca,modelo,session)

@app.post("/combustible/", response_model=Combustible, tags=["Combustible"])
async def crear_combustible(com:CombustibleCreate=Depends(combustible_create_form), session:AsyncSession=Depends(get_session))->Combustible:
    return await crear_combustible_precio_db(com,session)

@app.get("/combustible/", response_model=List[CombustibleRead], tags=["Combustible"])
async def obtener_combustible(session:AsyncSession=Depends(get_session))->List[CombustibleRead]:
    return await obtener_precio_combustible_db(session) 

@app.put("/combustible/{id}", response_model=Combustible, tags=["Combustible"])
async def actualizar_combustible_precio(id:int, combustible:CombustibleCreate=Depends(combustible_create_form), session:AsyncSession=Depends(get_session))->Combustible:
    return await actualizar_precio_combustible_db(id,combustible,session)

@app.delete("/combustible/{id}", response_model = Combustible, tags= ["Combustible"])
async def eliminar_combustible_precio(id:int, session:AsyncSession=Depends(get_session))->Combustible:
    return await eliminar_precio_combustible_db(id,session)

@app.get("/combustible/costo-tanqueo/", response_model=List[CostoTanqueo], tags=["Combustible"])
async def obtener_vehiculos_con_costo_combustible(marca:str,modelo:str,ciudad:str,localidad:str,session:AsyncSession=Depends(get_session))->List[CostoTanqueo]:
    return await obtener_vehiculos_con_costo_combustible_db(marca,modelo,ciudad,localidad,session)

@app.get("/combustible/historico/", response_model=List[CombustibleHistoricoRead], tags=["Historico Combustible"])
async def obtener_combustible_historico(session:AsyncSession=Depends(get_session))->List[CombustibleHistoricoRead]:
    result = await session.execute(select(CombustibleHistorico))
    combustible_historico = result.scalars().all()
    return combustible_historico

@app.get("/vehiculos/historico/", response_model=List[VehiculoHistoricoRead], tags=["Historico Vehiculo"])
async def obtener_combustible_historico(session:AsyncSession=Depends(get_session))->List[VehiculoHistoricoRead]:
    result = await session.execute(select(VehiculoHistorico))
    vehiculo_historico = result.scalars().all()
    return vehiculo_historico