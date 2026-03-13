import streamlit as st
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import tempfile
import os
from gtts import gTTS
import base64
import urllib.parse

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Kiosco Escudo Ciudadano", page_icon="🛡️", layout="centered")

# --- ESTILOS VISUALES EXTREMOS (Botones gigantes) ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 100px;
        font-size: 24px;
        font-weight: bold;
        border-radius: 15px;
    }
    .big-icon { font-size: 50px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- SEGURIDAD ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("⚠️ Falta configurar la Llave API.")
    st.stop()

# --- BOTÓN DE AYUDA HUMANA (Siempre visible arriba) ---
if st.button("🆘 NECESITO AYUDA", type="primary", use_container_width=True):
    st.error("🚨 **ALERTA VISUAL:** POR FAVOR, UN ASESOR ACÉRQUESE A AYUDAR AL CIUDADANO.")
    st.stop()

st.markdown("<h1 style='text-align: center;'>🛡️ ESCUDO CIUDADANO</h1>", unsafe_allow_html=True)
st.divider()

# --- PASO 1: SELECCIÓN VISUAL (ICONOGRAFÍA EXTREMA) ---
st.markdown("### 1️⃣ ¿De qué se trata su problema? Toca un dibujo:")

if 'categoria' not in st.session_state:
    st.session_state['categoria'] = "General"

col1, col2 = st.columns(2)
with col1:
    if st.button("💧 Luz, Agua, Calles"): st.session_state['categoria'] = "Servicios Públicos (Luz, Agua, Calles)"
    if st.button("🏥 Salud y Médicos"): st.session_state['categoria'] = "Atención Médica y Salud"
with col2:
    if st.button("🚓 Multas y Policía"): st.session_state['categoria'] = "Seguridad, Multas y Policía"
    if st.button("🌾 Apoyo y Gobierno"): st.session_state['categoria'] = "Programas Sociales y Trámites"

st.success(f"✅ Tema seleccionado: **{st.session_state['categoria']}**")

# --- PASO 2: EL MICRÓFONO ÚNICO ---
st.markdown("### 2️⃣ Toca el micrófono. Dinos tu Nombre, de dónde eres y cuál es el problema:")
st.info("💡 Puedes hablar en tu propio idioma (Maya, Náhuatl, Zapoteco, etc.) o en Español.")

audio_grabado = st.audio_input("🎤 TOCA AQUÍ PARA HABLAR")

# --- FUNCIÓN PARA GENERAR WORD ---
def crear_word(texto_oficio):
    doc = Document()
    estilo = doc.styles['Normal']
    estilo.font.name = 'Arial'
    estilo.font.size = Pt(12)
    for linea in texto_oficio.split('\n'):
        if linea.strip():
            p = doc.add_paragraph(linea.strip())
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    archivo_memoria = BytesIO()
    doc.save(archivo_memoria)
    return archivo_memoria.getvalue()

# --- FUNCIÓN PARA QUE LA APP HABLE (Text to Speech) ---
def reproducir_audio(texto):
    tts = gTTS(text=texto, lang='es', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        with open(fp.name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
        os.remove(fp.name)

# --- LÓGICA DE IA CON DOBLE REVISIÓN ---
if audio_grabado:
    if st.button("🚀 HACER MI DOCUMENTO", use_container_width=True, type="primary"):
        with st.status("⚙️ Escuchando y procesando tu caso...", expanded=True) as status:
            archivos_temporales = []
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # --- PASO 1: CREAR RESUMEN HABLADO Y BORRADOR ---
                status.update(label="⏳ Paso 1/2: Escuchando tu voz y redactando el borrador...", state="running")
                
                prompt_texto = f"""
                ERES UN ABOGADO PRO BONO MEXICANO. Has recibido un audio de un ciudadano que requiere ayuda sobre: {st.session_state['categoria']}.
                El audio puede estar en español o lengua indígena. Extrae su nombre, dirección y el problema.
                
                Instrucciones estrictas:
                Genera tu respuesta separada por la palabra exacta "DIVISOR_K".
                
                PARTE 1 (Resumen para leer en voz alta al ciudadano):
                Escribe un texto muy breve, amable y en español simple, como si le hablaras a un abuelo. Diciendo: "Hola [Nombre], ya terminé su documento sobre [resumen del problema]. Por favor pida ayuda para imprimirlo."
                
                DIVISOR_K
                
                PARTE 2 (Oficio Legal Borrador):
                Redacta el oficio legal completo, fundamentado en leyes mexicanas. 
                REGLA DE ORO: Redactado SIEMPRE en PRIMERA PERSONA ("yo, comparezco por mi propio derecho"), firmado por el ciudadano. Si detectaste lengua indígena en el audio, invoca el Art. 2 Constitucional. Formato texto plano sin asteriscos.
                """
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as t:
                    t.write(audio_grabado.getvalue())
                    archivos_temporales.append(t.name)
                    audio_ia = genai.upload_file(t.name)
                
                respuesta_borrador = model.generate_content([audio_ia, prompt_texto])
                
                # Separar la respuesta de la IA
                partes = respuesta_borrador.text.split("DIVISOR_K")
                if len(partes) == 2:
                    resumen_hablado = partes[0].replace("*", "").strip()
                    oficio_borrador = partes[1].replace("*", "").replace("#", "").strip()
                    
                    # --- PASO 2: EL FILTRO ANTI-ALUCINACIONES AL DOCUMENTO LEGAL ---
                    status.update(label="🔍 Paso 2/2: Verificando que las leyes sean reales y correctas...", state="running")
                    
                    prompt_revision = f"""
                    ERES UN REVISOR LEGAL MEXICANO ESTRICTO (Socio de Despacho).
                    Tu única tarea es leer el siguiente borrador de un oficio y ELIMINAR CUALQUIER ALUCINACIÓN DE IA.
                    
                    REGLAS ESTRICTAS:
                    1. Si el borrador cita un Artículo, Ley o Reglamento del que NO estás 100% seguro de que existe y es vigente en México, BÓRRALO y adapta la redacción.
                    2. Es preferible fundamentar con el "Artículo 8 Constitucional (Derecho de Petición)" y principios generales, a inventar una ley municipal.
                    3. Mantén la redacción en PRIMERA PERSONA ("yo, comparezco").
                    4. Devuelve ÚNICAMENTE el texto final del oficio corregido y limpio (sin asteriscos ni markdown).
                    
                    BORRADOR A REVISAR Y CORREGIR:
                    {oficio_borrador}
                    """
                    
                    respuesta_final = model.generate_content(prompt_revision)
                    oficio_revisado = respuesta_final.text.replace("**", "").replace("*", "").replace("#", "")
                    
                    st.session_state['oficio'] = oficio_revisado
                    st.session_state['resumen'] = resumen_hablado
                    
                    status.update(label="✅ ¡Documento verificado y listo!", state="complete", expanded=False)
                else:
                    status.update(label="❌ Error al procesar el audio.", state="error")
                    st.error("No se pudo procesar correctamente. Pida ayuda.")
                    
            except Exception as e:
                status.update(label="❌ Ocurrió un error.", state="error")
                st.error("❌ Ocurrió un error. Presione el botón de ayuda.")
            finally:
                for ruta in archivos_temporales:
                    if os.path.exists(ruta): os.remove(ruta)
        
        # Recargar para mostrar resultados
        if 'oficio' in st.session_state:
            st.rerun()

# --- MOSTRAR RESULTADOS Y REPRODUCIR VOZ ---
if 'oficio' in st.session_state:
    st.success("✅ ¡DOCUMENTO LISTO!")
    
    # Hacer que la aplicación hable (lee el resumen)
    reproducir_audio(st.session_state['resumen'])
    st.info(f"🔊 La computadora dice: *{st.session_state['resumen']}*")
    
    # --- ZONA DE BOTONES DE SALIDA ---
    col_descarga, col_whats = st.columns(2)
    
    with col_descarga:
        word_bytes = crear_word(st.session_state['oficio'])
        st.download_button("🖨️ DESCARGAR EN WORD", data=word_bytes, file_name="Documento_Ciudadano.docx", type="primary", use_container_width=True)
    
    with col_whats:
        # Preparamos el texto para que WhatsApp lo entienda
        mensaje_amigable = f"Hola, necesito ayuda para imprimir este documento oficial:\n\n{st.session_state['oficio']}"
        mensaje_codificado = urllib.parse.quote(mensaje_amigable)
        link_whatsapp = f"https://api.whatsapp.com/send?text={mensaje_codificado}"
        
        # Botón que abre WhatsApp directamente
        st.link_button("📲 ENVIAR POR WHATSAPP", url=link_whatsapp, use_container_width=True)
    
    with st.expander("👀 Ver el documento escrito"):
        st.text_area("Oficio:", value=st.session_state['oficio'], height=300)

    if st.button("🗑️ EMPEZAR DE NUEVO", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 7. AVISOS LEGALES Y DE PRIVACIDAD ---
st.write("---")
st.markdown("<h5 style='text-align: center; color: #6c757d;'>Información Legal y Transparencia</h5>", unsafe_allow_html=True)

with st.expander("⚖️ AVISO LEGAL Y LÍMITES DE RESPONSABILIDAD (LEER ANTES DE USAR)"):
    st.markdown("""
    **1. No es Asesoría Legal Humana:** "Escudo Ciudadano" es una herramienta tecnológica experimental impulsada por Inteligencia Artificial (IA). No sustituye el consejo, la representación, ni la revisión de un abogado titulado con Cédula Profesional.
    
    **2. Limitaciones de la Tecnología:** La Inteligencia Artificial puede cometer errores, citar artículos derogados, o interpretar incorrectamente el contexto o la traducción de lenguas originarias (alucinaciones de IA).
    
    **3. Responsabilidad del Usuario:** El documento generado es un "borrador" o "formato sugerido". Es responsabilidad absoluta y exclusiva del usuario o del asesor que lo acompaña leer, verificar, corregir y validar el contenido, los fundamentos legales y sus datos personales antes de firmarlo o presentarlo ante cualquier autoridad.
    
    **4. Deslinde de Responsabilidad:** El creador de este software y la plataforma de alojamiento no asumen ninguna responsabilidad legal, civil, penal o administrativa por el resultado de los trámites, rechazos de autoridades, daños, o perjuicios derivados del uso de los textos generados por este sistema.
    """)

with st.expander("🔒 AVISO DE PRIVACIDAD SIMPLIFICADO"):
    st.markdown("""
    De conformidad con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP), se informa lo siguiente:
    
    **1. Identidad del Responsable:** El proyecto independiente "Escudo Ciudadano" (desarrollado por Juan Manuel Villegas) es el responsable del tratamiento temporal de los datos recabados en este sitio.
    
    **2. Datos Recabados y Finalidad:** Los datos proporcionados mediante voz (audio) se utilizarán **exclusivamente** para redactar y estructurar el documento legal solicitado en tiempo real.
    
    **3. Almacenamiento y Borrado:** Esta plataforma NO almacena sus datos en bases de datos permanentes. La información y audios existen únicamente durante su sesión activa (memoria caché) y se eliminan irreversiblemente al presionar el botón "Empezar de Nuevo" o al cerrar el navegador.
    
    **4. Transferencia de Datos:** Para poder funcionar, los audios se procesan de manera cifrada a través de las interfaces de programación (APIs) de Google y Streamlit. Al usar esta plataforma, usted consiente este procesamiento automatizado de terceros para la generación de su documento.
    """)

st.caption("© 2026 Escudo Ciudadano v2.0 (Kiosco Parlante) | Desarrollado para el Acceso a la Justicia Social en México.")
