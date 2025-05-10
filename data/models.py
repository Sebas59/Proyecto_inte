from sqlmodel import SQLModel, Field,Relationship
from typing import Optional
from sqlalchemy import Enum as SqlEnum
from datetime import datetime
from enum import Enum

class Tipo_combustibleEnum(str,Enum):
    gasolina = "Gasolina"
    diesel = "Diesel"
    

class Vehiculo(SQLModel, table=True):
    __tablename__ = "Vehiculo"
    id: Optional[int] = Field(default=None, primary_key=True)
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float
