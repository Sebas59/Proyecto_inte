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
    Tipo_combustible: Tipo_combustibleEnum
    precio_por_galon: float

class CombustibleRead(SQLModel):
    id: Optional[int] = None
    ciudad: str
    tipo_combustible: Tipo_combustibleEnum
    precio_por_galon: float

    class Config:
        orm_mode = True