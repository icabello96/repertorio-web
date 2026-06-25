from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import tempfile
import requests
import os
import subprocess

app = FastAPI()
templates = Jinja2Templates(directory="templates")

PDF_URL = "https://rebrand.ly/entero"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/procesar/")
async def procesar(
    lista: UploadFile = File(...),
    nombre_salida: str = Form(...)
):
    # ---------- 1. Descargar el PDF ENTEROOOO ----------
    pdf_response = requests.get(PDF_URL)
    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_temp.write(pdf_response.content)
    pdf_temp.close()

    # ---------- 2. Guardar repertorio.txt ----------
    lista_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    lista_temp.write(await lista.read())
    lista_temp.close()

    # ---------- 3. Nombre de salida ----------
    if not nombre_salida.endswith(".pdf"):
        nombre_salida += ".pdf"

    salida_path = os.path.join(tempfile.gettempdir(), nombre_salida)

    # ---------- 4. Ejecutar tu script ----------
    subprocess.run([
        "python3",
        "extraer_repertorio.py",
        pdf_temp.name,
        lista_temp.name,
        salida_path
    ])

    # ---------- 5. Devolver PDF ----------
    return FileResponse(
        salida_path,
        media_type="application/pdf",
        filename=nombre_salida
    )