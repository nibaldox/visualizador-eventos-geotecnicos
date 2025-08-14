"""
Visualizador de Eventos Geotécnicos y Alertas de Seguridad
Aplicación principal desarrollada con Streamlit

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import DataLoader
from src.visualizations import (
    create_dashboard_metrics, create_events_timeline, create_events_scatter,
    create_alerts_scatter, create_correlation_analysis, create_dashboard_events_map,
    create_consolidated_scatter, create_3d_map, create_failure_height_analysis,
    create_velocity_analysis
)
from src.utils import format_date, validate_coordinates
from src.dxf_loader import DXFLoader
from src.dxf_visualizations import (
    create_dxf_base_map, create_dxf_with_events_map, 
    create_dxf_layers_summary, create_dxf_statistics_chart
)
from src.stl_loader import STLLoader
from src.stl_visualizations import (
    create_stl_mesh_figure,
    render_stl_metrics,
)

# Configuración de la página
st.set_page_config(
    page_title="Visualizador Eventos Geotécnicos",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """
    Función principal de la aplicación Streamlit
    """
    # Título principal
    st.title("🏔️ Visualizador de Eventos Geotécnicos y Alertas")
    st.markdown("---")
    
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    
    # Inicializar el cargador de datos
    data_loader = DataLoader()
    
    # Carga de datos desde archivos subidos (obligatorio)
    with st.expander("📥 Cargar datos (Eventos y Alertas)", expanded=True):
        colu1, colu2 = st.columns([2,2])
        with colu1:
            eventos_upload = st.file_uploader(
                "Subir archivo de Eventos (Excel/CSV/TXT)",
                type=["xlsx", "xls", "csv", "txt"],
                key="eventos_upload"
            )
        with colu2:
            alertas_upload = st.file_uploader(
                "Subir archivo de Alertas (Excel/CSV/TXT)",
                type=["xlsx", "xls", "csv", "txt"],
                key="alertas_upload"
            )

    with st.spinner("Cargando datos..."):
        if (eventos_upload is None) or (alertas_upload is None):
            st.error("Debes subir ambos archivos: Eventos y Alertas (Excel/CSV/TXT)")
            st.stop()
        eventos_df = data_loader.load_eventos_from_upload(eventos_upload)
        alertas_df = data_loader.load_alertas_from_upload(alertas_upload)
    
    if eventos_df is None or alertas_df is None:
        st.error("❌ Error al cargar los archivos subidos. Verifica el formato y las columnas requeridas")
        st.stop()
    
    if eventos_df is None:
        st.warning("⚠️ No se han cargado datos de eventos geotécnicos")
    
    if alertas_df is None:
        st.warning("⚠️ No se han cargado datos de alertas de seguridad")
    
    # Mostrar información básica de los datos
    st.sidebar.success(f"✅ Datos cargados exitosamente")
    if eventos_df is not None:
        st.sidebar.info(f"📊 Eventos: {len(eventos_df)} registros")
    if alertas_df is not None:
        st.sidebar.info(f"🚨 Alertas: {len(alertas_df)} registros")
    
    # Filtros en sidebar
    st.sidebar.header("🔍 Filtros")
    
    # Inicializar variables de fecha
    fechas_validas = pd.Series(dtype='datetime64[ns]')
    fecha_inicio = None
    fecha_fin = None
    
    # Filtro de fechas - considerar tanto eventos como alertas
    fechas_eventos = pd.Series(dtype='datetime64[ns]')
    fechas_alertas = pd.Series(dtype='datetime64[ns]')
    
    # Obtener fechas de eventos
    if 'Fecha' in eventos_df.columns:
        fechas_eventos = eventos_df['Fecha'].dropna()
    
    # Obtener fechas de alertas
    if 'Fecha Declarada' in alertas_df.columns:
        fechas_alertas = alertas_df['Fecha Declarada'].dropna()
    
    # Combinar todas las fechas para determinar el rango total
    todas_las_fechas = pd.concat([fechas_eventos, fechas_alertas], ignore_index=True)
    
    if len(todas_las_fechas) > 0:
        fecha_min = todas_las_fechas.min().date()
        fecha_max = todas_las_fechas.max().date()
        
        # Mostrar información de debug
        st.sidebar.info(f"📅 Rango total de fechas: {fecha_min} a {fecha_max}")
        if len(fechas_eventos) > 0:
            st.sidebar.info(f"📊 Eventos: {len(fechas_eventos)} registros")
        if len(fechas_alertas) > 0:
            st.sidebar.info(f"🚨 Alertas: {len(fechas_alertas)} registros")
        
        fecha_inicio = st.sidebar.date_input(
            "Fecha inicio",
            value=fecha_min,
            min_value=fecha_min,
            max_value=fecha_max
        )
        
        fecha_fin = st.sidebar.date_input(
            "Fecha fin",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max
        )
    else:
        # Si no hay fechas válidas, usar fechas por defecto
        st.sidebar.warning("⚠️ No se encontraron fechas válidas en los datos")
        fecha_inicio = st.sidebar.date_input(
            "Fecha inicio",
            value=datetime.now().date() - timedelta(days=365)
        )
        fecha_fin = st.sidebar.date_input(
            "Fecha fin",
            value=datetime.now().date()
        )
    
    # Inicializar variables de filtro
    zonas_seleccionadas = []
    tipos_seleccionados = []
    
    # Filtro por zona
    if 'Zona monitoreo' in eventos_df.columns:
        zonas_disponibles = eventos_df['Zona monitoreo'].dropna().unique()
        zonas_seleccionadas = st.sidebar.multiselect(
            "Zonas de monitoreo",
            options=zonas_disponibles,
            default=zonas_disponibles
        )
    
    # Filtro por tipo de evento
    if 'Tipo' in eventos_df.columns:
        tipos_disponibles = eventos_df['Tipo'].dropna().unique()
        tipos_seleccionados = st.sidebar.multiselect(
            "Tipos de evento",
            options=tipos_disponibles,
            default=tipos_disponibles
        )
    
    # Aplicar filtros
    eventos_filtrados = eventos_df.copy()
    alertas_filtradas = alertas_df.copy()
    
    # Aplicar filtros de fecha para eventos
    if 'Fecha' in eventos_df.columns and len(fechas_eventos) > 0 and fecha_inicio is not None and fecha_fin is not None:
        eventos_filtrados = eventos_filtrados[
            (eventos_filtrados['Fecha'] >= pd.to_datetime(fecha_inicio)) &
            (eventos_filtrados['Fecha'] <= pd.to_datetime(fecha_fin))
        ]
    
    # Aplicar filtros de fecha para alertas
    if 'Fecha Declarada' in alertas_df.columns and len(fechas_alertas) > 0 and fecha_inicio is not None and fecha_fin is not None:
        alertas_filtradas = alertas_filtradas[
            (alertas_filtradas['Fecha Declarada'] >= pd.to_datetime(fecha_inicio)) &
            (alertas_filtradas['Fecha Declarada'] <= pd.to_datetime(fecha_fin))
        ]
    
    # Aplicar filtros de zona para eventos
    if 'Zona monitoreo' in eventos_df.columns and zonas_seleccionadas:
        eventos_filtrados = eventos_filtrados[
            eventos_filtrados['Zona monitoreo'].isin(zonas_seleccionadas)
        ]
    
    # Aplicar filtros de zona para alertas (usando la columna correcta)
    if 'Zona de Monitoreo' in alertas_df.columns and zonas_seleccionadas:
        alertas_filtradas = alertas_filtradas[
            alertas_filtradas['Zona de Monitoreo'].isin(zonas_seleccionadas)
        ]
    
    # Aplicar filtros de tipo para eventos
    if 'Tipo' in eventos_df.columns and tipos_seleccionados:
        eventos_filtrados = eventos_filtrados[
            eventos_filtrados['Tipo'].isin(tipos_seleccionados)
        ]
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Dashboard", "📈 Eventos", "🚨 Alertas", "🗂️ DXF", "🔺 STL", "📋 Datos"])
    
    with tab1:
        st.header("Dashboard General")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Eventos",
                value=len(eventos_filtrados),
                delta=len(eventos_filtrados) - len(eventos_df)
            )
        
        with col2:
            st.metric(
                label="Total Alertas",
                value=len(alertas_filtradas),
                delta=len(alertas_filtradas) - len(alertas_df)
            )
        
        with col3:
            if 'Detectado por Sistema' in eventos_filtrados.columns:
                # Buscar tanto 'Sí' (con tilde) como 'Si' (sin tilde) para mayor compatibilidad
                detectados = eventos_filtrados['Detectado por Sistema'].value_counts().get('Sí', 0)
                if detectados == 0:
                    detectados = eventos_filtrados['Detectado por Sistema'].value_counts().get('Si', 0)
                st.metric(
                    label="Eventos Detectados",
                    value=detectados,
                    delta=f"{(detectados/len(eventos_filtrados)*100):.1f}%" if len(eventos_filtrados) > 0 else "0%"
                )
        
        with col4:
            if 'Estado' in alertas_filtradas.columns:
                cerradas = alertas_filtradas['Estado'].value_counts().get('Cerrado', 0)
                st.metric(
                    label="Alertas Cerradas",
                    value=cerradas,
                    delta=f"{(cerradas/len(alertas_filtradas)*100):.1f}%" if len(alertas_filtradas) > 0 else "0%"
                )
        
        # Gráficos del dashboard
        if len(eventos_filtrados) > 0:
            create_dashboard_metrics(eventos_filtrados, alertas_filtradas)
    
    with tab2:
        st.header("Análisis de Eventos")
        
        if len(eventos_filtrados) > 0:
            # Timeline de eventos
            create_events_timeline(eventos_filtrados)
            
            # Scatter plot de eventos
            create_events_scatter(eventos_filtrados)
            
            # Análisis de altura de falla
            create_failure_height_analysis(eventos_filtrados)
            
            # Distribución por zona
            if 'Zona monitoreo' in eventos_filtrados.columns:
                st.subheader("Distribución por Zona")
                zona_counts = eventos_filtrados['Zona monitoreo'].value_counts()
                fig_zona = px.bar(
                    x=zona_counts.index,
                    y=zona_counts.values,
                    title="Eventos por Zona de Monitoreo"
                )
                st.plotly_chart(fig_zona, use_container_width=True)
        else:
            st.warning("No hay eventos que mostrar con los filtros seleccionados")
    
    with tab3:
        st.header("Análisis de Alertas")
        
        if len(alertas_filtradas) > 0:
            # Scatter plot de alertas
            create_alerts_scatter(alertas_filtradas)
            
            # Estado de alertas
            if 'Estado' in alertas_filtradas.columns:
                st.subheader("Estado de Alertas")
                estado_counts = alertas_filtradas['Estado'].value_counts()
                fig_estado = px.pie(
                    values=estado_counts.values,
                    names=estado_counts.index,
                    title="Distribución por Estado"
                )
                st.plotly_chart(fig_estado, use_container_width=True)
        else:
            st.warning("No hay alertas que mostrar con los filtros seleccionados")
    
    with tab4:
        st.header("🗂️ Visualización DXF")
        
        # Carga de archivo DXF
        dxf_file = st.file_uploader(
            "📁 Subir archivo DXF",
            type=['dxf'],
            help="Archivo DXF con información geométrica",
            key="dxf_uploader"
        )
        
        if dxf_file is not None:
            try:
                # Cargar archivo DXF
                dxf_loader = DXFLoader()
                dxf_doc = dxf_loader.load_dxf_from_upload(dxf_file)
                
                if dxf_doc is not None:
                    st.success("✅ Archivo DXF cargado exitosamente")
                    
                    # Pestañas DXF
                    dxf_tab1, dxf_tab2, dxf_tab3, dxf_tab4 = st.tabs([
                        "🗺️ Mapa Base", 
                        "📍 Con Eventos", 
                        "📊 Estadísticas", 
                        "📋 Capas"
                    ])
                    
                    with dxf_tab1:
                        create_dxf_base_map(dxf_doc)
                    
                    with dxf_tab2:
                        if eventos_df is not None and len(eventos_df) > 0:
                            create_dxf_with_events_map(dxf_doc, eventos_df)
                        else:
                            st.warning("No hay datos de eventos para mostrar en el mapa DXF")
                    
                    with dxf_tab3:
                        create_dxf_statistics_chart(dxf_doc)
                    
                    with dxf_tab4:
                        create_dxf_layers_summary(dxf_doc)
                        
                else:
                    st.error("❌ Error al procesar el archivo DXF")
                    
            except Exception as e:
                st.error(f"❌ Error al cargar el archivo DXF: {str(e)}")
        else:
            st.info("👆 Sube un archivo DXF para comenzar la visualización")
    
    with tab5:
        st.header("🔺 Visualización STL")
        
        # Carga de archivo STL
        stl_file = st.file_uploader(
            "📁 Subir archivo STL",
            type=['stl'],
            help="Archivo STL con modelo 3D",
            key="stl_uploader"
        )
        
        if stl_file is not None:
            try:
                # Cargar archivo STL
                stl_loader = STLLoader()
                mesh_data = stl_loader.load_stl_from_upload(stl_file)
                
                if mesh_data is not None:
                    st.success("✅ Archivo STL cargado exitosamente")
                    
                    # Pestañas STL
                    stl_tab1, stl_tab2 = st.tabs(["🎯 Visualización 3D", "📊 Métricas"])
                    
                    with stl_tab1:
                        # Crear visualización 3D
                        fig_3d = create_stl_mesh_figure(mesh_data)
                        st.plotly_chart(fig_3d, use_container_width=True)
                        
                        # Opciones de exportación
                        st.subheader("📤 Exportar")
                        if st.button("💾 Exportar a OBJ"):
                            try:
                                obj_content = stl_loader.export_to_obj(mesh_data)
                                st.download_button(
                                    label="📥 Descargar archivo OBJ",
                                    data=obj_content,
                                    file_name=f"modelo_3d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.obj",
                                    mime="application/octet-stream"
                                )
                            except Exception as e:
                                st.error(f"Error al exportar: {str(e)}")
                    
                    with stl_tab2:
                        # Mostrar métricas del modelo STL
                        render_stl_metrics(mesh_data)
                        
                else:
                    st.error("❌ Error al procesar el archivo STL")
                    
            except Exception as e:
                st.error(f"❌ Error al cargar el archivo STL: {str(e)}")
        else:
            st.info("👆 Sube un archivo STL para comenzar la visualización 3D")
    
    with tab6:
        st.header("Datos Detallados")
        
        # Subtabs para eventos y alertas
        subtab1, subtab2 = st.tabs(["Eventos", "Alertas"])
        
        with subtab1:
            st.subheader("Tabla de Eventos")
            st.dataframe(eventos_filtrados, use_container_width=True)
            
            # Botón de descarga
            csv_eventos = eventos_filtrados.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Eventos (CSV)",
                data=csv_eventos,
                file_name=f"eventos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with subtab2:
            st.subheader("Tabla de Alertas")
            st.dataframe(alertas_filtradas, use_container_width=True)
            
            # Botón de descarga
            csv_alertas = alertas_filtradas.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Alertas (CSV)",
                data=csv_alertas,
                file_name=f"alertas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
