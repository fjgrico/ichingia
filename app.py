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

# ——— Simular lanzamiento de monedas clásico ———
def lanzar_linea():
    monedas = [random.choice([2, 3]) for _ in range(3)]
    valor   = sum(monedas)
    simbolo = "⚊" if valor in (7, 9) else "⚋"
    mutante = valor in (6, 9)
    return simbolo, mutante, valor, monedas

def obtener_hexagrama_por_lineas(lineas):
    binario = "".join("1" if s=="⚊" else "0" for s, *_ in lineas)
    return int(binario,2) + 1

def obtener_hexagrama_mutado(lineas):
    mutadas = []
    for s, mut, *_ in lineas:
        if mut:
            nuevo = "⚋" if s=="⚊" else "⚊"
        else:
            nuevo = s
        mutadas.append((nuevo, False, None, None))
    return obtener_hexagrama_por_lineas(mutadas)

# ——— Carga de textos ———
def cargar_texto_hexagrama(num):
    for fname in os.listdir(HEXAGRAMAS_TXT_DIR):
        if fname.lower().startswith(f"{num:02}") or fname.lower().startswith(f"hexagrama_{num}"):
            return (HEXAGRAMAS_TXT_DIR / fname).read_text(encoding="utf-8")
    return "Texto no disponible."

def cargar_texto_libros():
    for fname in sorted(os.listdir(LIBROS_TXT_DIR)):
        if fname.lower().endswith(".txt"):
            return (LIBROS_TXT_DIR / fname).read_text(encoding="utf-8")
    return ""

# ——— Iconos visuales ———
def iconos_linea(simbolo):
    return "⚫ ⚫ ⚫" if simbolo=="⚊" else "⚫ ⚪ ⚫"

# ——— Llamada de resumen ———
def resumir_texto(texto, etiqueta):
    prompt = f"Por favor, resume brevemente (300–400 tokens) el siguiente texto del {etiqueta} para su posterior interpretación:\n\n\"\"\"\n{texto}\n\"\"\"\nResumen:"
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.5,
            max_tokens=400
        )
        return resp.choices[0].message.content
    except OpenAIError as e:
        st.error(f"🚨 Error al resumir {etiqueta}: {e}")
        st.stop()

# ——— Interpretación final ———
def interpretar_hexagrama(res_hex, res_lib, info_hex, pregunta_usuario):
    if pregunta_usuario:
        intro = f'Aquí tienes la interpretación del oráculo I Ching a tu pregunta: "{pregunta_usuario}"\n\n'
    else:
        intro = ""
    prompt = f"""{intro}
HEXAGRAMA: {info_hex['Nombre']} ({info_hex['Pinyin']} – {info_hex['Caracter']})

RESUMEN DEL HEXAGRAMA:
{res_hex}

RESUMEN DEL TEXTO CLÁSICO:
{res_lib}

Interpreta estos resúmenes desde los enfoques:
- Espiritual (Taoísta, Budista...)
- Emocional / Relacional
- Profesional / Decisiones
- Salud / Bienestar

INTERPRETACIÓN:"""
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
            max_tokens=800
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

# ——— Interfaz de tirada ———
st.markdown("---")
modo = st.selectbox("Elige modo de tirada:", ["Automática", "Manual"], key="modo")
lineas = []

if modo=="Automática":
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
    for i, (simb, mut, valor, monedas) in enumerate(lineas[::-1]):
        num = 6 - i
        iconos = iconos_linea(simb)
        mut_text = " (mutante)" if mut else ""
        st.write(f"**Línea {num}:** {simb}  Valor={valor}  Monedas={monedas}  {iconos}{mut_text}")

# ——— Al tener 6 líneas, procedemos ———
if len(lineas)==6:
    num_hex = obtener_hexagrama_por_lineas(lineas)
    info    = HEXAGRAMAS_INFO.get(num_hex, {"Nombre":"Desconocido","Caracter":"?","Pinyin":"?"})
    st.markdown(f"## 🔵 Hexagrama {num_hex}: {info['Nombre']} ({info['Caracter']} – {info['Pinyin']})")
    st.image(str(IMG_DIR/f"{num_hex:02d}.png"), width=150)

    if any(mut for _,mut,*_ in lineas):
        num_mut = obtener_hexagrama_mutado(lineas)
        info_m  = HEXAGRAMAS_INFO.get(num_mut, {"Nombre":"Desconocido","Caracter":"?","Pinyin":"?"})
        st.markdown(f"## 🟠 Hexagrama Mutado {num_mut}: {info_m['Nombre']} ({info_m['Caracter']} – {info_m['Pinyin']})")
        st.image(str(IMG_DIR/f"{num_mut:02d}.png"), width=150)

    # ── Resumir ──
    with st.spinner("📝 Resumiendo textos..."):
        txt_hex = cargar_texto_hexagrama(num_hex)
        txt_lib = cargar_texto_libros()
        resumen_hex = resumir_texto(txt_hex, "hexagrama")
        resumen_lib = resumir_texto(txt_lib, "texto clásico")

    # ── Interpretar ──
    with st.spinner("🧠 Interpretando oráculo..."):
        resultado = interpretar_hexagrama(resumen_hex, resumen_lib, info, pregunta)

    st.markdown("### 🧾 Interpretación")
    st.write(resultado)
