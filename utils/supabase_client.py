import os
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi import UploadFile
from urllib.parse import urlparse
import uuid
import aiofiles
import asyncio

from fastapi.concurrency import run_in_threadpool

load_dotenv()

supabase_url: str = os.getenv("SUPABASE_URL")
supabase_key: str = os.getenv("SUPABASE_KEY")
supabase_bucket_name: str = os.getenv("SUPABASE_BUCKET_NAME")



if not supabase_url or not supabase_key:
    raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY no están configuradas.")

supabase=create_client(supabase_url, supabase_key)

async def upload_file(file: UploadFile, filename: str):
    content = await file.read()
    filepath = f"image/{filename}" # Aquí se define 'filepath'

    try:
        res = supabase.storage.from_(supabase_bucket_name).upload(
            filepath, # Se usa 'filepath' para la subida
            content,
            {"content-type": file.content_type}
        )

        print("Respuesta upload:", res)

        # ¡Corrección aquí! Usar 'filepath' (con 'p' mayúscula)
        public_url_response = supabase.storage.from_(supabase_bucket_name).get_public_url(filepath)
        print("Respuesta get_public_url:", public_url_response)

        return {"url": public_url_response}

    except Exception as e:
        print("Primer intento falló:", e)
        await asyncio.sleep(1)
        try:
            # segundo intento
            res = supabase.storage.from_(supabase_bucket_name).upload(
                filepath,
                content,
                {"content-type": file.content_type}
            )
            public_url_response = supabase.storage.from_(supabase_bucket_name).get_public_url(filepath)
            return {"url": public_url_response}
        except Exception as e:
            print("Segundo intento también falló:", e)
            return {"error": str(e)}

async def save_file(file: UploadFile, to_supabase: bool):
    if not file.content_type.startswith("image/"):
        return {"error": "Solo se permiten imágenes"}

    new_filename = f"{uuid.uuid4().hex}{file.filename}"

    if to_supabase:
        return await upload_file(file, new_filename)
    else:
        return await save_to_local(file, new_filename)


async def save_to_local(file: UploadFile, filename: str):

    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return {"filename": filename, "local_path": file_path}

def get_supabase_path_from_url(url: str, bucket_name: str) -> str:
    parsed = urlparse(url)
    return parsed.path.replace(f"/storage/v1/object/public/{bucket_name}/", "")