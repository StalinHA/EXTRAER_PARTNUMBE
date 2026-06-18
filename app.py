import streamlit as st
import pandas as pd
import zipfile
import json
import re
from io import BytesIO
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
import pickle

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Dashboard de Fichas Técnicas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #3B82F6;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #4B5563;
    }
    .info-box {
        padding: 1rem;
        background-color: #DBEAFE;
        border-radius: 0.5rem;
        border-left: 5px solid #3B82F6;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        background-color: #D1FAE5;
        border-radius: 0.5rem;
        border-left: 5px solid #10B981;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #FEF3C7;
        border-radius: 0.5rem;
        border-left: 5px solid #F59E0B;
        margin: 1rem 0;
    }
    .danger-box {
        padding: 1rem;
        background-color: #FEE2E2;
        border-radius: 0.5rem;
        border-left: 5px solid #EF4444;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- DICCIONARIOS ---
CATEGORIAS_OFICIALES = {
    '11743': 'COMPUTADORA PORTATIL',
    '11744': 'ESTACION DE TRABAJO PORTATIL',
    '11745': 'TABLETA',
    '11738': 'ESCANER DE DOCUMENTOS',
    '11735': 'COMPUTADORA DE ESCRITORIO',
    '11736': 'COMPUTADORA TODO EN UNO',
    '11740': 'ESTACION DE TRABAJO',
    '11741': 'MONITOR',
    '11742': 'PANTALLA PUBLICITARIA',
    '11747': 'DISPOSITIVOS DE ALMACENAMIENTO EXTERNO',
    '11749': 'PANTALLA INTERACTIVA',
    '11751': 'DISPOSITIVOS DE ALMACENAMIENTO INTERNO'
}

MARCAS_COMPLETAS = [
    'TRIUMPH BOARD', 'VASTEC', 'RHINOBOX', 'LENOVO', 'EXIN', 'M4X', 'KENYA TECHNOLOGY',
    'HP', 'MADI-TEK', 'INVESTMENT & BUSINESS SMART SBI', 'ADVANCE', 'QUI-TECH', 'TEXCOPER',
    'WIDETEK', 'IQTOUCH', 'LG', 'ONESCREEN', 'HUAWEI', 'INOTEC', 'DELL', 'I3', 'ASUS',
    'QUAMTU', 'KODAK', 'RICOH', 'SHARP', 'CIBER', 'HAO TECH', 'BROTHER', 'VIEWSONIC',
    'AVISION', 'SAMSUNG', 'ALLWIYA', 'GAMEMAX', 'DYNABOOK', 'HIPPOBOX', 'CONTEX', 'INNEX',
    'CTOUCH', 'HIKVISION', 'ZKT ECO', 'YEALINK', 'TEROS', 'SILVER VOLT', 'QOSOFT',
    'MIMIO', 'HAITECH', 'OPTOMA TECHNOLOGY INC', 'GROWTH HACK', 'MSI', 'XEROX', 'QOMO',
    'EPSON', 'CLEVERTOUCH', 'I2S INNOVATIVE IMAGING SOLUTIONS', 'IQ BOARD', 'GCS', 'COLORTRAC',
    'CANON', 'BOOKEYE', 'JFA TECHNOLOGY', 'AMC', 'MAXTIC', 'SANDISK', 'KINGSTON', 'ADATA',
    'NEW KRAL', 'TLC'
]

# --- ARCHIVOS PARA GUARDAR DATOS PERSONALIZADOS ---
EXCEPCIONES_FILE = "excepciones_part_numbers.pkl"
MARCAS_PERSONALIZADAS_FILE = "marcas_personalizadas.pkl"
CATEGORIAS_PERSONALIZADAS_FILE = "categorias_personalizadas.pkl"

def cargar_excepciones():
    try:
        if os.path.exists(EXCEPCIONES_FILE):
            with open(EXCEPCIONES_FILE, 'rb') as f:
                return pickle.load(f)
    except:
        pass
    return {}

def guardar_excepciones(excepciones):
    try:
        with open(EXCEPCIONES_FILE, 'wb') as f:
            pickle.dump(excepciones, f)
        return True
    except:
        return False

def cargar_marcas_personalizadas():
    try:
        if os.path.exists(MARCAS_PERSONALIZADAS_FILE):
            with open(MARCAS_PERSONALIZADAS_FILE, 'rb') as f:
                return pickle.load(f)
    except:
        pass
    return []

def guardar_marcas_personalizadas(marcas):
    try:
        with open(MARCAS_PERSONALIZADAS_FILE, 'wb') as f:
            pickle.dump(marcas, f)
        return True
    except:
        return False

def cargar_categorias_personalizadas():
    try:
        if os.path.exists(CATEGORIAS_PERSONALIZADAS_FILE):
            with open(CATEGORIAS_PERSONALIZADAS_FILE, 'rb') as f:
                return pickle.load(f)
    except:
        pass
    return []

def guardar_categorias_personalizadas(categorias):
    try:
        with open(CATEGORIAS_PERSONALIZADAS_FILE, 'wb') as f:
            pickle.dump(categorias, f)
        return True
    except:
        return False

# --- FUNCIONES DE EXTRACCIÓN ---
def extract_part_number_con_excepciones(descripcion, excepciones):
    if not descripcion or not isinstance(descripcion, str):
        return "No especificado"
    
    desc_upper = descripcion.upper()
    
    for patron, part_number in excepciones.items():
        if patron.upper() in desc_upper:
            return part_number
    
    return extract_part_number_normal(descripcion)

def extract_part_number_normal(descripcion):
    if not descripcion or not isinstance(descripcion, str):
        return "No especificado"
    
    desc_clean = descripcion.replace('&#160;', ' ').replace('&quot;', '"').replace('&#209;', 'Ñ')
    desc_upper = desc_clean.upper()
    
    PALABRAS_PROHIBIDAS = {
        'PROCESADOR', 'COMPUTADORA', 'PANTALLA', 'ALMACENAMIENTO', 'TECLADO', 'MOUSE', 
        'MONITOR', 'TABLETA', 'MEMORIA', 'DISCO', 'INTEL', 'CORE', 'ULTRA', 'DDR', 
        'SSD', 'LCD', 'LED', 'WLAN', 'BLUETOOTH', 'HDMI', 'VGA', 'WINDOWS', 'ANDROID', 
        'BATERIA', 'PESO', 'CAMARA', 'RAEE', 'COLECTIVO', 'GARANTIA', 'MESES', 'SIST',
        'OPER', 'DOWNGRADE', 'OPTICA', 'OFIMATICA', 'MANEJO', 'RETROILUMINACION', 
        'PIXELES', 'UNIDAD', 'GENERACION', 'NEGRO', 'BLANCO', 'PLATA', 'GRIS', 
        'NVIDIA', 'AMD', 'ETHERNET', 'THUNDERBOLT', 'USB', 'TACTIL', 'WUXGA', 'FHD',
        'LI-ION', 'LI-PO', 'ON-SITE', 'CARRY-IN', 'PRE-INSTALADA', 'GRAFITO',
        'HOME', 'BUSINESS', 'MICROSOFT', 'OFFICE', 'INSTALADA', 'INSTALADO',
        'VASTEC', 'VIEWSONIC', 'LENOVO', 'SAMSUNG', 'HP', 'DELL', 'ASUS', 'ACER',
        'TOSHIBA', 'SONY', 'PANASONIC', 'NEC', 'FUJITSU', 'IBM', 'COMPAQ',
        'CROSSTEK', 'FORESTER', 'FORESTERG2',
        'STATION', 'PRO', 'RL', 'MULTIV', 'THINKPAD', 'GALAXY', 'TAB', 'LITE',
        'SERIES', 'INCH', 'MONITOR', 'PORTATIL', 'ESCRITORIO', 'TODO', 'UNO',
        'ESTACION', 'TRABAJO', 'PUBLICITARIA', 'INTERACTIVA', 'EXTERNO', 'INTERNO',
        'INCLUIDO', 'ENTERPRISE', 'JELLYFISH', 'COMMANDER', 'CROSSTEK',
        'FORESTER', 'FORESTERG2', 'PREINSTALADA',
        '1920X1200', '1920X1080', '2560X1440', '2560X1080', '2880X1800',
        '1366X768', '3840X2160', '3440X1440', '2560X1600', '2048X1536',
        '1600X900', '1280X800', '1024X768', '800X600'
    }
    
    patrones_part_number = [
        # Patrón para 9GTRS9ZTQ500HP
        r'\b([0-9][A-Z]{2,}[0-9][A-Z]{2,}[0-9]{3,}[A-Z]{2})\b',
        
        # Con #: DX5R4LS#ABM
        r'\b([A-Z0-9]+#[A-Z0-9]+)\b',
        
        # RG24FIM6C, RG27FIM6C, etc.
        r'\b(R[GM][0-9]{2}[A-Z]{3,}[0-9][A-Z])\b',
        r'\b(R[PG][0-9]{2,3}[A-Z]{3,}[0-9][A-Z])\b',
        r'\b(R[PG][0-9]{2,3}[A-Z]{2,}[0-9][A-Z])\b',
        
        # LENOVO
        r'\b([A-Z][0-9][A-Z0-9]{5,}[0-9]{3,}[A-Z]?)\b',
        r'\b([A-Z][0-9]{2}[A-Z][0-9][A-Z][0-9]{8,}[A-Z]-[A-Z]{2})\b',
        
        # SAMSUNG
        r'\b(SM-[A-Z0-9]{7,})\b',
        
        # VASTEC
        r'\b([0-9][A-Z]{2,}[0-9]{3,}[A-Z0-9]*)\b',
        r'\b([0-9][A-Z]{2,}[A-Z0-9]{4,})\b',
        
        # HP (incluye 6FW09A-G3)
        r'\b([A-Z][0-9][A-Z]{2,}[0-9]{2,})\b',
        r'\b([A-Z0-9]{4,}-[A-Z0-9]{2})\b',
        
        # MDL/MDP
        r'\b(MD[LP][0-9]{4}[A-Z0-9]{6,})\b',
        
        # PCAD
        r'\b(PCAD3VP[0-9]{4}[A-Z]{2,}[A-Z]{2})\b',
        
        # ALL
        r'\b(ALL[0-9]{2}[A-Z]{3,}[A-Z0-9]{5,})\b',
        
        # N50SG6U7161, M70SG6U743162000H
        r'\b([A-Z][0-9]{2}[A-Z]{2}[A-Z][0-9]{4,})\b',
        
        # AB3S6LS, A95B6LSABM-SD
        r'\b([A-Z]{2,}[0-9][A-Z]{2,}[0-9]{2,}[A-Z]*(?:-[A-Z]{2})?)\b',
        
        # 90PF04U1
        r'\b([0-9]{2}[A-Z]{2}[0-9]{2}[A-Z][0-9])\b',
        
        # Patrón general: 8+ caracteres alfanuméricos
        r'\b([A-Z0-9]{8,}(?:-[A-Z0-9]+)?)\b',
    ]
    
    def es_part_number_valido(texto):
        if not texto or len(texto) < 5:
            return False
        
        texto_limpio = re.sub(r'[^A-Za-z0-9]', '', texto)
        
        if texto_limpio.upper() in PALABRAS_PROHIBIDAS:
            return False
        if texto.upper() in PALABRAS_PROHIBIDAS:
            return False
        
        if any(res in texto for res in ['1920X1200', '1920X1080', '2560X1440', '2560X1080', '2880X1800']):
            return False
        
        if any(p in texto.upper() for p in ['DDR', 'HDMI', 'VGA', 'USB', 'LAN']):
            return False
        
        if any(m in texto.upper() for m in ['VASTEC', 'VIEWSONIC', 'LENOVO', 'SAMSUNG', 'HP']):
            return False
        
        if any(p in texto.upper() for p in ['INCLUIDO', 'ENTERPRISE', 'JELLYFISH', 'COMMANDER', 'FORESTER']):
            return False
        
        if not re.search(r'[A-Z]', texto) or not re.search(r'[0-9]', texto):
            return False
        
        return True
    
    if 'UNIDAD' in desc_upper:
        partes = desc_upper.split('UNIDAD')
        if len(partes) > 1:
            after_unidad = partes[1].strip()
            for patron in patrones_part_number:
                matches = re.findall(patron, after_unidad)
                for match in matches:
                    if es_part_number_valido(match.strip()):
                        return match.strip()
    
    for patron in patrones_part_number:
        matches = re.findall(patron, desc_clean)
        for match in matches:
            if es_part_number_valido(match.strip()):
                return match.strip()
    
    palabras = desc_clean.split()
    for i in range(len(palabras) - 1, -1, -1):
        palabra = palabras[i].strip()
        palabra_limpia = re.sub(r'[^A-Za-z0-9#\-]', '', palabra)
        if es_part_number_valido(palabra_limpia):
            return palabra_limpia
    
    patron_especifico = r'\b([A-Z]{2,}[0-9]{3,}[A-Z0-9]{2,})\b'
    matches = re.findall(patron_especifico, desc_clean)
    for match in matches:
        if es_part_number_valido(match):
            return match
    
    codigos_largos = re.findall(r'\b([A-Z0-9]{8,})\b', desc_clean)
    for codigo in codigos_largos:
        if es_part_number_valido(codigo):
            return codigo
    
    return "No especificado"

def extract_category(descripcion, categorias_personalizadas):
    if not descripcion:
        return "OTROS"
    
    desc_lower = descripcion.lower()
    desc_upper = descripcion.upper()
    
    for categoria in categorias_personalizadas:
        if categoria.upper() in desc_upper:
            return categoria.upper()
    
    for codigo, categoria in CATEGORIAS_OFICIALES.items():
        if categoria.lower() in desc_lower:
            return categoria
    
    if 'ESCANER' in desc_upper or 'ESCANNER' in desc_upper:
        return 'ESCANER DE DOCUMENTOS'
    
    return "OTROS"

def extract_brand(descripcion, marcas_completas, marcas_personalizadas):
    if not descripcion:
        return "OTROS"
    
    desc_upper = descripcion.upper()
    
    for marca in marcas_personalizadas:
        if marca.upper() in desc_upper:
            return marca.upper()
    
    for marca in marcas_completas:
        if marca.upper() in desc_upper:
            return marca
    return "OTROS"

# --- FUNCIONES DE CARGA ---
def get_all_zip_files_from_github(repo_url):
    try:
        api_url = repo_url.replace('github.com', 'api.github.com/repos')
        if not api_url.endswith('/contents'):
            api_url = api_url.rstrip('/') + '/contents'
        
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        
        contents = response.json()
        zip_files = []
        
        for item in contents:
            if item.get('name', '').endswith('.zip'):
                zip_files.append({
                    'name': item['name'],
                    'download_url': item['download_url'],
                    'size': item.get('size', 0)
                })
        
        return zip_files
    
    except Exception as e:
        st.error(f"Error al obtener archivos: {str(e)}")
        return []

def process_zip_file(zip_url, zip_name, progress_bar, status_text, excepciones, marcas_personalizadas, categorias_personalizadas):
    productos = []
    part_numbers_vistos = set()
    
    try:
        status_text.text(f"📥 Descargando: {zip_name}")
        response = requests.get(zip_url)
        response.raise_for_status()
        
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            json_files = [f for f in z.namelist() if f.endswith('.json')]
            
            if not json_files:
                status_text.text(f"⚠️ No se encontraron JSON en {zip_name}")
                return productos
            
            total_json = len(json_files)
            for idx, json_file in enumerate(json_files):
                status_text.text(f"📄 Procesando {json_file} ({idx+1}/{total_json}) en {zip_name}")
                
                try:
                    with z.open(json_file) as f:
                        data = json.load(f)
                    
                    items = []
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, list):
                                items.extend(value)
                            elif isinstance(value, dict):
                                items.append(value)
                    elif isinstance(data, list):
                        items = data
                    
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        
                        # ============================================
                        # FILTRO CORREGIDO: Usar fecha_adjudicacion
                        # ============================================
                        fecha_adjudicacion = item.get('fecha_adjudicacion', '')
                        estado_ficha = item.get('estado_ficha', '')
                        estado_oferta = item.get('estado_oferta', '')
                        
                        # FILTRO: fecha_adjudicacion en Junio 2026
                        if '06/2026' not in fecha_adjudicacion and '2026-06' not in fecha_adjudicacion:
                            continue
                        
                        # FILTRO: OFERTADA + VIGENTE
                        if estado_ficha != "OFERTADA" or estado_oferta != "VIGENTE":
                            continue
                        
                        descripcion = item.get('descripcion', '')
                        part_number = extract_part_number_con_excepciones(descripcion, excepciones)
                        
                        # Evitar duplicados por Part Number
                        if part_number in part_numbers_vistos:
                            continue
                        part_numbers_vistos.add(part_number)
                        
                        categoria = extract_category(descripcion, categorias_personalizadas)
                        marca = extract_brand(descripcion, MARCAS_COMPLETAS, marcas_personalizadas)
                        
                        producto = {
                            'ID_ProductoOfertado': item.get('ID_ProductoOfertado', ''),
                            'Part_Number': part_number,
                            'Categoria': categoria,
                            'Marca': marca,
                            'Descripcion': descripcion,
                            'Moneda': item.get('moneda', ''),
                            'Precio': float(item.get('precio', 0)),
                            'Fecha_Registro': item.get('fecha_registro', ''),
                            'Estado_Ficha': estado_ficha,
                            'Estado_Oferta': estado_oferta,
                            'Fecha_Adjudicacion': fecha_adjudicacion,
                            'Fecha_Publicacion': item.get('fecha_publicacion', ''),
                            'Motivo': item.get('motivo', ''),
                            'Justificacion': item.get('justificacion', ''),
                            'Puntaje': float(item.get('puntaje', 0)),
                            'Archivo_Origen': zip_name,
                            'JSON_Origen': json_file
                        }
                        productos.append(producto)
                        
                except Exception as e:
                    st.warning(f"⚠️ Error en {json_file}: {str(e)}")
                    continue
                
                progress = (idx + 1) / total_json
                progress_bar.progress(progress)
        
        status_text.text(f"✅ Procesado: {zip_name} - {len(productos)} productos únicos")
        
    except Exception as e:
        st.error(f"❌ Error al procesar {zip_name}: {str(e)}")
    
    return productos

def load_all_data_from_repo(repo_url, excepciones, marcas_personalizadas, categorias_personalizadas):
    all_productos = []
    
    zip_files = get_all_zip_files_from_github(repo_url)
    
    if not zip_files:
        st.error("No se encontraron archivos ZIP.")
        return None
    
    st.info(f"📦 Se encontraron {len(zip_files)} archivos ZIP")
    
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_zips = len(zip_files)
        for idx, zip_info in enumerate(zip_files):
            status_text.text(f"🔄 Procesando ZIP {idx+1}/{total_zips}: {zip_info['name']}")
            
            productos = process_zip_file(
                zip_info['download_url'],
                zip_info['name'],
                progress_bar,
                status_text,
                excepciones,
                marcas_personalizadas,
                categorias_personalizadas
            )
            
            all_productos.extend(productos)
            
            overall_progress = (idx + 1) / total_zips
            progress_bar.progress(overall_progress)
    
    status_text.text("✅ ¡Todos los archivos procesados!")
    
    if all_productos:
        return pd.DataFrame(all_productos)
    else:
        return None

def create_excel_report(df):
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Datos_Filtrados', index=False)
        
        resumen = pd.DataFrame({
            'Métrica': ['Total de Fichas Únicas', 'Categorías', 'Marcas', 'Precio Promedio', 'Puntaje Promedio', 'ZIP Procesados'],
            'Valor': [
                len(df),
                df['Categoria'].nunique(),
                df['Marca'].nunique(),
                f"${df['Precio'].mean():,.2f}",
                f"{df['Puntaje'].mean():.2f}",
                df['Archivo_Origen'].nunique()
            ]
        })
        resumen.to_excel(writer, sheet_name='Resumen', index=False)
        
        categoria_counts = df['Categoria'].value_counts().reset_index()
        categoria_counts.columns = ['Categoria', 'Cantidad']
        categoria_counts.to_excel(writer, sheet_name='Dist_Categoria', index=False)
        
        marca_counts = df['Marca'].value_counts().reset_index()
        marca_counts.columns = ['Marca', 'Cantidad']
        marca_counts.to_excel(writer, sheet_name='Dist_Marca', index=False)
    
    output.seek(0)
    return output

# --- INTERFAZ PRINCIPAL ---
def main():
    st.markdown('<h1 class="main-header">📊 Dashboard de Fichas Técnicas - Junio 2026</h1>', unsafe_allow_html=True)
    
    repo_url = "https://github.com/StalinHA/EXTRAER_PARTNUMBE"
    
    excepciones = cargar_excepciones()
    marcas_personalizadas = cargar_marcas_personalizadas()
    categorias_personalizadas = cargar_categorias_personalizadas()
    
    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("🔄 Recargar Datos", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with st.sidebar.expander("⚙️ Gestionar Marcas y Categorías", expanded=True):
        st.markdown("### 🏷️ Marcas Personalizadas")
        
        if marcas_personalizadas:
            st.write(f"Marcas actuales: {', '.join(marcas_personalizadas)}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            nueva_marca = st.text_input("Nueva marca:", placeholder="Ej: MIMIO", key="nueva_marca")
        with col2:
            if st.button("➕ Agregar Marca", use_container_width=True):
                if nueva_marca and nueva_marca.upper() not in [m.upper() for m in marcas_personalizadas]:
                    marcas_personalizadas.append(nueva_marca.upper())
                    if guardar_marcas_personalizadas(marcas_personalizadas):
                        st.success(f"✅ Marca '{nueva_marca.upper()}' agregada")
                        st.rerun()
                else:
                    st.warning("⚠️ Marca ya existe o está vacía")
        
        if marcas_personalizadas:
            marca_eliminar = st.selectbox("Seleccionar marca para eliminar:", marcas_personalizadas)
            if st.button("🗑️ Eliminar Marca", type="secondary"):
                marcas_personalizadas.remove(marca_eliminar)
                if guardar_marcas_personalizadas(marcas_personalizadas):
                    st.success(f"✅ Marca '{marca_eliminar}' eliminada")
                    st.rerun()
        
        st.divider()
        
        st.markdown("### 📂 Categorías Personalizadas")
        
        if categorias_personalizadas:
            st.write(f"Categorías actuales: {', '.join(categorias_personalizadas)}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            nueva_categoria = st.text_input("Nueva categoría:", placeholder="Ej: ESCANER DE DOCUMENTOS", key="nueva_categoria")
        with col2:
            if st.button("➕ Agregar Categoría", use_container_width=True):
                if nueva_categoria and nueva_categoria.upper() not in [c.upper() for c in categorias_personalizadas]:
                    categorias_personalizadas.append(nueva_categoria.upper())
                    if guardar_categorias_personalizadas(categorias_personalizadas):
                        st.success(f"✅ Categoría '{nueva_categoria.upper()}' agregada")
                        st.rerun()
                else:
                    st.warning("⚠️ Categoría ya existe o está vacía")
        
        if categorias_personalizadas:
            categoria_eliminar = st.selectbox("Seleccionar categoría para eliminar:", categorias_personalizadas)
            if st.button("🗑️ Eliminar Categoría", type="secondary"):
                categorias_personalizadas.remove(categoria_eliminar)
                if guardar_categorias_personalizadas(categorias_personalizadas):
                    st.success(f"✅ Categoría '{categoria_eliminar}' eliminada")
                    st.rerun()
    
    st.markdown('<div class="info-box">📦 Procesando todos los archivos ZIP del repositorio...</div>', unsafe_allow_html=True)
    
    with st.spinner('🔄 Descargando y procesando todos los archivos...'):
        df = load_all_data_from_repo(repo_url, excepciones, marcas_personalizadas, categorias_personalizadas)
    
    if df is None or len(df) == 0:
        st.warning("⚠️ No se encontraron fichas que cumplan los criterios.")
        st.info("💡 Verifica que el repositorio contenga datos con las condiciones especificadas.")
        return
    
    categorias_encontradas = sorted(df['Categoria'].unique())
    st.markdown(f"""
    <div class="info-box">
        📊 Categorías encontradas: <b>{', '.join(categorias_encontradas)}</b>
        <br>📌 Total de fichas únicas: <b>{len(df):,}</b>
    </div>
    """, unsafe_allow_html=True)
    
    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    
    estados = sorted(df['Estado_Ficha'].unique())
    estados_filter = st.sidebar.multiselect("Estado de Ficha", options=estados, default=estados)
    
    todas_categorias = sorted(df['Categoria'].unique())
    categorias_filter = st.sidebar.multiselect(
        "Categoría",
        options=todas_categorias,
        default=todas_categorias
    )
    
    todas_marcas = sorted(df['Marca'].unique())
    marcas_filter = st.sidebar.multiselect(
        "Marca",
        options=todas_marcas,
        default=todas_marcas
    )
    
    min_price = float(df['Precio'].min())
    max_price = float(df['Precio'].max())
    price_range = st.sidebar.slider(
        "Rango de Precio (USD)",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=10.0,
        format="%.2f"
    )
    
    df_filtered = df[
        (df['Estado_Ficha'].isin(estados_filter)) &
        (df['Categoria'].isin(categorias_filter)) &
        (df['Marca'].isin(marcas_filter)) &
        (df['Precio'] >= price_range[0]) &
        (df['Precio'] <= price_range[1])
    ]
    
    # --- MÉTRICAS ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(df_filtered):,}</div>
            <div class="metric-label">Total de Fichas Únicas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{df_filtered['Categoria'].nunique()}</div>
            <div class="metric-label">Categorías</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{df_filtered['Marca'].nunique()}</div>
            <div class="metric-label">Marcas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">${df_filtered['Precio'].mean():,.2f}</div>
            <div class="metric-label">Precio Promedio</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{df_filtered['Archivo_Origen'].nunique()}</div>
            <div class="metric-label">ZIP Procesados</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # --- ESTADÍSTICAS DE PART NUMBERS ---
    col1, col2, col3 = st.columns(3)
    
    total_fichas = len(df_filtered)
    part_numbers_validos = len(df_filtered[df_filtered['Part_Number'] != 'No especificado'])
    part_numbers_invalidos = total_fichas - part_numbers_validos
    porcentaje_valido = (part_numbers_validos / total_fichas * 100) if total_fichas > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #10B981;">
            <div class="metric-value" style="color: #10B981;">{part_numbers_validos}</div>
            <div class="metric-label">✅ Part Numbers Válidos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #EF4444;">
            <div class="metric-value" style="color: #EF4444;">{part_numbers_invalidos}</div>
            <div class="metric-label">❌ No Detectados</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #3B82F6;">
            <div class="metric-value" style="color: #3B82F6;">{porcentaje_valido:.1f}%</div>
            <div class="metric-label">🎯 Tasa de Detección</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # --- CORREGIR NÚMEROS DE PARTE ---
    st.subheader("✏️ Corregir Números de Parte Manualmente")
    
    no_detectados = df_filtered[df_filtered['Part_Number'] == 'No especificado']
    
    if len(no_detectados) > 0:
        st.markdown(f"""
        <div class="danger-box">
            ⚠️ <b>{len(no_detectados)} productos</b> no tienen número de parte detectado.
        </div>
        """, unsafe_allow_html=True)
        
        opciones = no_detectados['ID_ProductoOfertado'].tolist()
        opciones_con_desc = [f"{id_} - {df_filtered[df_filtered['ID_ProductoOfertado']==id_]['Marca'].iloc[0]} - {df_filtered[df_filtered['ID_ProductoOfertado']==id_]['Categoria'].iloc[0]}" for id_ in opciones]
        
        if opciones:
            selected_idx = st.selectbox(
                "Selecciona un producto para corregir:",
                range(len(opciones_con_desc)),
                format_func=lambda x: opciones_con_desc[x][:100] + "..." if len(opciones_con_desc[x]) > 100 else opciones_con_desc[x]
            )
            
            selected_id = opciones[selected_idx]
            producto_seleccionado = df_filtered[df_filtered['ID_ProductoOfertado'] == selected_id].iloc[0]
            
            st.markdown("### 📄 Descripción COMPLETA del producto:")
            st.text_area(
                "Descripción (completa):",
                value=producto_seleccionado['Descripcion'],
                height=200,
                disabled=True,
                key="desc_completa"
            )
            
            st.info(f"📌 Categoría actual: **{producto_seleccionado['Categoria']}** | Marca actual: **{producto_seleccionado['Marca']}**")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                part_number_correcto = st.text_input(
                    "✏️ Ingresa el número de parte correcto:",
                    placeholder="Ejemplo: 6FW09A-G3",
                    key="part_number_manual"
                )
            
            with col2:
                if st.button("💾 Guardar Corrección", type="primary", use_container_width=True):
                    if part_number_correcto and len(part_number_correcto) >= 4:
                        palabras_clave = producto_seleccionado['Descripcion'].split()[:10]
                        patron_busqueda = " ".join(palabras_clave[:5])
                        
                        excepciones[patron_busqueda] = part_number_correcto
                        
                        if guardar_excepciones(excepciones):
                            st.success(f"✅ ¡Corrección guardada! '{part_number_correcto}'")
                            st.info("🔄 Recargando para aplicar cambios...")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar la corrección.")
                    else:
                        st.warning("⚠️ Ingresa un número de parte válido (mínimo 4 caracteres).")
    
    else:
        st.markdown("""
        <div class="success-box">
            ✅ ¡Todos los productos tienen número de parte detectado!
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # --- GRÁFICOS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribución por Categoría")
        if not df_filtered.empty:
            fig = px.pie(df_filtered, names='Categoria', title='Fichas por Categoría', hole=0.3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Top 10 Marcas")
        if not df_filtered.empty:
            top_brands = df_filtered['Marca'].value_counts().head(10).reset_index()
            top_brands.columns = ['Marca', 'Cantidad']
            fig = px.bar(top_brands, x='Marca', y='Cantidad', 
                        title='Top 10 Marcas', color='Cantidad',
                        color_continuous_scale='Blues', text='Cantidad')
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    # --- TABLA DE DATOS ---
    st.subheader("📋 Datos Detallados")
    st.caption(f"Mostrando {len(df_filtered):,} fichas únicas")
    
    display_cols = ['ID_ProductoOfertado', 'Part_Number', 'Categoria', 'Marca',
                    'Precio', 'Puntaje', 'Estado_Ficha', 'Estado_Oferta', 
                    'Fecha_Adjudicacion', 'Archivo_Origen']
    
    st.dataframe(
        df_filtered[display_cols],
        column_config={
            "ID_ProductoOfertado": st.column_config.TextColumn("ID Producto"),
            "Part_Number": st.column_config.TextColumn("Part Number"),
            "Categoria": st.column_config.TextColumn("Categoría"),
            "Marca": st.column_config.TextColumn("Marca"),
            "Precio": st.column_config.NumberColumn("Precio (USD)", format="$%.2f"),
            "Puntaje": st.column_config.NumberColumn("Puntaje", format="%.2f"),
            "Estado_Ficha": st.column_config.TextColumn("Estado Ficha"),
            "Estado_Oferta": st.column_config.TextColumn("Estado Oferta"),
            "Fecha_Adjudicacion": st.column_config.TextColumn("Fecha Adjudicación"),
            "Archivo_Origen": st.column_config.TextColumn("Archivo ZIP"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # --- EXPORTAR ---
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📥 Exportar Dashboard a Excel", use_container_width=True, type="primary"):
            with st.spinner("Generando archivo Excel..."):
                excel_data = create_excel_report(df_filtered)
                st.download_button(
                    label="📥 Descargar Excel",
                    data=excel_data,
                    file_name=f"dashboard_fichas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ Excel generado!")
    
    st.divider()
    st.caption(f"📊 Dashboard generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    main()
