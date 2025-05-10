from sqlmodel import SQLModel
from data.models import *
from typing import Optional

class VehiculoCreate(SQLModel):
    marca: str
    modelo: str
    year: int
    Tipo_combustible: str
    Tan_size: float