from fastapi import APIRouter, Depends, HTTPException, status, Form, Query,UploadFile,File
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.future import select

from data.models import *
from utils.connection_db import *
from data.schemas import *
from operations.operations_db import *

from utils.supabase_client import *
import aiofiles

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
async def vehiculos_list_html(
    request: Request,
    session : AsyncSession = Depends(get_session),
    marca : Optional[str] = Query(None, description="Filtrar por marca del vehiculo(opcional)"),
    modelo : Optional[str] = Query(None, description="Filtrar por modelo del vehiculo(opcional)"),
    vehiculo_id : Optional[str] = Query(None, description="Filtrar por ID del vehiculo(opcional)")
    ):
    
    current_marca = marca if marca else None
    current_modelo = modelo if modelo else None
   
    current_vehiculo_id = int(vehiculo_id) if vehiculo_id and vehiculo_id.isdigit() else None

    try:
        vehiculos = await obtener_vehiculos_db(
            session=session,
            marca=current_marca,
            modelo=current_modelo,
            vehiculo_id=current_vehiculo_id
        )
        error_message = None
        if not vehiculos and (current_marca or current_modelo or current_vehiculo_id):
            error_message = "No se encontraron vehículos con los criterios de búsqueda"

        return templades.TemplateResponse(
            "vehiculos.html",
            {
                "request": request,
                "vehiculos": vehiculos,
                "Tipo_combustible": Tipo_combustibleEnum,
                "Current_marca" : current_marca,
                "current_modelo" : current_modelo,
                "id_buscado" : current_vehiculo_id,
                "error_mensage" : error_message
            }
        )
    except HTTPException as e:
        return templades.TemplateResponse(
            "vehiculos.html",
            {
                "request": request,
                "vehiculos": [],
                "Tipo_combustible": Tipo_combustibleEnum,
                "Current_marca" : current_marca,
                "current_modelo" : current_modelo,
                "id_buscado" : current_vehiculo_id,
                "error_mensage" : e.detail
            },
            status_code=e.status_code
        )
    except Exception as e:
        return templades.TemplateResponse(
            "vehiculos.html",
            {
                "request": request,
                "vehiculos": [],
                "Tipo_combustible": Tipo_combustibleEnum,
                "Current_marca" : current_marca,
                "current_modelo" : current_modelo,
                "id_buscado" : current_vehiculo_id,
                "error_mensage" : f"Error inesperado: {e}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/vehiculos/crear", tags=["Vehículos"])
async def vehiculo_create_html(request:Request, session:AsyncSession = Depends(get_session)):
    return templades.TemplateResponse("vehiculo_create.html", {
        "request": request,
        "title": "Crear Vehículo",
        "Tipo_combustibleEnum":Tipo_combustibleEnum
    })

@router.post("/vehiculos/crear", tags=["Vehículos"]) 
async def crear_vehiculo(
    request: Request,
    session: AsyncSession = Depends(get_session),
    marca: str = Form(...),
    modelo: str = Form(...),
    year: int = Form(...),
    Tipo_combustible: Tipo_combustibleEnum = Form(...),
    Tan_size: float = Form(...),
    imagen: UploadFile = File(None) 
):
    try:
        vehiculo_data = VehiculoCreate(
            marca=marca,
            modelo=modelo,
            year=year,
            Tipo_combustible=Tipo_combustible,
            Tan_size=Tan_size
        )
        
        
        nuevo_vehiculo = await crear_vehiculo_db(vehiculo_data, session)

       
        if imagen and imagen.filename:
            
            upload_result = await save_file(imagen, to_supabase=True) 

            if "url" in upload_result:
                
                nuevo_vehiculo.imagen_url = upload_result["url"]
                session.add(nuevo_vehiculo) 
                await session.commit() 
                await session.refresh(nuevo_vehiculo) 
            else:
                print(f"Error uploading image: {upload_result.get('error', 'Unknown error')}")


        return RedirectResponse(url="/vehiculos_registro", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        error_message = e.detail
        return templades.TemplateResponse(
            "crear_vehiculo.html",
            {"request": request, "error_message": error_message, "form_data": await request.form(), "Tipo_combustibleEnum": Tipo_combustibleEnum} 
        )
    except Exception as e:
        error_message = f"Error inesperado: {e}"
        return templades.TemplateResponse(
            "crear_vehiculo.html",
            {"request": request, "error_message": error_message, "form_data": await request.form(), "Tipo_combustibleEnum": Tipo_combustibleEnum} 
        )


@router.get("/vehiculos_registro", tags=["Vehículos"])
async def vehiculos_registro_exitosa(request: Request):
    return templades.TemplateResponse("vehiculo_registration_success.html", {"request": request, "title": "Registro Exitoso"})

@router.get("/vehiculos_edit", tags=["Vehículos"])
async def vehiculos_edit_exitosa(request: Request):
    return templades.TemplateResponse("vehiculo_edit_success.html", {"request": request, "title": "Registro Exitoso"})

@router.get("/vehiculos_restar", tags=["Vehículos"])
async def vehiculos_restar_exitosa(request: Request):
    return templades.TemplateResponse("vehiculos_restaurar_success.html", {"request": request, "title": "Registro Exitoso"})

@router.get("/vehiculos_eliminar", tags=["Vehículos"])
async def vehiculos_eliminar_exitosa(request: Request):
    return templades.TemplateResponse("vehiculo_delete_success.html", {"request": request, "title": "Registro Exitoso"})

@router.post("/vehiculos/eliminar/{vehiculo_id}", tags=["Vehículos"])
async def eliminar_vehiculo(
    vehiculo_id : int,
    session : AsyncSession = Depends(get_session)
):
    try:
        await eliminar_vehiculo_db(vehiculo_id, session)
        return RedirectResponse(url="/vehiculos_eliminar", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        print(f"Error al eliminar vehículo: {e.detail}")
        return RedirectResponse(
            url="/vehiculos",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
@router.get("/vehiculos/edit/{vehiculo_id}", tags=["Vehículos"])
async def editar_vehiculo_html(
    request : Request,
    vehiculo_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Vehiculo).where(Vehiculo.id == vehiculo_id)
        )
    vehiculo = result.scalar_one_or_none()
    if vehiculo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado"
        )
    return templades.TemplateResponse(
        "vehiculo_edit.html", {
            "request":request,
            "title": "Editar Vehículo:{vehiculo.marca} {vehiculo.modelo}",
            "vehiculo": vehiculo,
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "imagen_url": vehiculo.imagen_url
            
        }
        )

@router.post("/vehiculos/edit/{vehiculo_id}", tags=["Vehículos"])
async def actualizar_vehiculo(
    vehiculo_id: int,
    vehiculo_update: VehiculoCreateForm = Depends(),  
    session: AsyncSession = Depends(get_session)
):
    vehiculo = await actualizar_vehiculo_db(vehiculo_id, vehiculo_update, session)
    return RedirectResponse(url="/vehiculos_edit", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/vehiculos/historial_eliminados", tags=["Vehiculos historial"])
async def vehiculos_historial_html(
    request:Request,
    session:AsyncSession= Depends(get_session),
    marca: Optional[str] = Query(None, description="Filtrar por marca del vehículo eliminado"),
    modelo: Optional[str] = Query(None, description="Filtrar por modelo del vehículo eliminado"),
    historico_id: Optional[str] = Query(None, description="Filtrar por ID del registro histórico (opcional)")
      ):
    current_marca = marca if marca else None
    current_modelo = modelo if modelo else None
    current_historico_id = int(historico_id) if historico_id and historico_id.isdigit() else None

    error_message = None

    try:
        vehiculo_historico = await obtener_vehiculo_historico_db(
            session=session,
            marca=current_marca,
            modelo=current_modelo,
            historico_id=current_historico_id 
        )

        if not vehiculo_historico:
            if current_marca or current_modelo or current_historico_id:
                error_message = "No se encontraron vehículos con los criterios de búsqueda."
            else:
                error_message = "No hay vehículos registrados en el sistema."

        return templades.TemplateResponse(
            "vehiculos_historial.html",
            {
                "request" : request,
                "vehiculo_historico" : vehiculo_historico,
                "title" : "Historial de Vehículos Eliminados",
                "Tipo_combustibleEnum" : Tipo_combustibleEnum,
                "current_marca" : current_marca,
                "current_modelo" : current_modelo,
                "current_historico_id": current_historico_id, 
                "error_message": error_message
            }
        )
    except HTTPException as e:
         return templades.TemplateResponse(
            "vehiculos_historial.html",
            {
                "request": request,
                "vehiculos_historico": [],
                "title": "Historial de Combustibles Eliminados",
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_marca": current_marca,
                "current_modelo": current_modelo,
                "current_historico_id": current_historico_id,
                "error_message": e.detail
            },
            status_code=e.status_code
        )
    except Exception as e:
        return templades.TemplateResponse(
            "vehiculos_historial.html",
            {
                "request": request,
                "vehiculo_historico": [],
                "title": "Historial de Vehiculos Eliminados",
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_marca": current_marca,
                "current_modelo": current_modelo,
                "current_historico_id": current_historico_id, 
                "error_message": f"Error inesperado: {e}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/vehiculos/restaurar/{historico_id}", tags=["Vehiculos historial"])
async def restaurar_vehiculo(
    historico_id:int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await retaurar_vehiculo_db(historico_id, session)
        return RedirectResponse(url="/vehiculos_restar",status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        print(f"Error al restaurar vehiculo:{e.detail}")
        return RedirectResponse(url=f"/vehiculos/historial?error_message:{e.detail}")
    except Exception as e:
        print(f"Error inesperado al restaurar vehiculo")
        return RedirectResponse(
            url=f"/vehiculos/historial?error_message=Ocurrió un error inesperado al restaurar el vehículo.",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/buscar_costo_tanqueo", response_class=HTMLResponse, tags=["Búsqueda"])
async def buscar_costo_tanqueo_html(
    request: Request,
    marca: Optional[str] = Query(None, description="Marca del vehículo"),
    modelo: Optional[str] = Query(None, description="Modelo del vehículo"),
    ciudad: Optional[str] = Query(None, description="Ciudad del combustible"),
    localidad: Optional[str] = Query(None, description="Localidad del combustible"),
    tipo_combustible: Optional[Tipo_combustibleEnum] = Query(None, description="Tipo de combustible"),
    session: AsyncSession = Depends(get_session)
):
    resultados_busqueda = []
    error_message = None 
    
    vehiculos_disponibles = await obtener_todos_vehiculos_simples(session)
    
    combustibles_disponibles = await obtener_todos_combustibles_simples(session)

    if marca or modelo or ciudad or localidad or tipo_combustible:
        try:
            resultados_busqueda = await obtener_vehiculos_con_costo_combustible_db(
                session=session,
                marca=marca,
                modelo=modelo,
                ciudad=ciudad,
                localidad=localidad,
                tipo_combustible=tipo_combustible
            )
            if not resultados_busqueda:
                error_message = "No se encontraron vehículos o precios de combustible que coincidan con los criterios de búsqueda."
        except HTTPException as e:
            error_message = e.detail
            resultados_busqueda = [] 
        except Exception as e:
            error_message = f"Ocurrió un error inesperado durante la búsqueda: {e}"
            resultados_busqueda = []
    else:
        error_message = None 

    return templades.TemplateResponse(
        "buscar_resutados.html", 
        {
            "request": request,
            "title": "Búsqueda de Costo de Tanqueo",
            "resultados": resultados_busqueda,
            "error_message": error_message,
            "marca_buscada": marca, 
            "modelo_buscado": modelo,
            "ciudad_buscada": ciudad,
            "localidad_buscada": localidad,
            "tipo_combustible_buscado": tipo_combustible,
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "vehiculos_disponibles": vehiculos_disponibles, 
            "combustibles_disponibles": combustibles_disponibles,
        }
    )


@router.get("/combustibles", tags=["Combustibles"])
async def combustible_list_html(
        request: Request,
    session: AsyncSession = Depends(get_session),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad (opcional)"),
    localidad: Optional[str] = Query(None, description="Filtrar por localidad (opcional)"),
    combustible_id: Optional[str] = Query(None, description="Filtrar por ID (opcional)")
):
    current_ciudad = ciudad if ciudad else None
    current_localidad = localidad if localidad else None
    current_combustible_id = int(combustible_id) if combustible_id and combustible_id.isdigit() else None

    error_message = None

    try:
        combustibles = await obtener_precio_combustible_db(
            session=session,
            ciudad=current_ciudad,
            localidad=current_localidad,
            combustible_id=current_combustible_id 
        )

        if not combustibles:
            if current_ciudad or current_localidad or current_combustible_id:
                error_message = "No se encontraron combustibles con los criterios de búsqueda."
            else:
                error_message = "No hay combustibles registrados en el sistema."

        return templades.TemplateResponse(
            "combustibles.html",
            {
                "request": request,
                "combustibles": combustibles,
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_ciudad": current_ciudad, 
                "current_localidad": current_localidad,
                "current_combustible_id": current_combustible_id, 
                "error_message": error_message
            }
        )
    except HTTPException as e:
        return templades.TemplateResponse(
            "combustibles.html",
            {
                "request": request,
                "combustibles": [],
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_ciudad": current_ciudad,
                "current_localidad": current_localidad,
                "current_combustible_id": current_combustible_id,
                "error_message": e.detail
            },
            status_code=e.status_code
        )
    except Exception as e:
        return templades.TemplateResponse(
            "combustibles.html",
            {
                "request": request,
                "combustibles": [],
                "Tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_ciudad": current_ciudad,
                "current_localidad": current_localidad,
                "current_combustible_id": current_combustible_id,
                "error_message": f"Error inesperado: {e}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.get("/combustibles_registro", tags=["Combustibles"])
async def combustibles_registro_exitosa(request: Request):
    return templades.TemplateResponse("combustible_registration_success.html", {"request": request, "title": "Registro Exitoso"})

@router.get("/combustibles_edit", tags=["Combustibles"])
async def combustibles_edit_exitosa(request: Request):
    return templades.TemplateResponse("combustible_edit_success.html", {"request": request, "title": "Registro Exitoso"})

@router.get("/combustibles_restar", tags=["Combustibles"])
async def combustibles_restar_exitosa(request: Request):
    return templades.TemplateResponse("combustible_restaurar_success.html", {"request": request, "title": "Registro Exitoso"})

@router.get("/combustibles_eliminar", tags=["Combustibles"])
async def combustibles_eliminar_exitosa(request: Request):
    return templades.TemplateResponse("combustible_delete_success.html", {"request": request, "title": "Registro Exitoso"})


@router.get("/combustible/crear", tags=["Combustibles"])
async def combustible_create_html(request:Request, session:AsyncSession = Depends(get_session)):
    return templades.TemplateResponse("combustible_create.html", {
        "request": request,
        "title": "Crear Combustible",
        "tipo_combustibleEnum":Tipo_combustibleEnum
    })

@router.post("/combustible/crear", tags=["Combustibles"]) 
async def create_combustible(
    combustible_data: CombustibleCreate = Depends(combustible_create_form), 
    session: AsyncSession = Depends(get_session)
):
    try:
        nuevo_combustible = await crear_combustible_precio_db(combustible_data,session)
        return RedirectResponse(url="/combustibles_registro", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
         return templades.TemplateResponse(
            "combustible_create.html", 
            {
                "request": Request(scope={"type": "http"}), 
                "title": "Crear Combustible",
                "tipo_combustibleEnum": Tipo_combustibleEnum,
                "error_message": e.detail, 
            },
            status_code=e.status_code 
        )
    except Exception as e:
        print(f"Error inesperado al crear combustible: {e}") 
        return templades.TemplateResponse(
            "combustible_create.html",
            {
                "request": Request(scope={"type": "http"}), 
                "title": "Crear combustible",
                "tipo_combustibleEnum": Tipo_combustibleEnum,
                "error_message": f"Ocurrió un error inesperado al registrar el vehículo."
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/combustible/eliminar/{combustible_id}", tags=["Combustibles"])
async def eliminar_combustible(
    combustible_id : int,
    session : AsyncSession = Depends(get_session)
):
    try:
        await eliminar_combustible_db(combustible_id, session)
        return RedirectResponse(url="/combustibles_eliminar", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        print(f"Error al eliminar combustible: {e.detail}")
        return RedirectResponse(
            url="/combustibles",
            status_code=status.HTTP_303_SEE_OTHER
        )
    
@router.get("/combustibles/edit/{combustible_id}", tags=["Combustibles"])
async def editar_combustible_html(
    request : Request,
    combustible_id: int,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Combustible).where(Combustible.id == combustible_id),
    )
        
    combustible = result.scalar_one_or_none()
    if combustible is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Combustible no encontrado"
        )
    return templades.TemplateResponse(
        "combustible_edit.html", {
            "request":request,
            "title": "Editar Combustible:{combustible.ciudad} {combustible.localidad}",
            "combustible": combustible,
            "tipo_combustibleEnum": Tipo_combustibleEnum
            
        }
        )

@router.post("/combustibles/edit/{combustible_id}", tags=["Combustibles"])
async def actualizar_combustible(
    combustible_id : int,
    combustible_data: CombustibleCreate = Depends(combustible_create_form),
    session: AsyncSession = Depends(get_session)
):
    combustible = await actualizar_precio_combustible_db(combustible_id, combustible_data, session)
    return RedirectResponse(
        url="/combustibles_edit",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/combustible/historial_eliminados", tags=["Combustibles historial"])
async def combustibles_historial_html(
    request:Request,
    session:AsyncSession= Depends(get_session),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad del combustible eliminado"),
    localidad: Optional[str] = Query(None, description="Filtrar por localidad del combustible eliminado"),
    historico_id: Optional[str] = Query(None, description="Filtrar por ID del registro histórico (opcional)") 
      ):
    current_ciudad = ciudad if ciudad else None
    current_localidad = localidad if localidad else None
    current_historico_id = int(historico_id) if historico_id and historico_id.isdigit() else None 

    error_message = None

    try:
        combustible_historico = await obtener_combustible_historico_db(
            session=session,
            ciudad=current_ciudad,
            localidad=current_localidad,
            historico_id=current_historico_id 
        )

        if not combustible_historico:
            if current_ciudad or current_localidad or current_historico_id:
                error_message = "No se encontraron combustibles con los criterios de búsqueda."
            else:
                error_message = "No hay combustibles registrados en el sistema."

        return templades.TemplateResponse(
            "combustible_historial.html",
            {
                "request" : request,
                "combustible_historico" : combustible_historico,
                "title" : "Historial de Combustibles Eliminados",
                "tipo_combustibleEnum" : Tipo_combustibleEnum,
                "current_ciudad" : current_ciudad,
                "current_localidad" : current_localidad,
                "current_historico_id": current_historico_id, 
                "error_message": error_message
            }
        )
    except HTTPException as e:
        return templades.TemplateResponse(
            "combustible_historial.html",
            {
                "request": request,
                "combustible_historico": [],
                "title": "Historial de Combustibles Eliminados",
                "tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_ciudad": current_ciudad,
                "current_localidad": current_localidad,
                "current_historico_id": current_historico_id, 
                "error_message": e.detail
            },
            status_code=e.status_code
        )
    except Exception as e:
        return templades.TemplateResponse(
            "combustible_historial.html",
            {
                "request": request,
                "combustible_historico": [],
                "title": "Historial de Combustibles Eliminados",
                "tipo_combustibleEnum": Tipo_combustibleEnum,
                "current_ciudad": current_ciudad,
                "current_localidad": current_localidad,
                "current_historico_id": current_historico_id, 
                "error_message": f"Error inesperado: {e}"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@router.post("/combustible/restaurar/{historico_id}", tags=["Combustibles historial"])
async def restaurar_combustible(
    historico_id:int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await restaurar_combustible_db(historico_id, session)
        return RedirectResponse(url="/combustibles_restar",status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        print(f"Error al restaurar combustible:{e.detail}")
        return RedirectResponse(url=f"/combustible/historial_eliminados?error_message={e.detail}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        print(f"Error inesperado al restaurar combustible: {e}")
        return RedirectResponse(
            url=f"/combustible/historial_eliminados?error_message=Ocurrió un error inesperado al restaurar el combustible. ({e})",
            status_code=status.HTTP_303_SEE_OTHER
        )



@router.get("/buscar_costo_tanqueo", tags=["Búsqueda"])
async def buscar_costo_tanqueo_html(
    request: Request,
  
    marca: Optional[str] = Query(None, description="Marca del vehículo"),
    modelo: Optional[str] = Query(None, description="Modelo del vehículo"),
    ciudad: Optional[str] = Query(None, description="Ciudad del combustible"),
    localidad: Optional[str] = Query(None, description="Localidad del combustible"),
    tipo_combustible: Optional[Tipo_combustibleEnum] = Query(None, description="Tipo de combustible")
    ,session: AsyncSession = Depends(get_session)
):
    resultados_busqueda = []
   
    if marca or modelo or ciudad or localidad or tipo_combustible:
        try:
            resultados_busqueda = await obtener_vehiculos_con_costo_combustible_db(
                session=session,
                marca=marca,
                modelo=modelo,
                ciudad=ciudad,
                localidad=localidad,
                tipo_combustible=tipo_combustible
            )
            if not resultados_busqueda:

                error_message = "No se encontraron vehículos o precios de combustible que coincidan con los criterios de búsqueda."
            else:
                error_message = None
        except HTTPException as e:
            error_message = e.detail
            resultados_busqueda = [] 
        except Exception as e:
            error_message = f"Ocurrió un error inesperado durante la búsqueda: {e}"
            resultados_busqueda = []
    else:
        error_message = None 

    return templades.TemplateResponse(
        "buscar_resutados.html", 
        {
            "request": request,
            "title": "Resultados de Búsqueda de Costo de Tanqueo",
            "resultados": resultados_busqueda,
            "error_message": error_message,
            "marca_buscada": marca, 
            "modelo_buscado": modelo,
            "ciudad_buscada": ciudad,
            "localidad_buscada": localidad,
            "tipo_combustible_buscado": tipo_combustible,
            "Tipo_combustibleEnum": Tipo_combustibleEnum 
        }
    )

@router.get("/informacion", tags=["Informacion"])
async def leer_info(request: Request):
    return templades.TemplateResponse("informacion.html", {"request": request})

@router.get("/informacion/planeacion", tags=["Informacion"])
async def leer_info(request: Request):
    return templades.TemplateResponse("informacion_planeacion.html", {"request": request})

@router.get("/informacion/diseno", tags=["Informacion"])
async def leer_info(request: Request):
    return templades.TemplateResponse("informacion_diseno.html", {"request": request})

@router.get("/informacion/desarrollador",tags=["informacion"])
async def leer_info_desa(request : Request):
    return templades.TemplateResponse("/informacion_desarrollador.html",{"request" : request})