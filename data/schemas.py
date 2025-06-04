from sqlmodel import SQLModel
from data.models import *
from typing import Optional
from fastapi import Form, UploadFile, File


class VehiculoCreate(SQLModel):
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float
    imagen_url: Optional[str] = Field(default=None)

class VehiculoRead(SQLModel):
    id: Optional[int] = None
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float
    imagen_url: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True

class VehiculoHistoricoRead(SQLModel):
    id: Optional[int] = None
    original_id: int
    marca: str
    modelo: str
    year: int
    Tipo_combustible: Tipo_combustibleEnum
    Tan_size: float
    imagen_url: Optional[str] = Field(default=None)

    class Config:
        orm_mode = True

class VehiculoCreateForm:
    def __init__(
        self,
        marca: str = Form(...),
        modelo: str = Form(...),
        year: int = Form(...),
        Tipo_combustible: Tipo_combustibleEnum = Form(...),
        Tan_size: float = Form(...),
        imagen: Optional[UploadFile] = File(None)
    ):
        self.marca = marca
        self.modelo = modelo
        self.year = year
        self.Tipo_combustible = Tipo_combustible
        self.Tan_size = Tan_size
        self.imagen = imagen


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
    