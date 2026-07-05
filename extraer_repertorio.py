#!/usr/bin/env python3
# extraer_repertorio.py
# Requiere: pip3 install pymupdf pypdf

import sys, unicodedata, re
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter


# ---------- Normalización ----------

def normalize_text(s):
    s = (s or "").upper()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    s = re.sub(r'[^A-Z0-9 #]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def limpiar_titulo_lista(s):
    """
    Elimina info extra en la lista:
    - texto entre paréntesis
    - texto después de '-'
    """
    s = re.sub(r'\(.*?\)', '', s)
    s = s.split('-')[0]
    return s.strip()


def titulo_base(norm_title):
    """
    Elimina tonalidades:
    F#M, C#m, Bb, BbM7, etc.
    """
    return re.sub(
        r'\s+[A-G](#|B)?(M|MAJ7|M7|MIN|M|7|DIM|AUG)?$',
        '',
        norm_title
    ).strip()


# ---------- Detección de canciones ----------

def detectar_canciones(pdf_path, size_threshold=20):
    doc = fitz.open(pdf_path)
    candidatos = []

    for i, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for l in b.get("lines", []):
                spans = l.get("spans", [])
                if not spans:
                    continue

                max_size = max(s.get("size", 0) for s in spans)
                text_line = ''.join(s.get("text", '') for s in spans).strip()

                if len(text_line) < 3:
                    continue

                if any(tok in text_line for tok in ['|', '||', ':', '—']) and len(text_line) < 40:
                    continue

                if text_line.upper() == text_line and max_size >= size_threshold:
                    norm = normalize_text(text_line)
                    base = titulo_base(norm)

                    if not base:
                        continue

                    if any(k in base for k in [
                        "INTRO", "ESTROFA", "BILLO", "ESTRIBILLO",
                        "POSTCORO", "PUENTE", "SOLO", "OUTRO"
                    ]):
                        continue

                    candidatos.append((text_line.strip(), base, i))

    canciones = []
    for idx, (titulo, base, inicio) in enumerate(candidatos):
        fin = candidatos[idx + 1][2] - 1 if idx + 1 < len(candidatos) else len(doc) - 1
        canciones.append((titulo, base, inicio, fin))

    return canciones


# ---------- Extracción ----------

def extraer(pdf_path, lista_path, salida_path):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    canciones = detectar_canciones(pdf_path)
    if not canciones:
        print("Error: no se detectaron títulos.")
        return

    print(f"Detectadas {len(canciones)} canciones.\n")

    with open(lista_path, "r", encoding="utf-8") as f:
        deseadas_raw = [l.strip() for l in f if l.strip()]

    deseadas = [
        normalize_text(limpiar_titulo_lista(x))
        for x in deseadas_raw
    ]

    for original, buscado in zip(deseadas_raw, deseadas):
        coincidencias = [
            (titulo, ini, fin)
            for titulo, base, ini, fin in canciones
            if base == buscado
        ]

        if coincidencias:
            print(f"✓ {original} → {len(coincidencias)} versión(es)")
            for titulo, ini, fin in coincidencias:
                print(f"   - {titulo} (páginas {ini + 1}-{fin + 1})")
                for p in range(ini, fin + 1):
                    writer.add_page(reader.pages[p])
        else:
            print(f"⚠️ No encontrada: {original}")

    with open(salida_path, "wb") as f:
        writer.write(f)

    print(f"\nPDF generado: {salida_path}")


# ---------- Main ----------

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python3 extraer_repertorio.py <PDF> <lista.txt> <salida.pdf>")
        sys.exit(1)

    extraer(sys.argv[1], sys.argv[2], sys.argv[3])
