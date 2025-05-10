from sqlmodel import SQLModel,Form,Field
from data.models import *
from typing import Optional

class VehiculoCreate(SQLModel):
    marca: str = Form(...), 
    modelo: Optional[str] = Form(...),
    Tipo_combustible: Optional[Tipo_combustibleEnum] = Form(None),
    Tan_size: Optional[float] = Form(default=0.0),

class VehiculoRead(SQLModel):
    id: Optional[int] = None
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float

    class Config:
        orm_mode = True