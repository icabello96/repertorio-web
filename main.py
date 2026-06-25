from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import requests
import os
import subprocess

app = FastAPI()

PDF_URL = "https://rebrand.ly/entero"


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <body>
        <h1>🎵 Generador de repertorio</h1>

        <form action="/procesar/" method="post" enctype="multipart/form-data">
            <label>Subir repertorio.txt</label><br>
            <input type="file" name="lista" required><br><br>

            <label>Nombre del PDF de salida</label><br>
            <input type="text" name="nombre_salida" required><br><br>

            <button type="submit">Generar PDF</button>
        </form>

    </body>
    </html>
    """


@app.post("/procesar/")
async def procesar(
    lista: UploadFile = File(...),
    nombre_salida: str = Form(...)
):
    # Descargar PDF base
