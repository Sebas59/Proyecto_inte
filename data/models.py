from sqlmodel import SQLModel, Field,Relationship
from typing import Optional
from sqlalchemy import Enum as SqlEnum,column,String
from datetime import datetime
from enum import Enum

class Tipo_combustibleEnum(str, Enum):
    corriente = "corriente"
    diesel = "diesel"
    super_ = "super"
    gas = "gas"
    
class Vehiculo(SQLModel, table=True):
    __tablename__ = "Vehiculo"
    id: Optional[int] = Field(default=None, primary_key=True)
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Optional[Tipo_combustibleEnum] = Field(sa_column=column(SqlEnum(Tipo_combustibleEnum)))
    Tan_size: float
    imagen_url: Optional[str] = Field(default=None)

class Combustible(SQLModel, table=True):
    __tablename__ = "Combustible"
    id: Optional[int] = Field(default=None, primary_key=True)
    ciudad: str
    localidad: str
    tipo_combustible: Optional[Tipo_combustibleEnum] = Field(sa_column=column(SqlEnum(Tipo_combustibleEnum)))
    precio_por_galon: float

class CombustibleHistorico(SQLModel, table=True):
    __tablename__ = "CombustibleHistorico"
    id: Optional[int] = Field(default=None, primary_key=True)
    original_id: int
    ciudad: str
    localidad: str
    tipo_combustible: Optional[Tipo_combustibleEnum] = Field(sa_column=column(SqlEnum(Tipo_combustibleEnum)))
    precio_por_galon: float

class VehiculoHistorico(SQLModel, table=True):
    __tablename__ = "VehiculoHistorico"
    id: Optional[int] = Field(default=None, primary_key=True)
    original_id: int
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Optional[Tipo_combustibleEnum] = Field(sa_column=column(SqlEnum(Tipo_combustibleEnum)))
    Tan_size: float
    imagen_url: Optional[str] = Field(default=None)