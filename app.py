import os
import random
from pathlib import Path

import streamlit as st
from openai import OpenAI, OpenAIError, AuthenticationError

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

# ——— Lógica de tirada de líneas ———
def lanzar_linea():
    resultado = random.randint(6, 9)
    simbolo = "⚊" if resultado in (7, 9) else "⚋"
    mutante = resultado in (6, 9)
    return simbolo, mutante

def obtener_hexagrama_por_lineas(lineas):
    binario = "".join("1" if s == "⚊" else "0" for s, _ in lineas)
    return int(binario, 2) + 1

def obtener_hexagrama_mutado(lineas):
    mutadas = []
    for s, mut in lineas:
        if mut:
            nuevo = "⚋" if s == "⚊" else "⚊"
        else:
            nuevo = s
        mutadas.append((nuevo, False))
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
            textos.append((LIBROS_TXT_DIR / fname).read_text(encoding="utf-8"))
    return "\n\n".join(textos[:3])

# ——— Iconos visuales ———
def iconos_linea(simbolo):
    # Línea continua (⚊): ⚫ ⚫ ⚫  /  Línea discontinua (⚋): ⚫ ⚪ ⚫
    return "⚫ ⚫ ⚫" if simbolo == "⚊" else "⚫ ⚪ ⚫"

# ——— Interpretación con GPT ———
def interpretar_hexagrama(texto_hex, texto_libros, info_hex):
    prompt = f"""
Actúa como un sabio experto en I Ching y desarrollo personal. Ofrece interpretación en varios enfoques:
- Espiritual (Taoísta, Budista, etc.)
- Emocional / Relacional
- Profesional / Decisiones
- Salud / Bienestar

HEXAGRAMA: {info_hex['Nombre']} ({info_hex['Pinyin']} – {info_hex['Caracter']})

TEXTO BASE:
{texto_hex}

BASE ADICIONAL:
{texto_libros}

INTERPRETACIÓN:
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        return resp.choices[0].message.content
    except AuthenticationError:
        st.error("🔑 Error de autenticación con OpenAI. Revisa tu OPENAI_API_KEY en Settings → Secrets.")
        st.stop()
    except OpenAIError as e:
        st.error(f"🚨 Error al llamar a OpenAI: {e}")
        st.stop()

# ——— Estado de la sesión ———
if "manual_lineas" not in st.session_state:
    st.session_state.manual_lineas = []
if "lineas_activas" not in st.session_state:
    st.session_state.lineas_activas = []

# ——— Interfaz de usuario ———
st.title("🔮 I Ching IA - Interpretación de Hexagramas")
modo = st.selectbox("Elige el modo de tirada:", ["Tirada Automática", "Tirada Manual"], key="modo_tirada")
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

# Mostrar líneas con iconos
if len(lineas) > 0:
    st.markdown("### Líneas del hexagrama (de abajo hacia arriba):")
    for i, (simb, mut) in enumerate(lineas[::-1]):
        linea_num = 6 - i
        iconos = iconos_linea(simb)
        mut_text = " (mutante)" if mut else ""
        st.write(f"**Línea {linea_num}:** {simb}{mut_text}   {iconos}")

# Cuando hay 6 líneas, enseña el hexagrama y la interpretación
if len(lineas) == 6:
    num_hex = obtener_hexagrama_por_lineas(lineas)
    info    = HEXAGRAMAS_INFO.get(num_hex, {"Nombre":"Desconocido","Caracter":"?","Pinyin":"?"})
    st.markdown(f"## 🔵 Hexagrama {num_hex}: {info['Nombre']} ({info['Caracter']} – {info['Pinyin']})")
    st.image(str(IMG_DIR / f"{num_hex:02d}.png"), width=150)

    if any(mut for _, mut in lineas):
        num_mut = obtener_hexagrama_mutado(lineas)
        info_m  = HEXAGRAMAS_INFO.get(num_mut, {"Nombre":"Desconocido","Caracter":"?","Pinyin":"?"})
        st.markdown(f"## 🟠 Hexagrama Mutado {num_mut}: {info_m['Nombre']} ({info_m['Caracter']} – {info_m['Pinyin']})")
        st.image(str(IMG_DIR / f"{num_mut:02d}.png"), width=150)

    with st.spinner("🧠 Interpretando con GPT..."):
        txt_hex     = cargar_texto_hexagrama(num_hex)
        txt_libros  = cargar_texto_libros()
        interpretacion = interpretar_hexagrama(txt_hex, txt_libros, info)

    st.markdown("### 🧾 Interpretación")
    st.write(interpretacion)
