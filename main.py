from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
import tempfile
import requests
import os
import subprocess
import base64
import re

app = FastAPI()

# PDF base
PDF_URL = "https://drive.google.com/uc?export=download&id=1GGv_629FDOYmcQ8sBJt5eOgu80Ow0xb1"

# Spotify credentials (pon aquí los tuyos)
CLIENT_ID = "TU_CLIENT_ID"
CLIENT_SECRET = "TU_CLIENT_SECRET"


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <body>

    <img src="https://losperrostratos.es/wp-content/uploads/2025/11/neontr.png" width="150">
    <h1>Generador de repertorios</h1>

    <label>URL de playlist Spotify</label><br>
    <input type="text" id="spotify_url" style="width:100%"><br><br>

    <button type="button" onclick="procesarPlaylist()">Procesar playlist</button><br><br>

    <form action="/procesar/" method="post">
        
        <label>Pega aquí el repertorio (una canción por línea)</label><br>
        <textarea name="repertorio_texto" rows="15" style="width:100%" required></textarea><br><br>

        <label>Nombre del PDF de salida</label><br>
        <input type="text" name="nombre_salida" required><br><br>

        <button type="submit">Generar PDF</button>

    </form>

    <script>
    async function procesarPlaylist() {
        const url = document.getElementById("spotify_url").value;

        const res = await fetch("/spotify", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url})
        });

        const text = await res.text();
        document.getElementsByName("repertorio_texto")[0].value = text;
    }
    </script>

    </body>
    </html>
    """


@app.post("/procesar/")
async def procesar(repertorio_texto: str = Form(...), nombre_salida: str = Form(...)):

    pdf_response = requests.get(PDF_URL, timeout=30)
    pdf_response.raise_for_status()

    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_temp.write(pdf_response.content)
    pdf_temp.close()

    lista_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    lista_temp.write(repertorio_texto.encode("utf-8"))
    lista_temp.close()

    if not nombre_salida.endswith(".pdf"):
        nombre_salida += ".pdf"

    salida_path = os.path.join(tempfile.gettempdir(), nombre_salida)

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


@app.post("/spotify")
async def spotify_playlist(req: Request):

    data = await req.json()
    url = data.get("url")

    match = re.search(r"playlist/([a-zA-Z0-9]+)", url)
    if not match:
        return "URL inválida"

    playlist_id = match.group(1)

    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    token_res = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth}"},
        data={"grant_type": "client_credentials"}
    )

    token = token_res.json().get("access_token")

    tracks_res = requests.get(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={"Authorization": f"Bearer {token}"}
    )

data = tracks_res.json()

if "items" not in data:
    return str(data)  # 👈 para ver error real

tracks = data.get("items", [])

    canciones = []
    for item in tracks:
        try:
            track = item["track"]
            nombre = track["name"]
            canciones.append(nombre)  # ✅ SOLO NOMBRE
        except:
            pass

    return "\n".join(canciones)
