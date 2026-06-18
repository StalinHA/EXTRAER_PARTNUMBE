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
    .part-number-highlight {
        background-color: #FEF3C7;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
        font-family: monospace;
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

# --- FUNCIÓN DEFINITIVA PARA NÚMEROS DE PARTE ---
def extract_part_number(descripcion):
    """
    Función ULTRA-OPTIMIZADA para extraer números de parte.
    Analiza 100+ patrones y filtros para identificar SOLO números de parte.
    """
    if not descripcion or not isinstance(descripcion, str):
        return "No especificado"
    
    # Limpiar descripción
    desc_clean = descripcion.replace('&#160;', ' ').replace('&quot;', '"').replace('&#209;', 'Ñ')
    desc_upper = desc_clean.upper()
    
    # ============================================
    # 1. LISTA NEGRA DE PALABRAS COMUNES (NUNCA SON PART NUMBERS)
    # ============================================
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
        'STATION', 'PRO', 'RL', 'MULTIV', 'THINKPAD', 'GALAXY', 'TAB', 'LITE',
        'SERIES', 'INCH', 'MONITOR', 'PORTATIL', 'ESCRITORIO', 'TODO', 'UNO',
        'ESTACION', 'TRABAJO', 'PUBLICITARIA', 'INTERACTIVA', 'EXTERNO', 'INTERNO'
    }
    
    # ============================================
    # 2. PATRONES DE NÚMEROS DE PARTE (ORDENADOS POR ESPECIFICIDAD)
    # ============================================
    patrones_part_number = [
        # LENOVO: L14G5U721162100D (Letra + Número + Letra + Números)
        r'\b([A-Z][0-9][A-Z0-9]{5,}[0-9]{3,}[A-Z]?)\b',
        
        # LENOVO con guión: E16G6U71716201H-OH
        r'\b([A-Z][0-9]{2}[A-Z][0-9][A-Z][0-9]{8,}[A-Z]-[A-Z]{2})\b',
        
        # SAMSUNG: SM-X406BZAAPEO
        r'\b(SM-[A-Z0-9]{7,})\b',
        
        # VASTEC: 7GTRCVA068 (Número + Letras + Número)
        r'\b([0-9][A-Z]{2,}[0-9]{3,})\b',
        
        # HP: B0CG8UT (Letra + Número + Letras + Número)
        r'\b([A-Z][0-9][A-Z]{2,}[0-9]{2,})\b',
        
        # MDL2605M2YWA0 (MDL + números + letras)
        r'\b(MDL[0-9A-Z]{6,})\b',
        
        # BZ2G2LT (Letra + Letra + Número + Letra + Número + Letra)
        r'\b([A-Z]{2}[0-9][A-Z][0-9][A-Z]{2})\b',
        
        # Patrón general: 8+ caracteres alfanuméricos (no comunes)
        r'\b([A-Z0-9]{8,}(?:-[A-Z0-9]+)?)\b',
    ]
    
    # ============================================
    # 3. ESTRATEGIA 1: Buscar después de "UNIDAD"
    # ============================================
    if 'UNIDAD' in desc_upper:
        partes = desc_upper.split('UNIDAD')
        if len(partes) > 1:
            after_unidad = partes[1].strip()
            # Buscar en la parte después de UNIDAD
            for patron in patrones_part_number:
                matches = re.findall(patron, after_unidad)
                for match in matches:
                    match_clean = match.strip()
                    if (len(match_clean) >= 5 and 
                        match_clean not in PALABRAS_PROHIBIDAS and
                        not any(p in match_clean for p in ['DDR', 'HDMI', 'VGA', 'USB', 'LAN']) and
                        not any(marca in match_clean for marca in ['VASTEC', 'VIEWSONIC', 'LENOVO', 'SAMSUNG', 'HP'])):
                        return match_clean
    
    # ============================================
    # 4. ESTRATEGIA 2: Buscar en toda la descripción
    # ============================================
    for patron in patrones_part_number:
        matches = re.findall(patron, desc_clean)
        for match in matches:
            match_clean = match.strip()
            # Validaciones estrictas
            if (len(match_clean) >= 5 and 
                match_clean not in PALABRAS_PROHIBIDAS and
                not any(p in match_clean for p in ['DDR', 'HDMI', 'VGA', 'USB', 'LAN']) and
                not any(marca in match_clean for marca in ['VASTEC', 'VIEWSONIC', 'LENOVO', 'SAMSUNG', 'HP']) and
                not any(palabra in match_clean for palabra in ['INSTALADA', 'UNIDAD', 'PRO', 'RL', 'STATION'])):
                return match_clean
    
    # ============================================
    # 5. ESTRATEGIA 3: Buscar códigos al final de la descripción
    # ============================================
    # Dividir por espacios y buscar al final
    palabras = desc_clean.split()
    for i in range(len(palabras) - 1, -1, -1):
        palabra = palabras[i].strip()
        # Limpiar caracteres especiales
        palabra_limpia = re.sub(r'[^A-Za-z0-9\-]', '', palabra)
        
        if (len(palabra_limpia) >= 5 and 
            palabra_limpia not in PALABRAS_PROHIBIDAS and
            not any(p in palabra_limpia for p in ['DDR', 'HDMI', 'VGA', 'USB', 'LAN']) and
            not any(marca in palabra_limpia for marca in ['VASTEC', 'VIEWSONIC', 'LENOVO', 'SAMSUNG', 'HP'])):
            # Verificar que tenga mayúsculas y números (característica de part number)
            if re.search(r'[A-Z]', palabra_limpia) and re.search(r'[0-9]', palabra_limpia):
                return palabra_limpia
    
    # ============================================
    # 6. ESTRATEGIA 4: Buscar patrones específicos de números de parte
    # ============================================
    # Buscar secuencias que parecen números de parte: Letras+Números+Letras
    patron_especifico = r'\b([A-Z]{2,}[0-9]{3,}[A-Z0-9]{2,})\b'
    matches = re.findall(patron_especifico, desc_clean)
    for match in matches:
        if (len(match) >= 6 and 
            match not in PALABRAS_PROHIBIDAS and
            not any(p in match for p in ['DDR', 'HDMI', 'VGA', 'USB'])):
            return match
    
    # ============================================
    # 7. ESTRATEGIA 5: Último recurso - buscar códigos largos
    # ============================================
    # Buscar cualquier código alfanumérico largo (8+ caracteres)
    codigos_largos = re.findall(r'\b([A-Z0-9]{8,})\b', desc_clean)
    for codigo in codigos_largos:
        if (codigo not in PALABRAS_PROHIBIDAS and
            not any(p in codigo for p in ['DDR', 'HDMI', 'VGA', 'USB']) and
            not any(marca in codigo for marca in ['VASTEC', 'VIEWSONIC', 'LENOVO', 'SAMSUNG'])):
            return codigo
    
    return "No especificado"

def extract_category(descripcion):
    """Extrae la categoría del producto basado en la descripción."""
    desc_lower = descripcion.lower() if descripcion else ""
    for codigo, categoria in CATEGORIAS_OFICIALES.items():
        if categoria.lower() in desc_lower:
            return categoria
    return "OTROS"

def extract_brand(descripcion, marcas_list):
    """Extrae la marca del producto basado en la descripción."""
    desc_upper = descripcion.upper() if descripcion else ""
    for marca in marcas_list:
        if marca.upper() in desc_upper:
            return marca
    return "OTROS"

# --- FUNCIONES DE CARGA ---
def get_all_zip_files_from_github(repo_url):
    """Obtiene todos los archivos ZIP del repositorio."""
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

def process_zip_file(zip_url, zip_name, progress_bar, status_text):
    """Procesa un archivo ZIP y extrae todos los JSON."""
    productos = []
    
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
                        
                        fecha_pub = item.get('fecha_publicacion', '')
                        estado_ficha = item.get('estado_ficha', '')
                        estado_oferta = item.get('estado_oferta', '')
                        
                        # Filtro estricto: Junio 2026 + OFERTADA + VIGENTE
                        if '06/2026' not in fecha_pub and '2026-06' not in fecha_pub:
                            continue
                        
                        if estado_ficha != "OFERTADA" or estado_oferta != "VIGENTE":
                            continue
                        
                        descripcion = item.get('descripcion', '')
                        part_number = extract_part_number(descripcion)
                        categoria = extract_category(descripcion)
                        marca = extract_brand(descripcion, MARCAS_COMPLETAS)
                        
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
                            'Fecha_Adjudicacion': item.get('fecha_adjudicacion', ''),
                            'Fecha_Publicacion': fecha_pub,
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
        
        status_text.text(f"✅ Procesado: {zip_name} - {len(productos)} productos")
        
    except Exception as e:
        st.error(f"❌ Error al procesar {zip_name}: {str(e)}")
    
    return productos

def load_all_data_from_repo(repo_url):
    """Carga y procesa todos los datos de todos los ZIP."""
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
                status_text
            )
            
            all_productos.extend(productos)
            
            overall_progress = (idx + 1) / total_zips
            progress_bar.progress(overall_progress)
    
    status_text.text("✅ ¡Todos los archivos procesados!")
    
    if all_productos:
        return pd.DataFrame(all_productos)
    else:
        return None

# --- FUNCIONES DE EXPORTACIÓN ---
def create_excel_report(df):
    """Crea un archivo Excel con el dashboard."""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Datos_Filtrados', index=False)
        
        resumen = pd.DataFrame({
            'Métrica': ['Total de Fichas', 'Categorías', 'Marcas', 'Precio Promedio', 'Puntaje Promedio', 'ZIP Procesados', 'Part Numbers Válidos'],
            'Valor': [
                len(df),
                df['Categoria'].nunique(),
                df['Marca'].nunique(),
                f"${df['Precio'].mean():,.2f}",
                f"{df['Puntaje'].mean():.2f}",
                df['Archivo_Origen'].nunique(),
                len(df[df['Part_Number'] != 'No especificado'])
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
    
    st.markdown('<div class="info-box">📦 Procesando todos los archivos ZIP del repositorio...</div>', unsafe_allow_html=True)
    
    with st.spinner('🔄 Descargando y procesando todos los archivos...'):
        df = load_all_data_from_repo(repo_url)
    
    if df is None or len(df) == 0:
        st.warning("⚠️ No se encontraron fichas que cumplan los criterios.")
        st.info("💡 Verifica que el repositorio contenga datos con las condiciones especificadas.")
        return
    
    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros")
    
    estados = sorted(df['Estado_Ficha'].unique())
    estados_filter = st.sidebar.multiselect("Estado de Ficha", options=estados, default=estados)
    
    categorias = sorted(df['Categoria'].unique())
    categorias_filter = st.sidebar.multiselect("Categoría", options=categorias, default=categorias)
    
    marcas = sorted(df['Marca'].unique())
    marcas_filter = st.sidebar.multiselect("Marca", options=marcas, default=marcas)
    
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
            <div class="metric-label">Total de Fichas</div>
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
            <div class="metric-label">❌ Part Numbers No Detectados</div>
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
    st.caption(f"Mostrando {len(df_filtered):,} de {len(df):,} fichas")
    
    display_cols = ['ID_ProductoOfertado', 'Part_Number', 'Categoria', 'Marca',
                    'Precio', 'Puntaje', 'Estado_Ficha', 'Estado_Oferta', 
                    'Fecha_Publicacion', 'Archivo_Origen']
    
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
            "Fecha_Publicacion": st.column_config.TextColumn("Fecha Publicación"),
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
