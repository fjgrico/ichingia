# ——— Interpretación final enriquecida ———
def interpretar_hexagrama(res_hex, res_lib, info_hex, pregunta_usuario):
    # Intro personalizada si hay pregunta
    if pregunta_usuario:
        intro = f'Aquí tienes la interpretación del oráculo I Ching a tu pregunta: "{pregunta_usuario}"\n\n'
    else:
        intro = ""
    # Prompt estructurado en secciones
    prompt = f"""{intro}
HEXAGRAMA: {info_hex['Nombre']} ({info_hex['Pinyin']} – {info_hex['Caracter']})

# 1️⃣ Interpretación por Líneas
Por favor, comenta brevemente cada una de las seis líneas (de la 1 a la 6), explicando su simbolismo y cómo contribuye al mensaje general.

# 2️⃣ Resumen del Hexagrama
{res_hex}

# 3️⃣ Resumen del Texto Clásico
{res_lib}

# 4️⃣ Conclusión General
Ofrece un párrafo que sintetice el mensaje central del hexagrama.

# 5️⃣ Reflexión Final
Incluye una reflexión práctica: ¿cómo podría el consultante aplicar este consejo en su vida diaria?

INTERPRETACIÓN COMPLETA:
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return resp.choices[0].message.content
    except AuthenticationError:
        st.error("🔑 Error de autenticación con OpenAI. Revisa tu OPENAI_API_KEY en Settings → Secrets.")
        st.stop()
    except OpenAIError as e:
        st.error(f"🚨 Error al llamar a OpenAI: {e}")
        st.stop()
