from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
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
from utils.supabase_db import *


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
    marca : Optional[str] = Query(None, description="Filtrar por marca del vehiculo"),
    modelo : Optional[str] = Query(None, description="Filtrar por modelo del vehiculo")
    ):
    vehiculos = await obtener_vehiculos_db(
        session=session,
        marca=marca,
        modelo=modelo,
        )
    return templades.TemplateResponse(
        "vehiculos.html", 
        {
        "request": request,
        "vehiculos": vehiculos, 
        "Tipo_combustible": Tipo_combustibleEnum,
        "Current_marca" : marca,
        "current_modelo" : modelo,
        }
        )

@router.get("/vehiculos/crear", tags=["Vistas HTML - Vehículos"], response_class=HTMLResponse)
async def vehiculo_create_html(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Renderiza el formulario HTML para crear un nuevo vehículo.
    """
    return templades.TemplateResponse("vehiculo_create.html", {
        "request": request,
        "title": "Crear Vehículo",
        "Tipo_combustibleEnum": Tipo_combustibleEnum, # Pasa el Enum al template para el dropdown
        "vehiculo_data": {} # Diccionario vacío para precargar el formulario si no hay datos previos
    })

@router.post("/vehiculos/crear", tags=["Vehículos"]) 
async def post_create_vehiculo_html(
    request: Request,
    form_data: dict = Depends(vehiculo_create_form_dependency), # Usa la dependencia que parsea el formulario
    session: AsyncSession = Depends(get_session)
):
    """
    Procesa el envío del formulario HTML para crear un vehículo.
    Sube la imagen a Supabase Storage y guarda la URL en la base de datos.
    Maneja errores y redirige o vuelve a mostrar el formulario con feedback.
    """
    imagen_url: Optional[str] = None
    error_message: Optional[str] = None

    # 1. Procesar la imagen (si se envió)
    if form_data.get("imagen") and form_data["imagen"].filename: # Asegúrate de que un archivo fue realmente seleccionado
        try:
            # Llama a tu función save_file para subir la imagen
            # 'to_supabase=True' para que use Supabase Storage
            upload_result = await save_file(form_data["imagen"], to_supabase=True)
            
            if "error" in upload_result:
                error_message = f"Error al subir la imagen: {upload_result['error']}"
            else:
                imagen_url = upload_result.get("url")
        except Exception as e:
            error_message = f"Error inesperado al procesar la imagen: {e}"
    
    # Si hubo un error relacionado con la carga de la imagen, renderiza el formulario de nuevo
    if error_message:
        return templades.TemplateResponse("vehiculo_create.html", {
            "request": request,
            "title": "Crear Vehículo",
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": error_message,
            "vehiculo_data": form_data # Para precargar los campos que el usuario ya rellenó
        })

    # 2. Crear una instancia de VehiculoCreate (el esquema Pydantic)
    # y mapear los campos del formulario a los campos del esquema de tu modelo Vehiculo
    try:
        vehiculo_create_schema = VehiculoCreate(
            marca=form_data["marca"],
            modelo=form_data["modelo"],
            year=form_data["año"], # <-- ¡IMPORTANTE!: Mapea 'año' del formulario a 'year' del modelo
            Tipo_combustible=form_data["Tipo_combustible"],
            Tan_size=form_data["Tan_size"],
            imagen_url=imagen_url # La URL de la imagen procesada
        )
    except Exception as e: # Esto captura errores de validación de Pydantic si los datos del formulario no coinciden con VehiculoCreate
        error_message = f"Datos del formulario inválidos. Por favor, revisa los campos. Detalles: {e}"
        return templades.TemplateResponse("vehiculo_create.html", {
            "request": request,
            "title": "Crear Vehículo",
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": error_message,
            "vehiculo_data": form_data # Para precargar campos en caso de error de validación
        })

    # 3. Llamar a tu función existente para guardar el vehículo en la base de datos
    try:
        await crear_vehiculo_db(vehiculo_create_schema, session)
        
        # Redirigir a una página de éxito (ej. la lista de vehículos)
        # HTTP_303_SEE_OTHER se recomienda para redirecciones después de un POST exitoso
        return RedirectResponse(url="/vehiculos/", status_code=status.HTTP_303_SEE_OTHER) 
    
    except HTTPException as e:
        # Captura excepciones lanzadas por crear_vehiculo_db (como IntegrityError o 500)
        error_message = e.detail
        return templades.TemplateResponse("vehiculo_create.html", {
            "request": request,
            "title": "Crear Vehículo",
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": error_message,
            "vehiculo_data": form_data # Para precargar campos en caso de error de DB
        })
    except Exception as e:
        # Captura cualquier otro error inesperado durante el proceso de guardado
        error_message = f"Ocurrió un error inesperado al guardar el vehículo: {e}"
        return templades.TemplateResponse("vehiculo_create.html", {
            "request": request,
            "title": "Crear Vehículo",
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": error_message,
            "vehiculo_data": form_data # Para precargar campos
        })

@router.get("/vehiculos_registro", tags=["Vehículos"])
async def vehiculos_registro_exitosa(request: Request):
    return templades.TemplateResponse("vehiculo_registration_success.html", {"request": request, "title": "Registro Exitoso"})

@router.post("/vehiculos/eliminar/{vehiculo_id}", tags=["Vehículos"])
async def eliminar_vehiculo(
    vehiculo_id : int,
    session : AsyncSession = Depends(get_session)
):
    try:
        await eliminar_vehiculo_db(vehiculo_id, session)
        return RedirectResponse(url="/vehiculos", status_code=status.HTTP_303_SEE_OTHER)
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
            "Tipo_combustibleEnum": Tipo_combustibleEnum
            
        }
        )

@router.get("/vehiculos/historial_eliminados", tags=["Vehiculos historial"])
async def vehiculos_historial_html(
    request:Request,
    session:AsyncSession= Depends(get_session),
    marca: Optional[str] = Query(None, description="Filtrar por marca del vehículo eliminado"),
    modelo: Optional[str] = Query(None, description="Filtrar por modelo del vehículo eliminado")
     ):
    vehiculo_historico = await obtener_vehiculo_historico_db(
        session=session,
        marca=marca,
        modelo=modelo
        )
    return templades.TemplateResponse( # Asegúrate que uses 'templates' y no 'templades'
        "vehiculos_historial.html", # Necesitarás crear este template
        {
            "request" : request,
            "vehiculos_historico" : vehiculo_historico,
            "title" : "Historial de Vehiculos Eliminados", # Corregido a "title"
            "Tipo_combustibleEnum" : Tipo_combustibleEnum, # Asegúrate de la consistencia del nombre
            "current_marca" : marca,
            "current_modelo" : modelo
        }
        )

@router.post("/vehiculos/edit/{vehiculo_id}", tags=["Vehículos"])
async def actualizar_vehiculo(
    request: Request, # Añadir request para renderizar el template en caso de error
    vehiculo_id : int,
    form_data: dict = Depends(vehiculo_update_form_dependency), # Usamos la dependencia de update
    session: AsyncSession = Depends(get_session)
):
    imagen_url: Optional[str] = None
    error_message: Optional[str] = None

    # Procesar nueva imagen si se envió
    if form_data.get("imagen") and form_data["imagen"].filename:
        try:
            upload_result = await save_file(form_data["imagen"], to_supabase=True)
            if "error" in upload_result:
                error_message = f"Error al subir nueva imagen: {upload_result['error']}"
            else:
                imagen_url = upload_result.get("url")
        except Exception as e:
            error_message = f"Error inesperado al procesar la nueva imagen: {e}"
    
    # Si hubo error en imagen, renderizar form con error
    if error_message:
        vehiculo_actual = await session.get(Vehiculo, vehiculo_id) # Recuperar para rellenar el formulario
        return templades.TemplateResponse("vehiculo_edit.html", {
            "request": request,
            "title": f"Editar Vehículo: {vehiculo_actual.marca} {vehiculo_actual.modelo}",
            "vehiculo": vehiculo_actual,
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": error_message,
            "vehiculo_data": form_data # Para precargar campos con los datos del form_data
        })

    # Preparar datos para actualizar, incluyendo la nueva imagen_url si existe
    update_data = {k: v for k, v in form_data.items() if k != "imagen" and v is not None} # Excluir 'imagen' y None
    if imagen_url:
        update_data["imagen_url"] = imagen_url
    
    try:
        # Pasa el diccionario a actualizar_vehiculo_db
        vehiculo_actualizado = await actualizar_vehiculo_db(vehiculo_id, update_data, session)
        return RedirectResponse(url="/vehiculos", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        vehiculo_actual = await session.get(Vehiculo, vehiculo_id)
        return templades.TemplateResponse("vehiculo_edit.html", {
            "request": request,
            "title": f"Editar Vehículo: {vehiculo_actual.marca} {vehiculo_actual.modelo}",
            "vehiculo": vehiculo_actual,
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": e.detail,
            "vehiculo_data": form_data
        })
    except Exception as e:
        vehiculo_actual = await session.get(Vehiculo, vehiculo_id)
        return templades.TemplateResponse("vehiculo_edit.html", {
            "request": request,
            "title": f"Editar Vehículo: {vehiculo_actual.marca} {vehiculo_actual.modelo}",
            "vehiculo": vehiculo_actual,
            "Tipo_combustibleEnum": Tipo_combustibleEnum,
            "error_message": f"Ocurrió un error inesperado al actualizar: {e}",
            "vehiculo_data": form_data
        })
    


@router.post("/vehiculos/restaurar/{historico_id}", tags=["Vehiculos historial"])
async def restaurar_vehiculo(
    historico_id:int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await retaurar_vehiculo_db(historico_id, session)
        return RedirectResponse(url="/vehiculos",status_code=status.HTTP_303_SEE_OTHER)
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
            "combustibles_disponibles": combustibles_disponibles 
        }
    )


@router.get("/combustibles", tags=["Combustibles"])
async def combustible_list_html(
    request: Request, 
    session: AsyncSession = Depends(get_session),
    ciudad : Optional[str] = Query(None, description="Filtrar por ciudad del combustible"),
    localidad: Optional[str] = Query(None, description="Filtrar por localidad del combustible")
    ):
    precios_combustible = await obtener_precio_combustible_db(
        session=session,
        ciudad=ciudad,
        localidad=localidad
        )
    return templades.TemplateResponse("combustibles.html",
     {
        "request": request,
        "precios_combustible": precios_combustible,
        "title": "Lista de Combustibles",
        "current_ciudad": ciudad,
        "current_localidad": localidad,
        "Tipo_combustibleEnum": Tipo_combustibleEnum
    })

@router.get("/combustible/crear", tags=["Combustibles"])
async def combustible_create_html(request:Request, session:AsyncSession = Depends(get_session)):
    return templades.TemplateResponse("combustible_create.html", {
        "request": request,
        "title": "Crear Combustible",
        "tipo_combustibleEnum":Tipo_combustibleEnum
    })

@router.post("/combustible/crear", tags=["Combustibles"]) 
async def create_vehiculo(
    combustible_data: CombustibleCreate = Depends(combustible_create_form), 
    session: AsyncSession = Depends(get_session)
):
    try:
        nuevo_combustible = await crear_combustible_precio_db(combustible_data,session)
        return RedirectResponse(url="/combustibles", status_code=status.HTTP_303_SEE_OTHER)
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
        return RedirectResponse(url="/combustibles", status_code=status.HTTP_303_SEE_OTHER)
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
        url="/combustibles",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/combustible/historial_eliminados", tags=["Combustibles historial"])
async def combustibles_historial_html(
    request:Request,
    session:AsyncSession= Depends(get_session),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad del combustible eliminado"),
    localidad: Optional[str] = Query(None, description="Filtrar por localidad del combustible eliminado")
      ):
    combustible_historico = await obtener_combustible_historico_db(
        session=session,
        ciudad=ciudad,
        localidad=localidad
        )
    return templades.TemplateResponse(
        "combustible_historial.html",
        {
            "request" : request,
            "combustible_historico" : combustible_historico,
            "title" : "Historial de Combustibles Eliminados",
            "tipo_combustibleEnum" : Tipo_combustibleEnum,
            "current_ciudad" : ciudad,
            "current_localidad" : localidad
        }
        )

@router.post("/combustible/restaurar/{historico_id}", tags=["Combustibles historial"])
async def restaurar_combustible(
    historico_id:int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await restaurar_combustible_db(historico_id, session)
        return RedirectResponse(url="/combustibles",status_code=status.HTTP_303_SEE_OTHER)
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

