<h1 align="center">🚗 Gestión de Vehículos y Combustibles ⛽️</h1>
<h3 align="center">Un proyecto web moderno con FastAPI, SQLAlchemy, Supabase y PostgreSQL</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&style=flat" alt="Versión de Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110.0-teal?logo=fastapi" alt="Versión de FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql" alt="Versión de PostgreSQL"/>
  <img src="https://img.shields.io/badge/Supabase-Storage-green?logo=supabase" alt="Almacenamiento Supabase"/>
  <img src="https://img.shields.io/badge/Licencia-MIT-green" alt="Licencia MIT"/>
</p>

---

## 📌 Descripción

Este sistema permite una gestión integral de vehículos y los costos asociados a sus combustibles. La aplicación facilita el registro detallado de vehículos, la administración de precios de combustible por localidad y el cálculo automático del costo de tanqueo, todo respaldado por almacenamiento de imágenes en la nube.

## 🧑‍💻 Tecnologías utilizadas

- ⚡️ **FastAPI** para la API backend robusta y asíncrona.
- 🐘 **PostgreSQL** como base de datos relacional para la persistencia de datos.
- 🧠 **SQLAlchemy** como ORM (Object Relational Mapper) para la interacción con la base de datos.
- 🖼️ **Supabase Storage** para el almacenamiento eficiente de imágenes de vehículos.
- 🌐 **Jinja2 + Bootstrap** para la construcción de una interfaz de usuario web dinámica y responsiva.

---

## 📂 Características principales

- **CRUD completo** para la gestión de **Vehículos** y **Precios de Combustibles**.
- **Cálculo de Costo de Tanqueo:** Calcula automáticamente el costo total para llenar el tanque de un vehículo basándose en su tamaño y el precio del combustible en una ubicación específica.
- **Subida y gestión de imágenes** de vehículos, sincronizadas con Supabase.
- **Filtrado avanzado:** Permite buscar vehículos y resultados de costo de tanqueo por marca, modelo, ciudad, localidad y tipo de combustible.
- **Protección contra envíos múltiples:** Implementación de JavaScript para deshabilitar botones de envío durante la carga, previniendo creaciones y actualizaciones duplicadas.
- **Vistas web intuitivas** desarrolladas con Jinja2 y Bootstrap.

---

## 🛠️ Instalación y Configuración

Sigue estos pasos para poner en marcha el proyecto en tu entorno local:

### 1. Clona el Repositorio

```bash
git clone [https://github.com/Sebas59/Proyecto_inte.git](https://github.com/Sebas59/Proyecto_inte.git)
cd Proyecto_inte
