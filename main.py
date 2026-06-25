from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import requests
import os
import subprocess

app = FastAPI()

# ✅ URL directa (Google Drive en bruto puede fallar)
PDF_URL = "https://drive.google.com/uc?export=download&id=1GGv_629FDOYmcQ8sBJt5eOgu80Ow0xb1"


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <body>
        <h1>🎵 Generador de repertorio</h1>

        <form action="/procesar/" method="post">
            
            <label>Pega aquí el repertorio (una canción por línea)</label><br>
            <textarea name="repertorio_texto" rows="15" cols="50" required></textarea><br><br>

            <label>Nombre del PDF de salida</label><br>
            <input type="text" name="nombre_salida" required><br><br>

            <button type="submit">Generar PDF</button>
        </form>

    </body>
    </html>
    """

@app.post("/procesar/")
async def procesar(repertorio_texto: str = Form(...), nombre_salida: str = Form(...)):

    # ✅ Descargar PDF base
    pdf_response = requests.get(PDF_URL, timeout=30)
    pdf_response.raise_for_status()

    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_temp.write(pdf_response.content)
    pdf_temp.close()

    # ✅ Crear "repertorio.txt" a partir del texto pegado
    lista_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    lista_temp.write(repertorio_texto.encode("utf-8"))
    lista_temp.close()

    # ✅ Nombre salida
    if not nombre_salida.endswith(".pdf"):
        nombre_salida += ".pdf"

    salida_path = os.path.join(tempfile.gettempdir(), nombre_salida)

    # ✅ Ejecutar script
    resultado = subprocess.run(
        [
            "python3",
            "extraer_repertorio.py",
            pdf_temp.name,
            lista_temp.name,
            salida_path
        ],
        capture_output=True,
        text=True
    )

    if resultado.returncode != 0:
        return f"<pre>{resultado.stderr}</pre>"

    return FileResponse(salida_path, filename=nombre_salida)
