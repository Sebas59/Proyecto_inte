from sqlmodel import SQLModel
from data.models import *
from typing import Optional
from fastapi import Form

class VehiculoCreate(SQLModel):
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float

class VehiculoRead(SQLModel):
    id: Optional[int] = None
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float

    class Config:
        orm_mode = True

class CombustibleCreate(SQLModel):
    ciudad: str
    localidad: str
    tipo_combustible: Tipo_combustibleEnum
    precio_por_galon: float

class CombustibleRead(SQLModel):
    id: Optional[int] = None
    ciudad: str
    localidad: str
    tipo_combustible: Tipo_combustibleEnum
    precio_por_galon: float

    class Config:
        orm_mode = True

class CombustibleHistoricoRead(SQLModel):
    id: Optional[int] = None
    original_id: int
    ciudad: str
    localidad: str
    tipo_combustible: Tipo_combustibleEnum
    precio_por_galon: float

    class Config:
        orm_mode = True

class CostoTanqueo(SQLModel):
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float
    precio_por_galon: float
    ciudad: str
    localidad: str
    costo_total: float
    