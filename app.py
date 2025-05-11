import streamlit as st
import random
import os
import openai
from hexagramas_data import HEXAGRAMAS_INFO

# Configuración API
openai.api_key = st.secrets["OPENAI_API_KEY"]

HEXAGRAMAS_TXT_DIR = "hexagramas_txt"
LIBROS_TXT_DIR = "libros_txt"
IMG_DIR = "img_hexagramas"

def lanzar_linea():
    resultado = random.randint(6, 9)
    if resultado == 6:
        return "⚋", True
    elif resultado == 7:
        return "⚊", False
    elif resultado == 8:
        return "⚋", False
    elif resultado == 9:
        return "⚊", True

def obtener_hexagrama_por_lineas(lineas):
    binario = ''.join(['1' if l[0] == "⚊" else '0' for l in lineas])
    return int(binario, 2) % 64 + 1

def obtener_hexagrama_mutado(lineas):
    mutadas = []
    for simbolo, mutante in lineas:
        nuevo = "⚊" if simbolo == "⚋" else "⚋" if mutante else simbolo
        mutadas.append((nuevo, False))
    return obtener_hexagrama_por_lineas(mutadas)

def cargar_texto_hexagrama(num):
    for f in os.listdir(HEXAGRAMAS_TXT_DIR):
        if f.lower().startswith(f"{num:02}") or f.lower().startswith(f"hexagrama_{num}"):
            with open(os.path.join(HEXAGRAMAS_TXT_DIR, f), "r", encoding="utf-8") as file:
                return file.read()
    return "Texto no disponible."

def cargar_texto_libros():
    textos = []
    for f in os.listdir(LIBROS_TXT_DIR):
        if f.endswith(".txt"):
            with open(os.path.join(LIBROS_TXT_DIR, f), "r", encoding="utf-8") as file:
                textos.append(file.read())
    return "\n\n".join(textos[:3])

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

# Interfaz
st.set_page_config(page_title="I Ching IA", layout="centered")
st.title("🔮 I Ching IA - Interpretación de Hexagramas")

if "manual_lineas" not in st.session_state:
    st.session_state.manual_lineas = []
if "lineas_activas" not in st.session_state:
    st.session_state.lineas_activas = []

modo = st.radio("Elige el modo de tirada:", ["Tirada Automática", "Tirada Manual"])
lineas = []

if modo == "Tirada Automática":
    if st.button("🎲 Realizar tirada automática"):
        lineas = [lanzar_linea() for _ in range(6)]
        st.session_state.lineas_activas = lineas
    else:
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

if len(lineas) > 0:
    st.markdown("### Líneas del hexagrama (de abajo hacia arriba):")
    for idx, (simbolo, mutante) in enumerate(lineas[::-1]):
        st.write(f"Línea {6-idx}: {simbolo} {'(mutante)' if mutante else ''}")

if len(lineas) == 6:
    num_hex = obtener_hexagrama_por_lineas(lineas)
    info = HEXAGRAMAS_INFO.get(num_hex, {"Nombre": "Desconocido", "Caracter": "?", "Pinyin": "?"})
    st.markdown(f"## 🔵 Hexagrama {num_hex}: {info['Nombre']} ({info['Caracter']} – {info['Pinyin']})")
    st.image(f"{IMG_DIR}/{num_hex:02d}.png", width=200)

    if any(mut for _, mut in lineas):
        num_mutado = obtener_hexagrama_mutado(lineas)
        info_mutado = HEXAGRAMAS_INFO.get(num_mutado, {"Nombre": "Desconocido", "Caracter": "?", "Pinyin": "?"})
        st.markdown(f"## 🟠 Hexagrama Mutado {num_mutado}: {info_mutado['Nombre']} ({info_mutado['Caracter']} – {info_mutado['Pinyin']})")
        st.image(f"{IMG_DIR}/{num_mutado:02d}.png", width=200)

    with st.spinner("🧠 Interpretando con GPT..."):
        texto_hex = cargar_texto_hexagrama(num_hex)
        texto_libros = cargar_texto_libros()
        interpretacion = interpretar_hexagrama(texto_hex, texto_libros, info)

    st.markdown("### 🧾 Interpretación")
    st.write(interpretacion)