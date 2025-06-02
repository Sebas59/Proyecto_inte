from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

import home

app = FastAPI(
    title="Gestion de Vehiculos a combustion y Combustibles",
    description="Aplicacion web para gestionar vehiculos a combustion, combustibles y costos de tanqueo"
)

app.mount("/statics", StaticFiles(directory="statics"), name="statics")

app.include_router(home.router)

templates = Jinja2Templates(directory="templates")