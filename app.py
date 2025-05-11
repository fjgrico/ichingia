import os
import random
from pathlib import Path

import streamlit as st
from openai import OpenAI, OpenAIError, AuthenticationError, Audio

from hexagramas_data import HEXAGRAMAS_INFO

# ——— Configuración de la página ———
st.set_page_config(page_title="I Ching IA", layout="centered")

# ——— API Key de OpenAI ———
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ No se ha encontrado OPENAI_API_KEY. Añádela en Settings → Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# ——— Rutas absolutas ———
BASE_DIR = Path(__file__).parent
HEXAGRAMAS_TXT_DIR = BASE_DIR / "hexagramas_txt"
LIBROS_TXT_DIR     = BASE_DIR / "libros_txt"
IMG_DIR            = BASE_DIR / "img_hexagramas"

# ——— Mensaje de bienvenida y explicación ———
st.title("🔮 I Ching IA - Consulta al Oráculo")
st.markdown("""
Bienvenido a **IChingIA**.  
Aquí puedes **escribir** tu pregunta al oráculo o **grabar** tu voz para formularla.  
_Hazlo sólo si quieres enfocar tu tirada en algo concreto.  
Si prefieres, puedes omitir la pregunta y realizar directamente la tirada._  
""")

# ——— Entrada de pregunta (texto o audio) ———
pregunta_texto = st.text_input("Escribe tu pregunta (opcional):")
audio_pregunta = st.file_uploader("O arrastra/selecciona un archivo de audio (opcional):", type=["wav","mp3","m4a"])

pregunta = ""
if pregunta_texto:
    pregunta = pregunta_texto
elif audio_pregunta:
    st.audio(audio_pregunta)
    with st.spinner("🎙️ Transcribiendo tu pregunta..."):
        try:
            # Transcripción con Whisper
            resp = client.audio.transcriptions.create(
                file=audio_pregunta,
                model="whisper-1"
            )
            pregunta = resp.text
            st.write("**Tu pregunta (transcrita):**", pregunta)
        except OpenAIError as e:
            st.error(f"🚨 Error al transcribir audio: {e}")
            st.stop()

# ——— Lógica de tirada de líneas ———
def lanzar_linea():
    monedas = [random.choice([2, 3]) for _ in range(3)]
    valor   = sum(monedas)
    simbolo = "⚊" if valor in (7, 9) else "⚋"
    mutante = valor in (6, 9)
    return simbolo, mutante, valor, monedas

def obtener_hexagrama_por_lineas(lineas):
    binario = "".join("1" if s == "⚊" else "0" for s, *_ in lineas)
    return int(binario, 2) + 1

def obtener_hexagrama_mutado(lineas):
    mutadas = []
    for s, mut, *_ in lineas:
        nuevo = "⚋" if (s=="⚊" and mut) else ("⚊" if (s=="⚋" and mut) else s)
        mutadas.append((nuevo, False, None, None))
    return obtener_hexagrama_por_lineas(mutadas)

# ——— Carga de textos ———
def cargar_texto_hexagrama(num):
    for fname in os.listdir(HEXAGRAMAS_TXT_DIR):
        lower = fname.lower()
        if lower.startswith(f"{num:02}") or lower.startswith(f"hexagrama_{num}"):
            return (HEXAGRAMAS_TXT_DIR / fname).read_text(encoding="utf-8")
    return "Texto no disponible."

def cargar_texto_libros():
    textos = []
    for fname in os.listdir(LIBROS_TXT_DIR):
        if fname.lower().endswith(".txt"):
            textos.append
