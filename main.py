from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
import tempfile
import requests
import os
import subprocess
import re
import html

app = FastAPI()

# PDF base
PDF_URL = "https://drive.google.com/uc?export=download&id=1GGv_629FDOYmcQ8sBJt5eOgu80Ow0xb1"


# ---------- LIMPIEZA ----------

def limpiar_playlist(texto):
    texto = html.unescape(texto)

    lineas = [l.strip() for l in texto.split("\n")]

    lineas_limpias = []
    for l in lineas:
        if not l:
            continue
        if re.search(r"\d[\d,]*\s+saves", l, re.IGNORECASE):
            continue
        if re.search(r"\b\d+\s?(hr|min)\b", l, re.IGNORECASE):
            continue
        if l.lower() in ["search", "your library", "premium", "home", "created with spotlistr - www.spotlistr.com"]:
            continue
        lineas_limpias.append(l)

    return "\n\n".join(lineas_limpias)


def normalizar_saltos(texto):
    return re.sub(r"\n\s*\n", "\n", texto).strip()


def convertir_a_lista(texto):
    texto = texto.strip('"')
    texto = texto.replace("\\n", "\n")
    return texto.strip()


# ---------- FRONT ----------

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<html>
<head>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="icon" href="https://losperrostratos.es/wp-content/uploads/2025/11/cropped-bk2a2736.jpg">

<style>

body {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 18px;

    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100svh;

    padding: 10px;

    position: relative;
}

/* ✅ fondo + overlay compatible iPhone */
body::before {
    content: "";
    position: fixed;
    inset: 0;

    background-image: url('https://losperrostratos.es/wp-content/uploads/2026/01/zevento.jpeg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;

    box-shadow: inset 0 0 0 1000px rgba(0,0,0,0.5);

    z-index: -1;
}

.container {
    width: 100%;
    max-width: 600px;
}

/* inputs */
input, textarea {
    width: 100%;
    font-size: 18px;
    padding: 10px;
    box-sizing: border-box;
    border-radius: 6px;
    border: none;
}

/* textarea */
textarea {
    height: 250px;
    resize: vertical;
}

/* botones */
button {
    font-size: 18px;
    padding: 12px 16px;
    margin-top: 10px;
    width: 100%;
    border-radius: 6px;
    border: none;
    cursor: pointer;
}

/* textos */
h1, label {
    color: white;
    font-weight: bold;
}

h1 {
    text-align: center;
}

/* iconos */
.icon {
    width: 20px;
    vertical-align: middle;
    margin-right: 8px;
}

/* ✅ MOBILE REAL */
@media (max-width: 600px) {

    body {
        align-items: flex-start;
        padding: 15px;
        font-size: 20px;
    }

    .container {
        max-width: 100%;
    }

    input, textarea {
        font-size: 20px;
        padding: 12px;
    }

    textarea {
        height: 50vh;
    }

    button {
        font-size: 20px;
        padding: 14px;
    }

    h1 {
        font-size: 24px;
    }
}

</style>
</head>

<body>

<div class="container">

    <h1>Generador de repertorios</h1>

    <label>
        <img class="icon" src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg">
        URL de playlist de Spotify
    </label><br>

    <input type="text" id="spotify_url"><br><br>

    <button type="button" onclick="procesarPlaylist()">
        Procesar playlist
    </button><br><br>

    <form action="/procesar/" method="post">

        <textarea name="repertorio_texto" required></textarea><br><br>

        <label>
            <img class="icon" src="https://upload.wikimedia.org/wikipedia/commons/8/87/PDF_file_icon.svg">
            Nombre del PDF de salida
        </label><br>

        <input type="text" name="nombre_salida" required><br><br>

        <button type="submit">Generar PDF</button>
    </form>

</div>

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


# ---------- PROCESAR PDF ----------

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

    # ✅ error real del script
    if resultado.returncode != 0:
        return f"<pre>{resultado.stderr}</pre>"

        return FileResponse(salida_path, filename=nombre_salida)


# ---------- DESCARGA ----------

@app.get("/download/{file_name}")
async def download(file_name: str):
    path = os.path.join(tempfile.gettempdir(), file_name)
    return FileResponse(path, filename=file_name)


# ---------- SPOTIFY ----------

@app.post("/spotify")
async def spotify_playlist(req: Request):

    data = await req.json()
    url = data.get("url")

    match = re.search(r"playlist/([a-zA-Z0-9]+)", url)
    if not match:
        return "URL inválida"

    playlist_id = match.group(1)

    html_page = requests.get(f"https://open.spotify.com/playlist/{playlist_id}").text

    canciones = re.findall(r'<span.*?>(.*?)</span>', html_page)

    canciones_limpias = []
    for c in canciones:
        c = c.strip()
        if 0 < len(c) < 80:
            canciones_limpias.append(c)

    texto = "\n".join(canciones_limpias[:100])

    texto = limpiar_playlist(texto)
    texto = normalizar_saltos(texto)
    texto = convertir_a_lista(texto)

    return PlainTextResponse(texto)
