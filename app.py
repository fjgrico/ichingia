import streamlit as st
import random
import os
import openai
from hexagramas_data import HEXAGRAMAS_INFO

# Configurar API de OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Rutas locales
HEXAGRAMAS_TXT_DIR = "hexagramas_txt_final/hexagramas_txt"
LIBROS_TXT_DIR = "libros_txt_final/libros_txt"

# Función para lanzar una línea (yin o yang, mutante o no)
def lanzar_linea():
    resultado = random.randint(6, 9)
    if resultado == 6:
        return "⚋", True  # yin mutante
    elif resultado == 7:
        return "⚊", False  # yang
    elif resultado == 8:
        return "⚋", False  # yin
    elif resultado == 9:
        return "⚊", True  # yang mutante

# Cálculo del número de hexagrama según líneas (simplificado aquí)
def obtener_hexagrama_por_lineas(lineas):
    binario = ''.join(['1' if l[0] == "⚊" else '0' for l in lineas])
    return int(binario, 2) % 64 + 1  # Hexagrama del 1 al 64

# Cargar contenido del hexagrama en TXT
def cargar_texto_hexagrama(num):
    archivos = os.listdir(HEXAGRAMAS_TXT_DIR)
    for f in archivos:
        if f.startswith(f"{num:02}") or f.startswith(f"hexagrama_{num}"):
            with open(os.path.join(HEXAGRAMAS_TXT_DIR, f), "r", encoding="utf-8") as file:
                return file.read()
    return "Texto no disponible."

# Cargar libros como base de interpretación
def cargar_texto_libros():
    textos = []
    for f in os.listdir(LIBROS_TXT_DIR):
        if f.endswith(".txt"):
            with open(os.path.join(LIBROS_TXT_DIR, f), "r", encoding="utf-8") as file:
                textos.append(file.read())
    return "\n\n".join(textos[:3])  # limitar a 3 libros por rendimiento

# GPT: interpretar hexagrama
def interpretar_hexagrama(texto_hex, texto_libros, info_hexagrama):
    prompt = f"""
Actúa como un sabio experto en I Ching y desarrollo personal. Usa el texto base del hexagrama y tu conocimiento para analizarlo desde los siguientes enfoques: emocional, sentimental, espiritual, profesional, trabajo, familiar, salud y relaciones.

HEXAGRAMA: {info_hexagrama['Nombre']} ({info_hexagrama['Pinyin']} - {info_hexagrama['Caracter']})

TEXTO BASE:
{texto_hex}

BASE ADICIONAL:
{texto_libros}

INTERPRETACIÓN:
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1200
    )
    return response.choices[0].message.content

# Streamlit UI
st.title("🔮 I Ching IA - Interpretación de Hexagramas")

st.markdown("### Elige una opción para generar tu hexagrama:")
modo = st.radio("Modo de tirada", ["Tirada Automática", "Tirada Manual"], key="modo_tirada")
lineas = []

if "manual_lineas" not in st.session_state:
    st.session_state.manual_lineas = []

if modo == "Tirada Automática":
    if st.button("🎲 Realizar tirada automática"):
        st.session_state.manual_lineas = []
        lineas = [lanzar_linea() for _ in range(6)]
        st.session_state.lineas_activas = lineas
    elif "lineas_activas" in st.session_state:
        lineas = st.session_state.lineas_activas

elif modo == "Tirada Manual":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Lanzar línea"):
            if len(st.session_state.manual_lineas) < 6:
                st.session_state.manual_lineas.append(lanzar_linea())
    with col2:
        if st.button("🔁 Reiniciar"):
            st.session_state.manual_lineas = []
            st.session_state.lineas_activas = []

    lineas = st.session_state.manual_lineas
    st.session_state.lineas_activas = lineas

st.markdown("Elige una opción para generar tu hexagrama:")

modo = st.radio("Modo de tirada", ["Tirada Automática", "Tirada Manual"])
lineas = []

if "manual_lineas" not in st.session_state:
    st.session_state.manual_lineas = []

if modo == "Tirada Automática":
    if st.button("🎲 Realizar tirada automática"):
        lineas = [lanzar_linea() for _ in range(6)]
elif modo == "Tirada Manual":
    if st.button("➕ Lanzar línea"):
        st.session_state.manual_lineas.append(lanzar_linea())
    if st.button("🔁 Reiniciar"):
        st.session_state.manual_lineas = []
    lineas = st.session_state.manual_lineas

if lineas:
    st.markdown("### Líneas del hexagrama (de abajo hacia arriba):")
    for idx, (simbolo, mutante) in enumerate(lineas[::-1]):
        st.write(f"Línea {6-idx}: {simbolo} {'(mutante)' if mutante else ''}")

    if len(lineas) == 6:
        numero_hex = obtener_hexagrama_por_lineas(lineas)
        info = HEXAGRAMAS_INFO.get(numero_hex, {"Nombre": "Desconocido", "Caracter": "?", "Pinyin": "?"})
        st.markdown(f"## ✨ Hexagrama {numero_hex}: {info['Nombre']} ({info['Caracter']}, {info['Pinyin']})")

        texto_hex = cargar_texto_hexagrama(numero_hex)
        texto_libros = cargar_texto_libros()

        with st.spinner("🧠 Interpretando con IA..."):
            interpretacion = interpretar_hexagrama(texto_hex, texto_libros, info)

        st.markdown("### 🧾 Interpretación")
        st.write(interpretacion)