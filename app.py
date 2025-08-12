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

from src.data_loader import DataLoader
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
        eventos_df = data_loader.load_eventos_from_filelike(eventos_upload)
        alertas_df = data_loader.load_alertas_from_filelike(alertas_upload)
    
    if eventos_df is None or alertas_df is None:
        st.error("❌ Error al cargar los archivos subidos. Verifica el formato y las columnas requeridas")
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Dashboard", "📈 Eventos", "🚨 Alertas", "📋 Datos", "🗺️ DXF", "🔺 STL"])
    
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
    
    # Pestaña DXF
    with tab5:
        st.header("🗺️ Visualización DXF")
        st.markdown("Carga y visualiza archivos DXF (AutoCAD) integrados con datos geotécnicos")
        
        # Inicializar session state para DXF
        if 'dxf_loader' not in st.session_state:
            st.session_state.dxf_loader = None
        if 'dxf_loaded' not in st.session_state:
            st.session_state.dxf_loaded = False
        
        # Sección de carga de archivo DXF
        st.subheader("📁 Cargar Archivo DXF")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Selecciona un archivo DXF",
                type=['dxf'],
                help="Formatos soportados: .dxf (AutoCAD Drawing Exchange Format)"
            )
        
        with col2:
            if uploaded_file is not None:
                if st.button("🔄 Cargar DXF", type="primary"):
                    with st.spinner("Cargando archivo DXF..."):
                        try:
                            # Crear nuevo cargador DXF
                            dxf_loader = DXFLoader()
                            
                            # Cargar archivo desde bytes
                            success = dxf_loader.load_dxf_from_bytes(
                                uploaded_file.getvalue(), 
                                uploaded_file.name
                            )
                            
                            if success:
                                st.session_state.dxf_loader = dxf_loader
                                st.session_state.dxf_loaded = True
                                st.success(f"✅ Archivo DXF '{uploaded_file.name}' cargado exitosamente")
                            else:
                                st.error("❌ Error al cargar el archivo DXF")
                                
                        except Exception as e:
                            st.error(f"❌ Error al procesar archivo DXF: {str(e)}")
        
        # Mostrar contenido DXF si está cargado
        if st.session_state.dxf_loaded and st.session_state.dxf_loader:
            dxf_loader = st.session_state.dxf_loader
            
            st.markdown("---")
            
            # Resumen del archivo DXF
            st.subheader("📊 Resumen del Archivo DXF")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Obtener resumen
                summary = dxf_loader.get_summary()
                
                if summary:
                    st.metric("Capas Totales", summary.get('layers_count', 0))
                    st.metric("Entidades Totales", summary.get('total_entities', 0))
                    
                    entities = summary.get('entities', {})
                    st.write("**Tipos de Entidades:**")
                    for entity_type, count in entities.items():
                        st.write(f"• {entity_type.title()}: {count}")
                    
                    # Mostrar dimensiones del dibujo
                    drawing_size = summary.get('drawing_size')
                    if drawing_size:
                        st.write(f"**Dimensiones:** {drawing_size['width']:.2f} x {drawing_size['height']:.2f} m")
            
            with col2:
                # Gráfico de estadísticas
                stats_fig = create_dxf_statistics_chart(dxf_loader)
                if stats_fig.data:
                    st.plotly_chart(stats_fig, use_container_width=True)
            
            # Tabla de capas
            st.subheader("📋 Información de Capas")
            layers_df = create_dxf_layers_summary(dxf_loader)
            if not layers_df.empty:
                st.dataframe(layers_df, use_container_width=True)
            
            # Configuración de visualización
            st.subheader("⚙️ Configuración de Visualización")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Capas a Mostrar:**")
                layers_info = dxf_loader.get_layers_info()
                available_layers = list(layers_info.keys())
                
                selected_layers = st.multiselect(
                    "Selecciona las capas a visualizar",
                    options=available_layers,
                    default=available_layers[:5] if len(available_layers) > 5 else available_layers,
                    help="Selecciona las capas DXF que deseas mostrar en el mapa"
                )
            
            with col2:
                st.write("**Elementos DXF:**")
                show_lines = st.checkbox("Mostrar Líneas", value=True)
                show_polylines = st.checkbox("Mostrar Polilíneas", value=True)
                show_circles = st.checkbox("Mostrar Círculos", value=True)
                show_text = st.checkbox("Mostrar Texto", value=False)
            
            # Pestañas de visualización DXF
            dxf_tab1, dxf_tab2, dxf_tab3 = st.tabs(["🗺️ Mapa DXF", "🔄 Integrado", "📊 Análisis"])
            
            with dxf_tab1:
                st.subheader("Mapa Base DXF")
                
                if selected_layers:
                    with st.spinner("Generando mapa DXF..."):
                        try:
                            dxf_fig = create_dxf_base_map(
                                dxf_loader, 
                                selected_layers,
                                show_lines=show_lines,
                                show_polylines=show_polylines,
                                show_circles=show_circles,
                                show_text=show_text
                            )
                            
                            st.plotly_chart(dxf_fig, use_container_width=True)
                            
                        except Exception as e:
                            st.error(f"Error al generar mapa DXF: {str(e)}")
                else:
                    st.warning("⚠️ Selecciona al menos una capa para visualizar")
            
            with dxf_tab2:
                st.subheader("Mapa Integrado: DXF + Datos Geotécnicos")
                
                if selected_layers:
                    with st.spinner("Generando mapa integrado..."):
                        try:
                            dxf_elements = {
                                'lines': show_lines,
                                'polylines': show_polylines,
                                'circles': show_circles,
                                'text': show_text
                            }
                            
                            integrated_fig = create_dxf_with_events_map(
                                dxf_loader,
                                eventos_filtrados,
                                alertas_filtradas,
                                selected_layers,
                                dxf_elements
                            )
                            
                            st.plotly_chart(integrated_fig, use_container_width=True)
                            
                            # Métricas del mapa integrado
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric(
                                    "Eventos Mostrados",
                                    len(eventos_filtrados)
                                )
                            
                            with col2:
                                st.metric(
                                    "Alertas Mostradas",
                                    len(alertas_filtradas)
                                )
                            
                            with col3:
                                st.metric(
                                    "Capas DXF Activas",
                                    len(selected_layers)
                                )
                            
                        except Exception as e:
                            st.error(f"Error al generar mapa integrado: {str(e)}")
                else:
                    st.warning("⚠️ Selecciona al menos una capa para visualizar")
            
            with dxf_tab3:
                st.subheader("Análisis de Datos DXF")
                
                if selected_layers:
                    # Análisis de líneas
                    lines_df = dxf_loader.extract_lines(selected_layers)
                    if not lines_df.empty:
                        st.write("**📏 Análisis de Líneas:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Total de Líneas", len(lines_df))
                            st.metric("Longitud Promedio", f"{lines_df['length'].mean():.2f} m")
                        
                        with col2:
                            st.metric("Longitud Total", f"{lines_df['length'].sum():.2f} m")
                            st.metric("Longitud Máxima", f"{lines_df['length'].max():.2f} m")
                        
                        # Distribución por capas
                        layer_counts = lines_df['layer'].value_counts()
                        if len(layer_counts) > 1:
                            fig_layers = px.bar(
                                x=layer_counts.index,
                                y=layer_counts.values,
                                title="Distribución de Líneas por Capa",
                                labels={'x': 'Capa', 'y': 'Cantidad de Líneas'}
                            )
                            st.plotly_chart(fig_layers, use_container_width=True)
                    
                    # Análisis de polilíneas
                    polylines_df = dxf_loader.extract_polylines(selected_layers)
                    if not polylines_df.empty:
                        st.write("**🔗 Análisis de Polilíneas:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Total de Polilíneas", len(polylines_df))
                            closed_count = polylines_df['closed'].sum()
                            st.metric("Polilíneas Cerradas", closed_count)
                        
                        with col2:
                            avg_vertices = polylines_df['vertices_count'].mean()
                            st.metric("Vértices Promedio", f"{avg_vertices:.1f}")
                            max_vertices = polylines_df['vertices_count'].max()
                            st.metric("Máximo Vértices", max_vertices)
                    
                    # Análisis de círculos
                    circles_df = dxf_loader.extract_circles(selected_layers)
                    if not circles_df.empty:
                        st.write("**⭕ Análisis de Círculos:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Total de Círculos", len(circles_df))
                            st.metric("Radio Promedio", f"{circles_df['radius'].mean():.2f} m")
                        
                        with col2:
                            st.metric("Área Total", f"{circles_df['area'].sum():.2f} m²")
                            st.metric("Radio Máximo", f"{circles_df['radius'].max():.2f} m")
                else:
                    st.warning("⚠️ Selecciona capas para ver el análisis")
        
        else:
            # Instrucciones cuando no hay archivo cargado
            st.info("""
            ### 📋 Instrucciones para usar archivos DXF:
            
            1. **Carga un archivo DXF** usando el botón de arriba
            2. **Selecciona las capas** que deseas visualizar
            3. **Configura los elementos** a mostrar (líneas, polilíneas, círculos, texto)
            4. **Explora las visualizaciones** en las pestañas disponibles:
               - **Mapa DXF**: Visualización solo del archivo DXF
               - **Integrado**: DXF combinado con eventos y alertas geotécnicas
               - **Análisis**: Estadísticas y métricas del archivo DXF
            
            ### 🎯 Beneficios de la integración DXF:
            - **Contexto espacial**: Visualiza eventos sobre planos de la mina
            - **Referencias geográficas**: Coordenadas precisas y límites
            - **Capas organizadas**: Diferentes elementos por categorías
            - **Análisis avanzado**: Métricas de geometría y distribución
            """)

    # Pestaña STL
    with tab6:
        st.header("🔺 Visualización STL (Malla 3D)")
        st.markdown("Carga y visualiza archivos STL de mallas 3D")

        # Session state para STL
        if 'stl_loader' not in st.session_state:
            st.session_state.stl_loader = None
        if 'stl_loaded' not in st.session_state:
            st.session_state.stl_loaded = False

        # Carga de archivo STL
        st.subheader("📁 Cargar Archivo STL")
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_stl = st.file_uploader(
                "Selecciona un archivo STL",
                type=['stl'],
                help="Formatos soportados: .stl (Binary o ASCII)"
            )

        with col2:
            if uploaded_stl is not None and st.button("🔄 Cargar STL", type="primary"):
                with st.spinner("Cargando archivo STL..."):
                    try:
                        stl_loader = STLLoader()
                        stl_bytes = uploaded_stl.getvalue()
                        success = stl_loader.load_stl_from_bytes(stl_bytes, uploaded_stl.name)
                        if success:
                            st.session_state.stl_loader = stl_loader
                            st.session_state.stl_loaded = True
                            st.session_state.stl_original_bytes = stl_bytes
                            st.success(f"✅ Archivo STL '{uploaded_stl.name}' cargado exitosamente")
                        else:
                            st.error("❌ Error al cargar el archivo STL")
                    except Exception as e:
                        st.error(f"❌ Error al procesar archivo STL: {str(e)}")

        # Mostrar contenido STL si está cargado
        if st.session_state.stl_loaded and st.session_state.stl_loader:
            stl_loader = st.session_state.stl_loader

            st.markdown("---")
            st.subheader("📊 Resumen de la Malla STL")
            render_stl_metrics(stl_loader)

            st.subheader("⚙️ Configuración de Visualización 3D")
            colc1, colc2 = st.columns(2)
            with colc1:
                mesh_color = st.color_picker("Color de la malla", value="#8c564b")
            with colc2:
                opacity = st.slider("Opacidad", min_value=0.1, max_value=1.0, value=0.8)

            with st.spinner("Generando visualización 3D..."):
                fig_stl = create_stl_mesh_figure(stl_loader, color=mesh_color, opacity=opacity)
                st.plotly_chart(fig_stl, use_container_width=True)

            st.subheader("⬇️ Exportación")
            colx1, colx2 = st.columns(2)
            with colx1:
                obj_str = stl_loader.export_as_obj()
                if obj_str:
                    st.download_button(
                        label="📥 Descargar como OBJ",
                        data=obj_str,
                        file_name="malla_exportada.obj",
                        mime="text/plain"
                    )
            with colx2:
                # Re-ofrecer el archivo STL original si está disponible en el uploader
                if 'stl_original_bytes' not in st.session_state:
                    st.session_state.stl_original_bytes = None
                # Guardar bytes si recién se cargó
                # Nota: esto lo llenamos cuando se presiona cargar
                if st.session_state.get('stl_original_bytes'):
                    st.download_button(
                        label="📥 Descargar STL original",
                        data=st.session_state['stl_original_bytes'],
                        file_name="malla_original.stl",
                        mime="application/sla"
                    )
        else:
            st.info("""
            ### 📋 Instrucciones para usar archivos STL:

            1. **Carga un archivo STL** usando el botón de arriba
            2. **Configura** el color y la opacidad de la malla
            3. **Explora** la malla en 3D con controles de cámara
            """)

if __name__ == "__main__":
    main()
