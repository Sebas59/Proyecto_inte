from sqlmodel import SQLModel, Field,Relationship
from typing import Optional
from sqlalchemy import Enum as SqlEnum
from datetime import datetime
import enum

class Vehiculo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    marca: str
    modelo: str
    year: int
    Tipo_combustible: str
    Tan_size: float
    