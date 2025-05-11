import os
import random
import json
from pathlib import Path

import streamlit as st
from openai import OpenAI, OpenAIError, AuthenticationError

from hexagramas_data import HEXAGRAMAS_INFO

# ——— Configuración de página y cliente OpenAI ———
st.set_page_config(page_title="I Ching IA", layout="centered")
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ No encuentro OPENAI_API_KEY. Ponla en Settings → Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# ——— Paths y cache ———
BASE_DIR   = Path(__file__).parent
HEX_DIR    = BASE_DIR / "hexagramas_txt"
LIB_DIR    = BASE_DIR / "libros_txt"
IMG_DIR    = BASE_DIR / "img_hexagramas"
CACHE_DIR  = BASE_DIR / ".cache"
CACHE_FILE = CACHE_DIR / "summaries.json"
os.makedirs(CACHE_DIR, exist_ok=True)

# ——— Función chunked resumen (idéntica al script) ———
def resumir_chunked(texto, etiqueta):
    MAX_CHARS, MAX_TOKENS = 3000, 400
    chunks = [texto[i:i+MAX_CHARS] for i in range(0, len(texto), MAX_CHARS)]
    partials = []
    for idx, chunk in enumerate(chunks, 1):
        prompt = (
            f"Fragmento {idx}/{len(chunks)} de {etiqueta}. "
            "Resume en 250–350 tokens:\n\n"
            f"\"\"\"\n{chunk}\n\"\"\"\n\nResumen {idx}:"
        )
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.5,
            max_tokens=MAX_TOKENS
        )
        partials.append(resp.choices[0].message.content)
    combo = "\n\n".join(partials)
    prompt2 = (
        f"Une estos resúmenes parciales de {etiqueta} en uno solo (300–400 tokens):\n\n"
        f"{combo}\n\nResumen final:"
    )
    resp2 = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt2}],
        temperature=0.5,
        max_tokens=450
    )
    return resp2.choices[0].message.content

# ——— Pre-genera cache si no existe ———
if not CACHE_FILE.exists():
    with st.spinner("🔄 Generando cache de resúmenes (esto tarda unos minutos)…"):
        # 1) carga textos
        hex_texts = {
            f: (HEX_DIR / f).read_text(encoding="utf-8")
            for f in os.listdir(HEX_DIR) if f.lower().endswith(".txt")
        }
        lib_texts = {
            f: (LIB_DIR / f).read_text(encoding="utf-8")
            for f in os.listdir(LIB_DIR) if f.lower().endswith(".txt")
        }
        # 2) define 8 libros completos
        BASE_BOOKS = [
            "8Virtues_Spanish.txt",
            "I_Ching_El_libro_de_las_mutaciones_-_Richard_Wilhelm.txt",
            "EL-SECRETO-de-la-FLOR-de-ORO_Raquel-Paricio_v2.txt",
            "I_Ching_El_Libro_de_los_Cambios_-_James_Legge.txt",
            "I_CHING_RICHARD_WILHELM_(COMPLETO_VERSIÓN_VOGELMANN).txt",
            "I_CHING_Ritsema_Karcher_COMPLETO.txt",
            "I_Ching_señales_de_Amor.Karcher.txt",
            "Ricardo_Andreë_(extraïdo_de_su_libro__Tratado_I_Ching,_el_Canon_de_las_Mutaciones,_el_Séptimo._Tiempo)_TIEMPOS.txt"
        ]
        # 3) resumen del resto de bibliografía
        resto = "\n\n".join(
            txt for f, txt in lib_texts.items() if f not in BASE_BOOKS
        )
        summary_others = resumir_chunked(resto, "resto de bibliografía")
        # 4) resumen de cada hexagrama
        resumen_hex = {}
        for fname, txt in hex_texts.items():
            num = int(''.join(filter(str.isdigit, fname)))
            etiqueta = f"Hexagrama {num}"
            resumen_hex[f"hex_{num}"] = resumir_chunked(txt, etiqueta)
        # 5) vuelca todo a disco
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "summary_others": summary_others,
                "resumen_hex": resumen_hex
            }, f, ensure_ascii=False, indent=2)

# ——— Carga cache en memoria ———
with open(CACHE_FILE, "r", encoding="utf-8") as f:
    disk_cache = json.load(f)
st.session_state.summary_others = disk_cache["summary_others"]
st.session_state.resumen_hex    = disk_cache["resumen_hex"]

# ——— Resto de app: UI, tirada, interpretación… ———

# Funciones de tirada, carga de texto, iconos, y función interpretar_hexagrama
def lanzar_linea(): …
def obtener_hexagrama_por_lineas(lineas): …
def obtener_hexagrama_mutado(lineas): …
def cargar_texto_hexagrama(num): …
def iconos_linea(simbolo): …

def interpretar_hexagrama(res_hex, res_lib, info_hex, pregunta_usuario): …

# Estado de sesión para tirada manual/automática…
if "manual_lineas" not in st.session_state: …
if "lineas_activas" not in st.session_state: …

# UI: título, explicación, pregunta, botones de tirada…
# Mostrar líneas…
# Mostrar hexagramas e interpretación, usando:
#   res_lib  = st.session_state.summary_others
#   resumen_hex = st.session_state.resumen_hex[f"hex_{num_hex}"]

# …y el resto de tu lógica actual sin modificaciones significativas.
