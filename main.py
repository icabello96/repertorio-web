from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import requests
import os
import subprocess

app = FastAPI()

# ✅ IMPORTANTE: enlace directo al PDF
PDF_URL = "https://drive.google.com/uc?export=download&id=1GGv_629FDOYmcQ8sBJt5eOgu80Ow0xb1"


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
async def procesar(lista: UploadFile = File(...), nombre_salida: str = Form(...)):
    try:
        # ✅ Descargar PDF base
        pdf_response = requests.get(PDF_URL, timeout=30)
        pdf_response.raise_for_status()

        # ✅ Validar que es PDF real
        if "application/pdf" not in pdf_response.headers.get("Content-Type", ""):
            return "<h2>Error: la URL no devuelve un PDF válido</h2>"

        # ✅ Guardar PDF temporal
        pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_temp.write(pdf_response.content)
        pdf_temp.close()

        # ✅ Leer archivo subido
        lista_bytes = await lista.read()
        lista_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        lista_temp.write(lista_bytes)
        lista_temp.close()

        # ✅ Nombre archivo salida
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

        # ✅ Si falla, mostrar error
        if resultado.returncode != 0:
            return f"<pre>{resultado.stderr}</pre>"

        # ✅ Devolver PDF generado
        return FileResponse(salida_path, filename=nombre_salida)

    except Exception as e:
        return f"<pre>{str(e)}</pre>"
