from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from typing import List, Optional,Dict
from data.models import *
from data.schemas import *
from fastapi import Form,File
from utils.supabase_client import *


async def crear_vehiculo_db(vehiculo_create, session:AsyncSession)->Vehiculo:
    nuevo_vehiculo = Vehiculo(**vehiculo_create.dict())
    session.add(nuevo_vehiculo)
    try:
        await session.commit()
        await session.refresh(nuevo_vehiculo)
        return nuevo_vehiculo
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al crear el vehiculo")
    
async def obtener_vehiculos_db(
        session:AsyncSession,
        marca : Optional[str] = None,
        modelo : Optional[str] = None,
        vehiculo_id: Optional[int] = None
        )->List[Vehiculo]:
    
    query = select(Vehiculo)
    condition = []
    if marca:
        condition.append(Vehiculo.marca.ilike(f"%{marca}"))
    if modelo:
        condition.append(Vehiculo.modelo.ilike(f"%{modelo}"))
    if vehiculo_id:
        condition.append(Vehiculo.id == vehiculo_id)

    if condition:
        query = query.where(and_(*condition))
    
    result = await session.execute(query)
    vehiculos = result.scalars().all()
    return vehiculos

async def actualizar_vehiculo_db(
        vehiculo_id: int, vehiculo_update:VehiculoUpdateForm, session:AsyncSession
        )->Vehiculo:
    result = await session.execute(select(Vehiculo).where(Vehiculo.id == vehiculo_id))
    vehiculo = result.scalar_one_or_none()
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    imagen_actual = vehiculo.imagen_url
    nueva_imagen_url: Optional[str] = None
    if vehiculo_update.imagen:
        resultado = await save_file(vehiculo_update.imagen, to_supabase=True)

        if "url" in resultado:
            nueva_imagen_url = resultado["url"]
            if imagen_actual:
                path_antiguo = get_supabase_path_from_url(imagen_actual, supabase_bucket_name)
                supabase.storage.from_(supabase_bucket_name).remove([path_antiguo])
        else:
            print("Error al subir nueva imagen:", resultado.get("error"))
    for campo in ["marca", "modelo", "year", "Tipo_combustible", "Tan_size"]:
        valor = getattr(vehiculo_update, campo)
        if valor is not None:
            setattr(vehiculo, campo, valor)
    if nueva_imagen_url:
        vehiculo.imagen_url = nueva_imagen_url

    session.add(vehiculo)
    await session.commit()
    await session.refresh(vehiculo)
    return vehiculo
    
    
async def eliminar_vehiculo_db(id:int, session:AsyncSession)->Vehiculo:
    vehiculo_a_eliminar = await session.get(Vehiculo, id)
    if not vehiculo_a_eliminar:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    historico = VehiculoHistorico(
        original_id=vehiculo_a_eliminar.id,
        marca=vehiculo_a_eliminar.marca,
        modelo=vehiculo_a_eliminar.modelo,
        year=vehiculo_a_eliminar.year,
        Tipo_combustible=vehiculo_a_eliminar.Tipo_combustible,
        Tan_size=vehiculo_a_eliminar.Tan_size,
        imagen_url=vehiculo_a_eliminar.imagen_url
    )
    session.add(historico)
    await session.delete(vehiculo_a_eliminar)
    try:
        await session.commit()
        return vehiculo_a_eliminar
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al eliminar el vehiculo")

async def retaurar_vehiculo_db(historico_id:int, session:AsyncSession):
    vehiculo_hist= await session.get(VehiculoHistorico, historico_id)
    if not vehiculo_hist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro historico de vehiculo no encontrado")
    vehiculo_data={
        "marca" : vehiculo_hist.marca,
        "modelo" : vehiculo_hist.modelo,
        "year" : vehiculo_hist.year,
        "Tipo_combustible" : vehiculo_hist.Tipo_combustible,
        "Tan_size" : vehiculo_hist.Tan_size,
        "imagen_url" : vehiculo_hist.imagen_url
    }
    nuevo_vehiculo = Vehiculo(**vehiculo_data)
    session.add(nuevo_vehiculo)
    await session.delete(vehiculo_hist)
    try:
        await session.commit()
        await session.refresh(nuevo_vehiculo)
        return nuevo_vehiculo
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al restaurar vehiculo")
    
async def obtener_vehiculo_historico_db(
        session:AsyncSession,
        marca : Optional[str] = None,
        modelo : Optional[str] = None
        ):
    query = select(VehiculoHistorico)
    conditions = []

    if marca:
        conditions.append(VehiculoHistorico.marca.ilike(f"%{marca}%"))
    if modelo:
        conditions.append(VehiculoHistorico.modelo.ilike(f"%{modelo}%"))

    if conditions:
        query = query.where(and_(*conditions))

    result = await session.execute(query)
    vehiculos_historico = result.scalars().all()
    return vehiculos_historico
   

async def obtener_vehiculo_por_marca_modelo_db(marca:str,modelo:str, session:AsyncSession)->List[Vehiculo]:
    result = await session.execute(
        select(Vehiculo).where(
            and_(Vehiculo.marca.ilike(f"%{marca}%"), Vehiculo.modelo.ilike(f"%{modelo}%"))
        )
    )
    vehiculos = result.scalars().all()
    if not vehiculos:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    return vehiculos

def combustible_create_form(
    ciudad: str = Form(...),
    localidad:str= Form(...),
    tipo_combustible: Tipo_combustibleEnum = Form(...),
    precio_por_galon: float = Form(...)
    
) -> CombustibleCreate:
    return CombustibleCreate(
        ciudad=ciudad,
        localidad=localidad,
        tipo_combustible=tipo_combustible,
        precio_por_galon=precio_por_galon
    )

async def obtener_todos_vehiculos_simples(session: AsyncSession) -> List[Dict]:
    """
    Obtiene una lista de todos los vehículos (ID, marca, modelo, tipo_combustible) 
    para poblar un desplegable.
    """
    try:
        result = await session.execute(
            select(Vehiculo.id, Vehiculo.marca, Vehiculo.modelo, Vehiculo.Tipo_combustible) 
            .order_by(Vehiculo.marca, Vehiculo.modelo) 
        )
        vehiculos_data = [
            {
                "id": v.id, 
                "marca": v.marca, 
                "modelo": v.modelo,
                "tipo_combustible": v.Tipo_combustible.value 
            }
            for v in result.all()
        ]
        return vehiculos_data
    except Exception as e:
        print(f"Error al obtener vehículos simples: {e}") 
        return []

async def obtener_todos_combustibles_simples(session: AsyncSession) -> List[Dict]:
    try:
        result = await session.execute(
            select(Combustible.id, Combustible.tipo_combustible, Combustible.ciudad, Combustible.localidad, Combustible.precio_por_galon)
            .order_by(Combustible.tipo_combustible, Combustible.ciudad, Combustible.localidad) 
        )
        combustibles_data = []
        for c in result.all():
            tipo_combustible_value = None
            if c.tipo_combustible:
                tipo_combustible_value = c.tipo_combustible.value 
            
            combustibles_data.append({
                "id": c.id,
                "tipo_combustible": tipo_combustible_value,
                "ciudad": c.ciudad,
                "localidad": c.localidad,
                "precio": c.precio_por_galon
            })
        return combustibles_data
    except Exception as e:
        print(f"Error al obtener combustibles simples: {e}")
        return []
        
async def crear_combustible_precio_db(combustible:CombustibleCreate, session:AsyncSession)->Combustible:
    nuevo_precio = Combustible(ciudad=combustible.ciudad, localidad=combustible.localidad ,tipo_combustible=combustible.tipo_combustible, precio_por_galon=combustible.precio_por_galon)
    session.add(nuevo_precio)
    try:
        await session.commit()
        await session.refresh(nuevo_precio)
        return nuevo_precio
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al crear el precio del combustible") 
    
async def obtener_precio_combustible_db(
    session: AsyncSession,
    ciudad: Optional[str] = None, 
    localidad: Optional[str] = None 
) -> List[CombustibleRead]: 
    query = select(Combustible)
    conditions = []

    if ciudad:
        conditions.append(Combustible.ciudad.ilike(f"%{ciudad}%"))
    if localidad:
        conditions.append(Combustible.localidad.ilike(f"%{localidad}%"))

    if conditions:
        query = query.where(and_(*conditions))

    result = await session.execute(query)
    precios_combustible = result.scalars().all()
    return precios_combustible

async def actualizar_precio_combustible_db(id:int, combustible:CombustibleCreate, session:AsyncSession)->Combustible:
    nuevo_precio = await session.get(Combustible, id)
    if not nuevo_precio:
        raise HTTPException(status_code=404, detail="Precio de combustible no encontrado")
    for key, value in combustible.dict(exclude_unset=True).items():
        setattr(nuevo_precio, key, value)
    session.add(nuevo_precio)
    try:
        await session.commit()
        await session.refresh(nuevo_precio)
        return nuevo_precio
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al actualizar el precio del combustible")
    
async def eliminar_combustible_db(id:int, session:AsyncSession)->Combustible:
    combustible_a_eliminar = await session.get(Combustible, id)
    if not combustible_a_eliminar:
        raise HTTPException(status_code=404, detail="Combustible no encontrado")
    historico = CombustibleHistorico(
        original_id=combustible_a_eliminar.id,
        ciudad=combustible_a_eliminar.ciudad,
        localidad=combustible_a_eliminar.localidad,
        tipo_combustible=combustible_a_eliminar.tipo_combustible,
        precio_por_galon=combustible_a_eliminar.precio_por_galon
    )
    session.add(historico)
    await session.delete(combustible_a_eliminar)
    try:
        await session.commit()
        return combustible_a_eliminar
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=404, detail="Error al eliminar el combustible")

async def restaurar_combustible_db(historico_id: int, session: AsyncSession) -> Combustible: 
    combustible_hist = await session.get(CombustibleHistorico, historico_id) 
    if not combustible_hist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro histórico de combustible no encontrado")
    
    combustible_data = {
        "ciudad": combustible_hist.ciudad,
        "localidad": combustible_hist.localidad,
        "tipo_combustible": combustible_hist.tipo_combustible,
        "precio_por_galon": combustible_hist.precio_por_galon,
    }
    
    nuevo_combustible = Combustible(**combustible_data) 
    session.add(nuevo_combustible)
    
    await session.delete(combustible_hist) 
    
    try:
        await session.commit()
        await session.refresh(nuevo_combustible) 
        return nuevo_combustible
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Error de integridad al restaurar combustible: {e}")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado al restaurar combustible: {e}")

async def obtener_combustible_historico_db(
    session: AsyncSession,
    ciudad: Optional[str] = None,
    localidad: Optional[str] = None
) -> List[CombustibleHistorico]:
   
    query = select(CombustibleHistorico)
    conditions = []

    if ciudad:
        conditions.append(CombustibleHistorico.ciudad.ilike(f"%{ciudad}%"))
    if localidad:
        conditions.append(CombustibleHistorico.localidad.ilike(f"%{localidad}%"))

    if conditions:
        query = query.where(and_(*conditions))

    result = await session.execute(query)
    combustibles_historico = result.scalars().all()
    return combustibles_historico

async def obtener_vehiculos_con_costo_combustible_db(
    session: AsyncSession,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    ciudad: Optional[str] = None,
    localidad: Optional[str] = None,
    tipo_combustible: Optional[Tipo_combustibleEnum] = None 
) -> List[CostoTanqueo]:
    
   
    query_vehiculos = select(Vehiculo)
    conditions_vehiculos = []
    if marca:
        conditions_vehiculos.append(Vehiculo.marca.ilike(f"%{marca}%"))
    if modelo:
        conditions_vehiculos.append(Vehiculo.modelo.ilike(f"%{modelo}%"))
    if conditions_vehiculos:
        query_vehiculos = query_vehiculos.where(and_(*conditions_vehiculos))

    result_vehiculos = await session.execute(query_vehiculos)
    vehiculos = result_vehiculos.scalars().all()

    if not vehiculos:
        return [] 

    resultado: List[CostoTanqueo] = []
    for vehiculo in vehiculos:
        query_combustible = select(Combustible)
        conditions_combustible = []
        if ciudad:
            conditions_combustible.append(Combustible.ciudad.ilike(f"%{ciudad}%"))
        if localidad:
            conditions_combustible.append(Combustible.localidad.ilike(f"%{localidad}%"))
 
        conditions_combustible.append(Combustible.tipo_combustible == vehiculo.Tipo_combustible)
        

        if tipo_combustible:
            conditions_combustible.append(Combustible.tipo_combustible == tipo_combustible)

        if conditions_combustible:
            query_combustible = query_combustible.where(and_(*conditions_combustible))

        result_combustible = await session.execute(query_combustible)
        combustible = result_combustible.scalars().one_or_none() 

        if combustible:

            if vehiculo.Tan_size is not None and combustible.precio_por_galon is not None:
                costo_total = round(vehiculo.Tan_size * combustible.precio_por_galon, 3)
            else:
                costo_total = None 
            
            resultado.append(
                CostoTanqueo(
                    marca=vehiculo.marca,
                    modelo=vehiculo.modelo,
                    year=vehiculo.year,
                    Tipo_combustible=vehiculo.Tipo_combustible,
                    Tan_size=vehiculo.Tan_size,
                    precio_por_galon=combustible.precio_por_galon,
                    ciudad=combustible.ciudad,
                    localidad=combustible.localidad,
                    costo_total=costo_total
                )
            )
    
  
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron vehículos o precios de combustible que coincidan con los criterios proporcionados."
        )
        pass 
    
    return resultado