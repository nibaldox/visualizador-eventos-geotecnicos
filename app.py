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
    create_alerts_scatter, create_correlation_analysis, create_failure_height_analysis
)
from utils import format_date, validate_coordinates

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
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        eventos_df, alertas_df = data_loader.load_all_data()
    
    if eventos_df is None or alertas_df is None:
        st.error("❌ Error al cargar los archivos de datos. Verifica que los archivos Excel estén en la carpeta data-input/")
        st.stop()
    
    # Mostrar información básica de los datos
    st.sidebar.success(f"✅ Datos cargados exitosamente")
    st.sidebar.info(f"📊 Eventos: {len(eventos_df)} registros")
    st.sidebar.info(f"🚨 Alertas: {len(alertas_df)} registros")
    
    # Filtros en sidebar
    st.sidebar.header("🔍 Filtros")
    
    # Inicializar variables de fecha
    fechas_validas = pd.Series(dtype='datetime64[ns]')
    fecha_inicio = None
    fecha_fin = None
    
    # Filtro de fechas
    if 'Fecha' in eventos_df.columns:
        # Filtrar fechas válidas (no NaT)
        fechas_validas = eventos_df['Fecha'].dropna()
        
        if len(fechas_validas) > 0:
            fecha_min = fechas_validas.min().date()
            fecha_max = fechas_validas.max().date()
            
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
            fecha_inicio = st.sidebar.date_input(
                "Fecha inicio",
                value=datetime.now().date() - timedelta(days=365)
            )
            fecha_fin = st.sidebar.date_input(
                "Fecha fin",
                value=datetime.now().date()
            )
    
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
    
    # Aplicar filtros de fecha
    if 'Fecha' in eventos_df.columns and len(fechas_validas) > 0 and fecha_inicio is not None and fecha_fin is not None:
        eventos_filtrados = eventos_filtrados[
            (eventos_filtrados['Fecha'] >= pd.to_datetime(fecha_inicio)) &
            (eventos_filtrados['Fecha'] <= pd.to_datetime(fecha_fin))
        ]
    
    # Aplicar filtros de zona
    if 'Zona monitoreo' in eventos_df.columns and zonas_seleccionadas:
        eventos_filtrados = eventos_filtrados[
            eventos_filtrados['Zona monitoreo'].isin(zonas_seleccionadas)
        ]
    
    # Aplicar filtros de tipo
    if 'Tipo' in eventos_df.columns and tipos_seleccionados:
        eventos_filtrados = eventos_filtrados[
            eventos_filtrados['Tipo'].isin(tipos_seleccionados)
        ]
    
    # Pestañas principales
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Eventos", "🚨 Alertas", "📋 Datos"])
    
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
