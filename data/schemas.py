from sqlmodel import SQLModel
from data.models import *
from typing import Optional

class VehiculoCreate(SQLModel):
    marca: str
    modelo: str
    year: int
    Tipo_combustible: str
    Tan_size: float

class VehiculoRead(SQLModel):
    id: Optional[int] = None
    marca: str
    modelo: str
    year: int
    Tipo_combustible: str
    Tan_size: float

    class Config:
        orm_mode = True