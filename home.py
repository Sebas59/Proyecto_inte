from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, RedirectResponse


from data.models import *
from utils.connection_db import *
from data.schemas import *
from operations.operations_db import ( 
    obtener_vehiculos_db,
    crear_vehiculo_db,
    actualizar_vehiculo_db,
    eliminar_vehiculo_db,
    obtener_vehiculo_por_marca_modelo_db,
    vehiculo_create_form, 
    combustible_create_form, 
    crear_combustible_precio_db, 
    obtener_precio_combustible_db, 
    actualizar_precio_combustible_db, 
    eliminar_precio_combustible_db, 
    obtener_vehiculos_con_costo_combustible_db 
)



@asynccontextmanager
async def lifespan(app: APIRouter):
    await init_db()
    yield

templades = Jinja2Templates(directory="templates")
router = APIRouter(lifespan=lifespan)

@router.get("/", response_class=HTMLResponse)
async def leer_home(request: Request):
    return templades.TemplateResponse("home.html", {"request": request})

@router.get("/vehiculos", tags=["Vehículos"])
async def vehiculos_list_html(request: Request, session : AsyncSession = Depends(get_session)):
    vehiculos = await obtener_vehiculos_db(session)
    return templades.TemplateResponse("vehiculos.html", {
        "request": request,
        "sesions": vehiculos, 
        "title": "Lista de Vehículos"})

@router.get("/vehiculos/crear", tags=["Vehículos"])
async def vehiculo_create_html(request:Request, session:AsyncSession = Depends(get_session)):
    return templades.TemplateResponse("vehiculo_create.html", {
        "request": request,
        "title": "Crear Vehículo",
        "Tipo_combustibleEnum":Tipo_combustibleEnum
    })

@router.post("/vehiculos/crear", tags=["Vehículos"]) 
async def create_vehiculo(
    request: Request,
    vehiculo_data: VehiculoCreate = Depends(vehiculo_create_form), 
    session: AsyncSession = Depends(get_session)
):
    """Procesa el formulario y crea un nuevo vehículo."""
    try:
        nuevo_vehiculo = await crear_vehiculo_db(vehiculo_data, session)
        return RedirectResponse(url="/vehiculos", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return templades.TemplateResponse(
            "vehiculo_create.html",
            {
                "request": request,
                "title": "Crear Vehículo",
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "error_message": e.detail 
            },
            status_code=e.status_code
        )
    except Exception as e:
        return templades.TemplateResponse(
            "vehiculo_create.html",
            {
                "request": request,
                "title": "Crear Vehículo",
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "error_message": f"Ocurrió un error inesperado: {e}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
