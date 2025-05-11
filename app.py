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

# ——— Paths ———
BASE_DIR            = Path(__file__).parent
HEX_DIR             = BASE_DIR / "hexagramas_txt"
LIB_DIR             = BASE_DIR / "libros_txt"
IMG_DIR             = BASE_DIR / "img_hexagramas"
MANUAL_SUMMARY_FILE = BASE_DIR / "resto_summary.txt"

# ——— Carga de resumen manual de bibliografía ———
if MANUAL_SUMMARY_FILE.exists():
    summary_others = MANUAL_SUMMARY_FILE.read_text(encoding="utf-8")
else:
    st.error("❌ Falta resto_summary.txt en la raíz del proyecto.")
    st.stop()
# Guarda en sesión para evitar relecturas
st.session_state.summary_others = summary_others

# ——— Inicializa cache de resúmenes de hexagramas ———
if "resumen_hex" not in st.session_state:
    st.session_state.resumen_hex = {}

# ——— Mensaje de bienvenida ———
st.title("🔮 I Ching IA - Consulta al Oráculo")
st.markdown("""
Bienvenido a **IChingIA**.  
Aquí puedes **escribir** tu pregunta al oráculo antes de lanzar las monedas.  
_Hazlo sólo si quieres enfocar tu tirada en algo concreto._  
Si prefieres, puedes **dejar el campo vacío** y realizar directamente la tirada.
""")

# ——— Entrada de pregunta opcional ———
pregunta = st.text_input("Escribe tu pregunta (opcional):")

# ——— Función de resumen chunked (por hexagrama) ———
def resumir_chunked(texto: str, etiqueta: str) -> str:
    MAX_CHARS = 3000
    MAX_TOKENS = 400
    chunks = [texto[i:i+MAX_CHARS] for i in range(0, len(texto), MAX_CHARS)]
    sumarios = []
    for idx, ch in enumerate(chunks, start=1):
        prompt = (
            f"Fragmento {idx}/{len(chunks)} de {etiqueta}. Resume en 250–350 tokens:\n\n"
            f"\"\"\"\n{ch}\n\"\"\"\n\n"
            f"Resumen {idx}:"
        )
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=MAX_TOKENS
        )
        sumarios.append(resp.choices[0].message.content)
    combinado = "\n\n".join(sumarios)
    final_prompt = (
        f"Une estos resúmenes parciales de {etiqueta} en uno solo (300–400 tokens):\n\n"
        f"{combinado}\n\nResumen final:"
    )
    resp2 = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.5,
        max_tokens=450
    )
    return resp2.choices[0].message.content

# ——— Funciones de tirada y carga ———
def lanzar_linea():
    monedas = [random.choice([2, 3]) for _ in range(3)]
    valor = sum(monedas)
    simbolo = "⚊" if valor in (7, 9) else "⚋"
    mutante = valor in (6, 9)
    return simbolo, mutante, valor, monedas

def obtener_hexagrama_por_lineas(lineas):
    binario = "".join("1" if s == "⚊" else "0" for s, *_ in lineas)
    return int(binario, 2) + 1

def obtener_hexagrama_mutado(lineas):
    mutadas = []
    for s, mut, *_ in lineas:
        nuevo = ("⚋" if s == "⚊" else "⚊") if mut else s
        mutadas.append((nuevo, False, None, None))
    return obtener_hexagrama_por_lineas(mutadas)

def cargar_texto_hexagrama(num):
    for fname in os.listdir(HEX_DIR):
        lower = fname.lower()
        if lower.startswith(f"{num:02}") or lower.startswith(f"hexagrama_{num}"):
            return (HEX_DIR / fname).read_text(encoding="utf-8")
    return ""

def iconos_linea(simbolo):
    return "⚫ ⚫ ⚫" if simbolo == "⚊" else "⚫ ⚪ ⚫"

# ——— Interpretación enriquecida ———
def interpretar_hexagrama(res_hex, res_lib, info_hex, pregunta_usuario):
    intro = f'Aquí tienes la interpretación del oráculo I Ching a tu pregunta: "{pregunta_usuario}"\n\n' if pregunta_usuario else ""
    prompt = f"""{intro}
HEXAGRAMA {info_hex['Numero']}: {info_hex['Nombre']} ({info_hex['Caracter']} – {info_hex['Pinyin']})

# 0️⃣ Bibliografía obligada y resumen del resto:
{res_lib}

# 1️⃣ Interpretación por Líneas
Comenta cada línea (1 a 6), menciona si es mutada y su simbolismo.

# 2️⃣ Interpretación del Hexagrama Original
Explica el mensaje global.

# 3️⃣ Hexagrama Mutado
Número, nombre y simbolismo tras mutaciones.

# 4️⃣ Interpretación del Hexagrama Mutado
Cómo cambia el mensaje.

# 5️⃣ Conclusión General
Párrafo síntesis.

# 6️⃣ Reflexión Final
Cómo aplicar este consejo.

INTERPRETACIÓN COMPLETA:
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        return resp.choices[0].message.content
    except AuthenticationError:
        st.error("🔑 Error de autenticación con OpenAI. Revisa tu OPENAI_API_KEY en Secrets.")
        st.stop()
    except OpenAIError as e:
        st.error(f"🚨 Error al llamar a OpenAI: {e}")
        st.stop()

# ——— Estado de la sesión para tiradas ———
if "manual_lineas" not in st.session_state:
    st.session_state.manual_lineas = []
if "lineas_activas" not in st.session_state:
    st.session_state.lineas_activas = []

# ——— UI de tirada ———
st.markdown("---")
modo = st.selectbox("Elige modo de tirada:", ["Automática", "Manual"], key="modo")
lineas = []

if modo == "Automática":
    if st.button("🎲 Realizar tirada"):
        lineas = [lanzar_linea() for _ in range(6)]
        st.session_state.lineas_activas = lineas
    else:
        lineas = st.session_state.lineas_activas
else:
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

# ——— Mostrar líneas ———
if lineas:
    st.markdown("### Líneas (de abajo hacia arriba):")
    for i, (s, mut, val, mon) in enumerate(lineas[::-1]):
        num = 6 - i
        iconos = iconos_linea(s)
        mut_txt = " (mutante)" if mut else ""
        st.write(f"**Línea {num}:** {s}  Valor={val}  Monedas={mon}  {iconos}{mut_txt}")

# ——— Mostrar hexagrama e interpretación ———
if len(lineas) == 6:
    num_hex = obtener_hexagrama_por_lineas(lineas)
    info    = {**HEXAGRAMAS_INFO.get(num_hex, {}), "Numero": num_hex}
    st.markdown(f"## 🔵 Hexagrama {num_hex}: {info['Nombre']} ({info['Caracter']} – {info['Pinyin']})")
    st.image(str(IMG_DIR / f"{num_hex:02d}.png"), width=150)

    if any(m for _, m, *_ in lineas):
        num_mut  = obtener_hexagrama_mutado(lineas)
        info_mut = HEXAGRAMAS_INFO.get(num_mut, {})
        st.markdown(f"## 🟠 Hexagrama Mutado {num_mut}: {info_mut['Nombre']} ({info_mut['Caracter']} – {info_mut['Pinyin']})")
        st.image(str(IMG_DIR / f"{num_mut:02d}.png"), width=150)

    # Carga resumen manual y resumen on-demand de hexagrama
    res_lib     = st.session_state.summary_others
    key         = f"hex_{num_hex}"
    if key not in st.session_state.resumen_hex:
        txt_hex = cargar_texto_hexagrama(num_hex)
        st.session_state.resumen_hex[key] = resumir_chunked(txt_hex, f"Hexagrama {num_hex}")
    resumen_hex = st.session_state.resumen_hex[key]

    # Interpretación
    with st.spinner("🧠 Interpretando oráculo..."):
        resultado = interpretar_hexagrama(resumen_hex, res_lib, info, pregunta)
    st.markdown("### 🧾 Interpretación")
    st.write(resultado)
