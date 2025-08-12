"""
Módulo para crear visualizaciones interactivas de eventos geotécnicos y alertas
Contiene funciones para generar gráficos, mapas y dashboards

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

def create_dashboard_metrics(eventos_df: pd.DataFrame, alertas_df: pd.DataFrame):
    """
    Crear métricas y gráficos principales para el dashboard
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
        alertas_df (pd.DataFrame): DataFrame de alertas de seguridad
    """
    
    # Gráfico de eventos por mes
    if 'Fecha' in eventos_df.columns:
        st.subheader("📈 Tendencia de Eventos por Mes")
        
        # Filtrar fechas válidas
        eventos_validos = eventos_df.dropna(subset=['Fecha'])
        
        if len(eventos_validos) > 0:
            # Crear lista de todos los meses del año 2025
            meses_2025 = [
                '2025-01', '2025-02', '2025-03', '2025-04', '2025-05', '2025-06',
                '2025-07', '2025-08', '2025-09', '2025-10', '2025-11', '2025-12'
            ]
            
            nombres_meses = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]
            
            # Contar eventos por mes
            eventos_validos['Año_Mes'] = eventos_validos['Fecha'].dt.strftime('%Y-%m')
            conteo_eventos = eventos_validos['Año_Mes'].value_counts().to_dict()
            
            # Crear datos para el gráfico con todos los meses
            datos_grafico = []
            for i, mes in enumerate(meses_2025):
                cantidad = conteo_eventos.get(mes, 0)
                datos_grafico.append({
                    'Mes': nombres_meses[i],
                    'Mes_Num': mes,
                    'Cantidad': cantidad
                })
            
            df_grafico = pd.DataFrame(datos_grafico)
            
            # Crear gráfico de barras
            fig_tendencia = px.bar(
                df_grafico,
                x='Mes',
                y='Cantidad',
                title="Evolución Temporal de Eventos 2025 (Una Barra por Mes)",
                color_discrete_sequence=['red']
            )
            
            fig_tendencia.update_layout(
                xaxis_title="Mes",
                yaxis_title="Número de Eventos",
                hovermode='x unified',
                xaxis={'categoryorder': 'array', 'categoryarray': nombres_meses}
            )
            
            st.plotly_chart(fig_tendencia, use_container_width=True)
        else:
            st.warning("No hay eventos con fechas válidas para mostrar")
    
    # Mapa de eventos con filtro de mes
    create_dashboard_events_map(eventos_df)
    
    # Gráfico scatter consolidado
    create_consolidated_scatter(eventos_df, alertas_df)
    
    # Mapa 3D interactivo
    create_3d_map(eventos_df, alertas_df)
    
    # Gráficos en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución por tipo de evento
        if 'Tipo' in eventos_df.columns:
            st.subheader("🎯 Tipos de Eventos")
            tipo_counts = eventos_df['Tipo'].value_counts()
            
            fig_tipos = px.pie(
                values=tipo_counts.values,
                names=tipo_counts.index,
                title="Distribución por Tipo de Evento"
            )
            fig_tipos.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_tipos, use_container_width=True)
    
    with col2:
        # Detección por sistema
        if 'Detectado por Sistema' in eventos_df.columns:
            st.subheader("🤖 Detección Automática")
            deteccion_counts = eventos_df['Detectado por Sistema'].value_counts()
            
            # Definir colores para detección (rojo para eventos)
            colors_deteccion = ['red' if x == 'Si' else 'darkred' for x in deteccion_counts.index]
            
            fig_deteccion = px.bar(
                x=deteccion_counts.index,
                y=deteccion_counts.values,
                title="Eventos Detectados por Sistema",
                color=deteccion_counts.index,
                color_discrete_map={'Si': 'red', 'No': 'darkred'}
            )
            fig_deteccion.update_layout(
                xaxis_title="Detectado por Sistema",
                yaxis_title="Cantidad de Eventos",
                showlegend=False
            )
            st.plotly_chart(fig_deteccion, use_container_width=True)
    
    # Correlación eventos-alertas
    if len(alertas_df) > 0:
        st.subheader("🔗 Correlación Eventos-Alertas")
        
        # Crear timeline combinado
        timeline_data = []
        
        # Agregar eventos
        for _, evento in eventos_df.iterrows():
            if pd.notna(evento.get('Fecha')):
                timeline_data.append({
                    'Fecha': evento['Fecha'],
                    'Tipo': 'Evento',
                    'Descripcion': f"Evento {evento.get('Tipo', 'N/A')} - Zona: {evento.get('Zona monitoreo', 'N/A')}",
                    'Zona': evento.get('Zona monitoreo', 'N/A')
                })
        
        # Agregar alertas
        for _, alerta in alertas_df.iterrows():
            if pd.notna(alerta.get('Fecha Declarada')):
                timeline_data.append({
                    'Fecha': alerta['Fecha Declarada'],
                    'Tipo': 'Alerta',
                    'Descripcion': f"Alerta {alerta.get('Estatus', 'N/A')} - Zona: {alerta.get('Zona de Monitoreo', 'N/A')}",
                    'Zona': alerta.get('Zona de Monitoreo', 'N/A')
                })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            
            fig_timeline = px.scatter(
                timeline_df,
                x='Fecha',
                y='Tipo',
                color='Zona',
                hover_data=['Descripcion'],
                title="Timeline de Eventos y Alertas"
            )
            fig_timeline.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Tipo",
                height=400
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

def create_events_timeline(eventos_df: pd.DataFrame):
    """
    Crear timeline detallado de eventos
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
    """
    
    if 'Fecha' in eventos_df.columns and len(eventos_df) > 0:
        st.subheader("⏰ Timeline de Eventos")
        
        # Preparar datos para el timeline
        eventos_timeline = eventos_df.copy()
        eventos_timeline = eventos_timeline.sort_values('Fecha')
        
        # Crear gráfico de timeline
        fig = go.Figure()
        
        # Agregar puntos por tipo de evento
        if 'Tipo' in eventos_df.columns:
            tipos_unicos = eventos_df['Tipo'].unique()
            colors = px.colors.qualitative.Set3[:len(tipos_unicos)]
            
            for i, tipo in enumerate(tipos_unicos):
                eventos_tipo = eventos_timeline[eventos_timeline['Tipo'] == tipo]
                
                fig.add_trace(go.Scatter(
                    x=eventos_tipo['Fecha'],
                    y=[tipo] * len(eventos_tipo),
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=colors[i % len(colors)],
                        symbol='circle'
                    ),
                    name=tipo,
                    text=eventos_tipo.apply(lambda row: 
                        f"ID: {row.get('id', 'N/A')}<br>"
                        f"Zona: {row.get('Zona monitoreo', 'N/A')}<br>"
                        f"Vigilante: {row.get('Vigilante', 'N/A')}<br>"
                        f"Volumen: {row.get('Volumen (ton)', 'N/A')} ton", axis=1),
                    hovertemplate='<b>%{text}</b><br>Fecha: %{x}<extra></extra>'
                ))
        
        fig.update_layout(
            title="Timeline de Eventos Geotécnicos",
            xaxis_title="Fecha",
            yaxis_title="Tipo de Evento",
            height=500,
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estadísticas adicionales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'Volumen (ton)' in eventos_df.columns:
                volumen_total = eventos_df['Volumen (ton)'].sum()
                st.metric("Volumen Total", f"{volumen_total:,.0f} ton")
        
        with col2:
            if 'Velocidad Máxima Últimas 12hrs. (mm/h)' in eventos_df.columns:
                vel_max = eventos_df['Velocidad Máxima Últimas 12hrs. (mm/h)'].max()
                st.metric("Velocidad Máxima", f"{vel_max:.2f} mm/h")
        
        with col3:
            if 'Altura Falla (m)' in eventos_df.columns:
                altura_max = eventos_df['Altura Falla (m)'].max()
                st.metric("Altura Máxima Falla", f"{altura_max:.1f} m")

def create_alerts_scatter(alertas_df: pd.DataFrame):
    """
    Crear scatter plot de alertas con coordenadas locales de mina
    
    Args:
        alertas_df (pd.DataFrame): DataFrame de alertas de seguridad
    """
    
    if all(col in alertas_df.columns for col in ['Este', 'Norte']) and len(alertas_df) > 0:
        st.subheader("🗺️ Mapa de Alertas (Coordenadas Locales)")
        
        # Filtrar alertas con coordenadas válidas
        alertas_validas = alertas_df.dropna(subset=['Este', 'Norte'])
        
        if len(alertas_validas) > 0:
            # Definir colores por estado
            color_map = {
                'Abierto': 'yellow',
                'Cerrado': 'green',
                'En Proceso': 'yellow',  # Consideramos en proceso como abierto
                'Activo': 'yellow',
                'Inactivo': 'green'
            }
            
            # Crear scatter plot
            fig = px.scatter(
                alertas_validas,
                x='Este',
                y='Norte',
                color='Estado',
                size_max=15,
                hover_name='id',
                hover_data={
                    'Estado': True,
                    'Estatus': True,
                    'Zona de Monitoreo': True,
                    'Vigilante': True,
                    'Este': ':.0f',
                    'Norte': ':.0f'
                },
                title="Distribución Espacial de Alertas en la Mina",
                color_discrete_map=color_map
            )
            
            # Personalizar el gráfico
            fig.update_layout(
                xaxis_title="Coordenada Este (m)",
                yaxis_title="Coordenada Norte (m)",
                height=600,
                showlegend=True,
                hovermode='closest'
            )
            
            # Asegurar que el aspect ratio sea igual
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            # Grilla fija cada 500 m (gris muy suave)
            fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
            fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Estadísticas del mapa
            col1, col2, col3 = st.columns(3)
            
            with col1:
                alertas_abiertas = len(alertas_validas[alertas_validas['Estado'] == 'Abierto'])
                st.metric("Alertas Abiertas", alertas_abiertas)
            
            with col2:
                alertas_cerradas = len(alertas_validas[alertas_validas['Estado'] == 'Cerrado'])
                st.metric("Alertas Cerradas", alertas_cerradas)
            
            with col3:
                zonas_afectadas = alertas_validas['Zona de Monitoreo'].nunique()
                st.metric("Zonas Afectadas", zonas_afectadas)
        
        else:
            st.warning("No hay alertas con coordenadas válidas para mostrar en el mapa")
    
    else:
        st.warning("No se pueden crear mapas: faltan datos de coordenadas")

def create_events_scatter(eventos_df: pd.DataFrame):
    """
    Crear scatter plot de eventos geotécnicos con coordenadas locales de mina
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
    """
    
    if all(col in eventos_df.columns for col in ['Este', 'Norte']) and len(eventos_df) > 0:
        st.subheader("🗺️ Mapa de Eventos (Coordenadas Locales)")
        
        # Filtrar eventos con coordenadas válidas
        eventos_validos = eventos_df.dropna(subset=['Este', 'Norte'])
        
        if len(eventos_validos) > 0:
            # Definir colores por tipo de evento (todos rojos según especificación)
            tipos_unicos = eventos_validos['Tipo'].unique() if 'Tipo' in eventos_validos.columns else ['Sin Tipo']
            # Usar diferentes tonos de rojo para distinguir tipos
            red_colors = ['red', 'darkred', 'crimson', 'firebrick', 'indianred', 'lightcoral']
            color_map = dict(zip(tipos_unicos, red_colors[:len(tipos_unicos)]))
            
            # Preparar datos para el scatter plot
            size_column = None
            if 'Volumen (ton)' in eventos_validos.columns:
                # Verificar si hay valores válidos en la columna de volumen
                volumen_valido = eventos_validos['Volumen (ton)'].dropna()
                if len(volumen_valido) > 0 and volumen_valido.sum() > 0:
                    # Crear una columna de tamaño con valores por defecto para NaN
                    eventos_validos = eventos_validos.copy()
                    eventos_validos['Tamaño_Plot'] = eventos_validos['Volumen (ton)'].fillna(100)  # Valor por defecto
                    size_column = 'Tamaño_Plot'
            
            # Crear scatter plot
            fig = px.scatter(
                eventos_validos,
                x='Este',
                y='Norte',
                color='Tipo' if 'Tipo' in eventos_validos.columns else None,
                size=size_column,
                size_max=25,
                hover_name='id',
                hover_data={
                    'Tipo': True,
                    'Zona monitoreo': True,
                    'Vigilante': True,
                    'Volumen (ton)': ':.0f' if 'Volumen (ton)' in eventos_validos.columns else False,
                    'Velocidad Máxima Últimas 12hrs. (mm/h)': ':.2f' if 'Velocidad Máxima Últimas 12hrs. (mm/h)' in eventos_validos.columns else False,
                    'Este': ':.0f',
                    'Norte': ':.0f',
                    'Tamaño_Plot': False  # Ocultar la columna temporal
                },
                title="Distribución Espacial de Eventos Geotécnicos en la Mina",
                color_discrete_map=color_map
            )
            
            # Personalizar el gráfico
            fig.update_layout(
                xaxis_title="Coordenada Este (m)",
                yaxis_title="Coordenada Norte (m)",
                height=600,
                showlegend=True,
                hovermode='closest'
            )
            
            # Asegurar que el aspect ratio sea igual
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Estadísticas del mapa
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_eventos = len(eventos_validos)
                st.metric("Total Eventos", total_eventos)
            
            with col2:
                if 'Volumen (ton)' in eventos_validos.columns:
                    volumen_total = eventos_validos['Volumen (ton)'].sum()
                    st.metric("Volumen Total", f"{volumen_total:,.0f} ton")
            
            with col3:
                zonas_afectadas = eventos_validos['Zona monitoreo'].nunique() if 'Zona monitoreo' in eventos_validos.columns else 0
                st.metric("Zonas Afectadas", zonas_afectadas)
        
        else:
            st.warning("No hay eventos con coordenadas válidas para mostrar en el mapa")
    
    else:
        st.warning("No se pueden crear mapas: faltan datos de coordenadas")

def create_dashboard_events_map(eventos_df: pd.DataFrame):
    """
    Crear mapa scatter de eventos para dashboard con filtro de mes
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
    """
    
    if all(col in eventos_df.columns for col in ['Este', 'Norte', 'Fecha']) and len(eventos_df) > 0:
        st.subheader("🗺️ Mapa de Eventos por Mes")
        
        # Filtrar eventos con coordenadas y fechas válidas
        eventos_validos = eventos_df.dropna(subset=['Este', 'Norte', 'Fecha'])
        
        if len(eventos_validos) > 0:
            # Crear mapeo de nombres de meses en español
            meses_espanol = {
                'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
            }
            
            # Crear columnas para mes original y en español
            eventos_validos['Mes_Original'] = eventos_validos['Fecha'].dt.strftime('%B %Y')
            eventos_validos['Mes_Espanol'] = eventos_validos['Mes_Original']
            
            # Convertir nombres a español
            for eng, esp in meses_espanol.items():
                eventos_validos['Mes_Espanol'] = eventos_validos['Mes_Espanol'].str.replace(eng, esp)
            
            # Obtener lista de meses disponibles en español
            meses_disponibles = sorted(eventos_validos['Mes_Espanol'].unique())
            
            # Filtro de mes
            col1, col2 = st.columns([1, 3])
            
            with col1:
                mes_seleccionado = st.selectbox(
                    "Seleccionar mes a resaltar:",
                    options=['Todos'] + meses_disponibles,
                    index=0
                )
            
            # Preparar datos para el mapa
            eventos_mapa = eventos_validos.copy()
            
            # Asignar colores basado en el mes seleccionado
            if mes_seleccionado == 'Todos':
                eventos_mapa['Color'] = 'green'  # Todos verdes
                eventos_mapa['Categoria'] = 'Todos los eventos'
            else:
                # Comparar directamente con el mes en español
                eventos_mapa['Es_Mes_Seleccionado'] = eventos_mapa['Mes_Espanol'] == mes_seleccionado
                eventos_mapa['Color'] = eventos_mapa['Es_Mes_Seleccionado'].map({
                    True: 'yellow',  # Amarillo para mes seleccionado
                    False: 'green'   # Verde para otros meses
                })
                eventos_mapa['Categoria'] = eventos_mapa['Es_Mes_Seleccionado'].map({
                    True: f'Eventos de {mes_seleccionado}',
                    False: 'Otros meses'
                })
            
            # Crear scatter plot
            fig = px.scatter(
                eventos_mapa,
                x='Este',
                y='Norte',
                color='Categoria',
                size_max=15,
                hover_name='id',
                hover_data={
                    'Tipo': True if 'Tipo' in eventos_mapa.columns else False,
                    'Zona monitoreo': True if 'Zona monitoreo' in eventos_mapa.columns else False,
                    'Vigilante': True if 'Vigilante' in eventos_mapa.columns else False,
                    'Fecha': True,
                    'Este': ':.0f',
                    'Norte': ':.0f',
                    'Categoria': False,
                    'Color': False
                },
                title=f"Distribución Espacial de Eventos - {mes_seleccionado}",
                color_discrete_map={
                    'Todos los eventos': 'green',
                    f'Eventos de {mes_seleccionado}': 'yellow',
                    'Otros meses': 'green'
                }
            )
            
            # Personalizar el gráfico
            fig.update_layout(
                xaxis_title="Coordenada Este (m)",
                yaxis_title="Coordenada Norte (m)",
                height=500,
                showlegend=True,
                hovermode='closest'
            )
            
            # Asegurar que el aspect ratio sea igual
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            # Grilla fija cada 500 m (gris muy suave)
            fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
            fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
            
            with col2:
                st.plotly_chart(fig, use_container_width=True)
            
            # Estadísticas del mapa
            if mes_seleccionado != 'Todos':
                eventos_mes = eventos_mapa[eventos_mapa['Es_Mes_Seleccionado'] == True]
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(f"Eventos en {mes_seleccionado}", len(eventos_mes))
                
                with col2:
                    if 'Volumen (ton)' in eventos_mes.columns:
                        volumen_mes = eventos_mes['Volumen (ton)'].sum()
                        st.metric("Volumen del Mes", f"{volumen_mes:,.0f} ton")
                
                with col3:
                    if 'Zona monitoreo' in eventos_mes.columns:
                        zonas_mes = eventos_mes['Zona monitoreo'].nunique()
                        st.metric("Zonas Afectadas", zonas_mes)
        
        else:
            st.warning("No hay eventos con coordenadas y fechas válidas para mostrar en el mapa")
    
    else:
        st.warning("No se puede crear el mapa: faltan datos de coordenadas o fechas")

def create_consolidated_scatter(eventos_df: pd.DataFrame, alertas_df: pd.DataFrame):
    """
    Crear gráfico scatter consolidado que muestre alertas, alarmas y eventos juntos
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
        alertas_df (pd.DataFrame): DataFrame de alertas de seguridad
    """
    
    st.subheader("🎯 Vista Consolidada: Eventos, Alertas y Alarmas")
    
    # Verificar que tenemos datos con coordenadas
    eventos_validos = eventos_df.dropna(subset=['Este', 'Norte']) if 'Este' in eventos_df.columns and 'Norte' in eventos_df.columns else pd.DataFrame()
    alertas_validas = alertas_df.dropna(subset=['Este', 'Norte']) if 'Este' in alertas_df.columns and 'Norte' in alertas_df.columns else pd.DataFrame()
    
    if len(eventos_validos) == 0 and len(alertas_validas) == 0:
        st.warning("No hay datos con coordenadas válidas para mostrar")
        return
    
    # Preparar datos consolidados
    datos_consolidados = []
    
    # Agregar eventos
    if len(eventos_validos) > 0:
        for _, evento in eventos_validos.iterrows():
            datos_consolidados.append({
                'Este': evento['Este'],
                'Norte': evento['Norte'],
                'Tipo_General': 'Evento Geotécnico',
                'Subtipo': evento.get('Tipo', 'Sin especificar'),
                'ID': evento.get('id', 'N/A'),
                'Fecha': evento.get('Fecha', 'N/A'),
                'Zona': evento.get('Zona monitoreo', 'N/A'),
                'Vigilante': evento.get('Vigilante', 'N/A'),
                'Volumen': evento.get('Volumen (ton)', 0),
                'Color': 'red',
                'Tamaño': 4
            })
    
    # Agregar alertas/alarmas
    if len(alertas_validas) > 0:
        for _, alerta in alertas_validas.iterrows():
            # Determinar color basado en estado
            estado = alerta.get('Estado', 'Desconocido')
            if 'Abierta' in str(estado) or 'Activa' in str(estado):
                color = 'yellow'
            elif 'Cerrada' in str(estado) or 'Inactiva' in str(estado):
                color = 'green'
            else:
                color = 'orange'  # Estado desconocido
            
            datos_consolidados.append({
                'Este': alerta['Este'],
                'Norte': alerta['Norte'],
                'Tipo_General': 'Alerta/Alarma',
                'Subtipo': alerta.get('Tipo', 'Sin especificar'),
                'ID': alerta.get('id', 'N/A'),
                'Fecha': alerta.get('Fecha creacion', alerta.get('Fecha cierre', 'N/A')),
                'Zona': alerta.get('Zona monitoreo', 'N/A'),
                'Vigilante': alerta.get('Vigilante', 'N/A'),
                'Estado': estado,
                'Color': color,
                'Tamaño': 4
            })
    
    # Crear DataFrame consolidado
    df_consolidado = pd.DataFrame(datos_consolidados)
    
    if len(df_consolidado) == 0:
        st.warning("No hay datos válidos para mostrar en el gráfico consolidado")
        return
    
    # Crear filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipos_disponibles = df_consolidado['Tipo_General'].unique()
        tipos_seleccionados = st.multiselect(
            "Filtrar por tipo:",
            options=tipos_disponibles,
            default=tipos_disponibles
        )
    
    with col2:
        if 'Zona' in df_consolidado.columns:
            zonas_disponibles = df_consolidado['Zona'].unique()
            zonas_disponibles = [z for z in zonas_disponibles if str(z) != 'N/A']
            if zonas_disponibles:
                zonas_seleccionadas = st.multiselect(
                    "Filtrar por zona:",
                    options=['Todas'] + list(zonas_disponibles),
                    default=['Todas']
                )
            else:
                zonas_seleccionadas = ['Todas']
        else:
            zonas_seleccionadas = ['Todas']
    
    with col3:
        mostrar_leyenda = st.checkbox("Mostrar leyenda", value=True)
    
    # Aplicar filtros
    df_filtrado = df_consolidado[df_consolidado['Tipo_General'].isin(tipos_seleccionados)]
    
    if 'Todas' not in zonas_seleccionadas and zonas_seleccionadas:
        df_filtrado = df_filtrado[df_filtrado['Zona'].isin(zonas_seleccionadas)]
    
    # Crear gráfico scatter
    fig = px.scatter(
        df_filtrado,
        x='Este',
        y='Norte',
        color='Tipo_General',
        size_max=8,
        hover_name='ID',
        hover_data={
            'Subtipo': True,
            'Fecha': True,
            'Zona': True,
            'Vigilante': True,
            'Estado': True if 'Estado' in df_filtrado.columns else False,
            'Volumen': True if 'Volumen' in df_filtrado.columns else False,
            'Este': ':.0f',
            'Norte': ':.0f',
            'Tamaño': False
        },
        title="Vista Consolidada: Distribución Espacial de Eventos, Alertas y Alarmas",
        color_discrete_map={
            'Evento Geotécnico': 'red',
            'Alerta/Alarma': 'orange'  # Color base, se ajustará por estado
        }
    )
    
    # Personalizar el gráfico
    fig.update_layout(
        xaxis_title="Coordenada Este (m)",
        yaxis_title="Coordenada Norte (m)",
        height=600,
        showlegend=mostrar_leyenda,
        hovermode='closest'
    )
    
    # Asegurar aspect ratio igual
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    # Grilla fija cada 500 m (gris muy suave)
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Estadísticas consolidadas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_eventos = len(df_filtrado[df_filtrado['Tipo_General'] == 'Evento Geotécnico'])
        st.metric("Total Eventos", total_eventos)
    
    with col2:
        total_alertas = len(df_filtrado[df_filtrado['Tipo_General'] == 'Alerta/Alarma'])
        st.metric("Total Alertas/Alarmas", total_alertas)
    
    with col3:
        total_puntos = len(df_filtrado)
        st.metric("Total Puntos", total_puntos)
    
    with col4:
        if 'Zona' in df_filtrado.columns:
            zonas_unicas = df_filtrado['Zona'].nunique()
            st.metric("Zonas Involucradas", zonas_unicas)

def create_3d_map(eventos_df: pd.DataFrame, alertas_df: pd.DataFrame):
    """
    Crear mapa 3D interactivo que muestre eventos, alertas y alarmas con elevación
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
        alertas_df (pd.DataFrame): DataFrame de alertas de seguridad
    """
    
    st.subheader("🏔️ Mapa 3D Interactivo: Vista Espacial Avanzada")
    
    # Verificar que tenemos datos con coordenadas
    eventos_validos = eventos_df.dropna(subset=['Este', 'Norte']) if 'Este' in eventos_df.columns and 'Norte' in eventos_df.columns else pd.DataFrame()
    alertas_validas = alertas_df.dropna(subset=['Este', 'Norte']) if 'Este' in alertas_df.columns and 'Norte' in alertas_df.columns else pd.DataFrame()
    
    if len(eventos_validos) == 0 and len(alertas_validas) == 0:
        st.warning("No hay datos con coordenadas válidas para mostrar en el mapa 3D")
        return
    
    # Preparar datos 3D consolidados
    datos_3d = []
    
    # Agregar eventos con elevación
    if len(eventos_validos) > 0:
        for _, evento in eventos_validos.iterrows():
            # Usar elevación si está disponible, sino usar volumen como proxy de altura
            elevacion = evento.get('Elevacion', evento.get('Elevación', 0))
            if elevacion == 0 or pd.isna(elevacion):
                # Usar volumen como proxy de elevación (escalado)
                volumen = evento.get('Volumen (ton)', 0)
                elevacion = volumen / 1000 if volumen > 0 else np.random.uniform(0, 10)  # Altura aleatoria pequeña si no hay datos
            
            datos_3d.append({
                'Este': evento['Este'],
                'Norte': evento['Norte'],
                'Elevacion': elevacion,
                'Tipo': 'Evento Geotécnico',
                'Subtipo': evento.get('Tipo', 'Sin especificar'),
                'ID': evento.get('id', 'N/A'),
                'Fecha': str(evento.get('Fecha', 'N/A')),
                'Zona': evento.get('Zona monitoreo', 'N/A'),
                'Vigilante': evento.get('Vigilante', 'N/A'),
                'Volumen': evento.get('Volumen (ton)', 0),
                'Color': 'red'
            })
    
    # Agregar alertas/alarmas con elevación
    if len(alertas_validas) > 0:
        for _, alerta in alertas_validas.iterrows():
            # Usar elevación si está disponible, sino asignar altura pequeña aleatoria
            elevacion = alerta.get('Elevacion', alerta.get('Elevación', 0))
            if elevacion == 0 or pd.isna(elevacion):
                elevacion = np.random.uniform(0, 5)  # Altura aleatoria pequeña para alertas
            
            # Determinar color basado en estado
            estado = alerta.get('Estado', 'Desconocido')
            if 'Abierta' in str(estado) or 'Activa' in str(estado):
                color = 'yellow'
            elif 'Cerrada' in str(estado) or 'Inactiva' in str(estado):
                color = 'green'
            else:
                color = 'orange'
            
            datos_3d.append({
                'Este': alerta['Este'],
                'Norte': alerta['Norte'],
                'Elevacion': elevacion,
                'Tipo': 'Alerta/Alarma',
                'Subtipo': alerta.get('Tipo', 'Sin especificar'),
                'ID': alerta.get('id', 'N/A'),
                'Fecha': str(alerta.get('Fecha creacion', alerta.get('Fecha cierre', 'N/A'))),
                'Zona': alerta.get('Zona monitoreo', 'N/A'),
                'Vigilante': alerta.get('Vigilante', 'N/A'),
                'Estado': estado,
                'Color': color
            })
    
    # Crear DataFrame 3D
    df_3d = pd.DataFrame(datos_3d)
    
    if len(df_3d) == 0:
        st.warning("No hay datos válidos para mostrar en el mapa 3D")
        return
    
    # Controles del mapa 3D
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipos_3d = df_3d['Tipo'].unique()
        tipos_seleccionados_3d = st.multiselect(
            "Filtrar tipos (3D):",
            options=tipos_3d,
            default=tipos_3d,
            key="tipos_3d"
        )
    
    with col2:
        vista_3d = st.selectbox(
            "Vista 3D:",
            options=['Perspectiva', 'Superior', 'Lateral'],
            index=0,
            key="vista_3d"
        )
    
    with col3:
        mostrar_superficie = st.checkbox(
            "Mostrar superficie base",
            value=False,
            key="superficie_3d"
        )
    
    # Aplicar filtros
    df_3d_filtrado = df_3d[df_3d['Tipo'].isin(tipos_seleccionados_3d)]
    
    # Crear gráfico 3D
    fig_3d = px.scatter_3d(
        df_3d_filtrado,
        x='Este',
        y='Norte',
        z='Elevacion',
        color='Tipo',
        size_max=10,
        hover_name='ID',
        hover_data={
            'Subtipo': True,
            'Fecha': True,
            'Zona': True,
            'Vigilante': True,
            'Estado': True if 'Estado' in df_3d_filtrado.columns else False,
            'Volumen': True if 'Volumen' in df_3d_filtrado.columns else False,
            'Este': ':.0f',
            'Norte': ':.0f',
            'Elevacion': ':.1f'
        },
        title="Mapa 3D: Distribución Espacial con Elevación",
        color_discrete_map={
            'Evento Geotécnico': 'red',
            'Alerta/Alarma': 'orange'
        }
    )
    
    # Configurar vista 3D según selección
    if vista_3d == 'Superior':
        camera = dict(
            eye=dict(x=0, y=0, z=2.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=1, z=0)
        )
    elif vista_3d == 'Lateral':
        camera = dict(
            eye=dict(x=2.5, y=0, z=0.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        )
    else:  # Perspectiva
        camera = dict(
            eye=dict(x=1.5, y=1.5, z=1.5),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        )
    
    # Personalizar el gráfico 3D
    fig_3d.update_layout(
        scene=dict(
            xaxis_title="Coordenada Este (m)",
            yaxis_title="Coordenada Norte (m)",
            zaxis_title="Elevación (m)",
            camera=camera,
            aspectmode='cube' if mostrar_superficie else 'data'
        ),
        height=700,
        showlegend=True,
        title_x=0.5
    )
    
    # Agregar superficie base si se solicita
    if mostrar_superficie and len(df_3d_filtrado) > 0:
        # Crear malla de superficie base
        x_range = np.linspace(df_3d_filtrado['Este'].min(), df_3d_filtrado['Este'].max(), 20)
        y_range = np.linspace(df_3d_filtrado['Norte'].min(), df_3d_filtrado['Norte'].max(), 20)
        X, Y = np.meshgrid(x_range, y_range)
        Z = np.zeros_like(X)  # Superficie plana en z=0
        
        fig_3d.add_surface(
            x=X, y=Y, z=Z,
            opacity=0.3,
            colorscale='Greys',
            showscale=False,
            name='Superficie Base'
        )
    
    # Mostrar gráfico 3D
    st.plotly_chart(fig_3d, use_container_width=True)
    
    # Estadísticas 3D
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Puntos 3D", len(df_3d_filtrado))
    
    with col2:
        if len(df_3d_filtrado) > 0:
            elevacion_max = df_3d_filtrado['Elevacion'].max()
            st.metric("Elevación Máxima", f"{elevacion_max:.1f} m")
    
    with col3:
        if len(df_3d_filtrado) > 0:
            elevacion_min = df_3d_filtrado['Elevacion'].min()
            st.metric("Elevación Mínima", f"{elevacion_min:.1f} m")
    
    with col4:
        if len(df_3d_filtrado) > 0:
            rango_elevacion = df_3d_filtrado['Elevacion'].max() - df_3d_filtrado['Elevacion'].min()
            st.metric("Rango Elevación", f"{rango_elevacion:.1f} m")

def create_failure_height_analysis(eventos_df: pd.DataFrame):
    """
    Crear gráficos para análisis de altura de falla de eventos geotécnicos
    Categoriza en: ≤ 15m (verde), >15m y ≤ 30m (azul), >30m (rojo)
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
    """
    
    st.subheader("📏 Análisis de Altura de Falla")
    
    # Verificar si existe columna de altura de falla
    altura_col = None
    
    # Lista de posibles nombres de columna de altura de falla
    possible_columns = [
        'Altura Falla (m)',
        'Altura falla (m)', 
        'Altura de falla (m)',
        'Altura Banco (m)',
        'Altura',
        'Height'
    ]
    
    # Buscar la primera columna que exista
    for col_name in possible_columns:
        if col_name in eventos_df.columns:
            altura_col = col_name
            break
    
    if altura_col is None:
        st.warning("⚠️ No se encontró columna de altura de falla en los datos. Columnas disponibles: " + ", ".join(eventos_df.columns.tolist()))
        return
    
    # Filtrar eventos con altura de falla válida
    eventos_con_altura = eventos_df.dropna(subset=[altura_col])
    eventos_con_altura = eventos_con_altura[eventos_con_altura[altura_col] > 0]  # Solo alturas positivas
    
    if len(eventos_con_altura) == 0:
        st.warning("No hay eventos con datos válidos de altura de falla")
        return
    
    # Categorizar por altura de falla
    def categorizar_altura(altura):
        if altura <= 15:
            return "Baja (≤ 15m)"
        elif altura <= 30:
            return "Media (>15m - ≤ 30m)"
        else:
            return "Alta (>30m)"
    
    def color_categoria(categoria):
        if "Baja" in categoria:
            return "green"
        elif "Media" in categoria:
            return "blue"
        else:
            return "red"
    
    # Aplicar categorización
    eventos_con_altura['Categoria_Altura'] = eventos_con_altura[altura_col].apply(categorizar_altura)
    eventos_con_altura['Color_Categoria'] = eventos_con_altura['Categoria_Altura'].apply(color_categoria)
    
    # Layout en columnas para métricas
    col1, col2, col3, col4 = st.columns(4)
    
    # Contar eventos por categoría
    categoria_counts = eventos_con_altura['Categoria_Altura'].value_counts()
    
    with col1:
        baja_count = categoria_counts.get("Baja (≤ 15m)", 0)
        st.metric(
            label="🟢 Altura Baja",
            value=f"{baja_count} eventos",
            delta=f"{(baja_count/len(eventos_con_altura)*100):.1f}%"
        )
    
    with col2:
        media_count = categoria_counts.get("Media (>15m - ≤ 30m)", 0)
        st.metric(
            label="🔵 Altura Media",
            value=f"{media_count} eventos",
            delta=f"{(media_count/len(eventos_con_altura)*100):.1f}%"
        )
    
    with col3:
        alta_count = categoria_counts.get("Alta (>30m)", 0)
        st.metric(
            label="🔴 Altura Alta",
            value=f"{alta_count} eventos",
            delta=f"{(alta_count/len(eventos_con_altura)*100):.1f}%"
        )
    
    with col4:
        altura_promedio = eventos_con_altura[altura_col].mean()
        st.metric(
            label="📊 Altura Promedio",
            value=f"{altura_promedio:.1f}m",
            delta=f"Max: {eventos_con_altura[altura_col].max():.1f}m"
        )
    
    # Gráficos en columnas
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras por categoría
        fig_barras = px.bar(
            x=categoria_counts.index,
            y=categoria_counts.values,
            title="Distribución de Eventos por Altura de Falla",
            color=categoria_counts.index,
            color_discrete_map={
                "Baja (≤ 15m)": "green",
                "Media (>15m - ≤ 30m)": "blue",
                "Alta (>30m)": "red"
            }
        )
        fig_barras.update_layout(
            xaxis_title="Categoría de Altura",
            yaxis_title="Número de Eventos",
            showlegend=False
        )
        st.plotly_chart(fig_barras, use_container_width=True)
    
    with col2:
        # Gráfico de torta
        fig_pie = px.pie(
            values=categoria_counts.values,
            names=categoria_counts.index,
            title="Proporción por Categoría de Altura",
            color=categoria_counts.index,
            color_discrete_map={
                "Baja (≤ 15m)": "green",
                "Media (>15m - ≤ 30m)": "blue",
                "Alta (>30m)": "red"
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Histograma de distribución de alturas
    st.subheader("📈 Distribución de Alturas de Falla")
    
    fig_hist = px.histogram(
        eventos_con_altura,
        x=altura_col,
        color='Categoria_Altura',
        title="Histograma de Alturas de Falla",
        nbins=20,
        color_discrete_map={
            "Baja (≤ 15m)": "green",
            "Media (>15m - ≤ 30m)": "blue",
            "Alta (>30m)": "red"
        }
    )
    
    # Añadir líneas verticales para los límites
    fig_hist.add_vline(x=15, line_dash="dash", line_color="green", 
                       annotation_text="Límite 15m", annotation_position="top")
    fig_hist.add_vline(x=30, line_dash="dash", line_color="blue", 
                       annotation_text="Límite 30m", annotation_position="top")
    
    fig_hist.update_layout(
        xaxis_title="Altura de Falla (m)",
        yaxis_title="Frecuencia",
        bargap=0.1
    )
    
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Scatter plot espacial por categoría de altura
    if all(col in eventos_con_altura.columns for col in ['Este', 'Norte']):
        st.subheader("🗺️ Distribución Espacial por Altura de Falla")
        
        fig_scatter = px.scatter(
            eventos_con_altura,
            x='Este',
            y='Norte',
            color='Categoria_Altura',
            size=altura_col,
            hover_name='id' if 'id' in eventos_con_altura.columns else None,
            hover_data={
                altura_col: ':.1f',
                'Tipo': True if 'Tipo' in eventos_con_altura.columns else False,
                'Zona monitoreo': True if 'Zona monitoreo' in eventos_con_altura.columns else False,
                'Fecha': True if 'Fecha' in eventos_con_altura.columns else False,
                'Este': ':.0f',
                'Norte': ':.0f'
            },
            title="Ubicación de Eventos por Categoría de Altura de Falla",
            color_discrete_map={
                "Baja (≤ 15m)": "green",
                "Media (>15m - ≤ 30m)": "blue",
                "Alta (>30m)": "red"
            }
        )
        
        fig_scatter.update_layout(
            xaxis_title="Coordenada Este (m)",
            yaxis_title="Coordenada Norte (m)",
            height=500
        )
        
        # Asegurar aspect ratio igual
        fig_scatter.update_yaxes(scaleanchor="x", scaleratio=1)
        # Grilla fija cada 500 m (gris muy suave)
        fig_scatter.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
        fig_scatter.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
        
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Tabla resumen por categoría
    st.subheader("📋 Resumen Estadístico por Categoría")
    
    resumen_data = []
    for categoria in eventos_con_altura['Categoria_Altura'].unique():
        datos_cat = eventos_con_altura[eventos_con_altura['Categoria_Altura'] == categoria]
        resumen_data.append({
            'Categoría': categoria,
            'Cantidad': len(datos_cat),
            'Altura Promedio (m)': f"{datos_cat[altura_col].mean():.1f}",
            'Altura Mínima (m)': f"{datos_cat[altura_col].min():.1f}",
            'Altura Máxima (m)': f"{datos_cat[altura_col].max():.1f}",
            'Desviación Estándar': f"{datos_cat[altura_col].std():.1f}"
        })
    
    resumen_df = pd.DataFrame(resumen_data)
    st.dataframe(resumen_df, use_container_width=True)

def create_correlation_analysis(eventos_df: pd.DataFrame, alertas_df: pd.DataFrame):
    """
    Crear análisis de correlación entre eventos y alertas
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
        alertas_df (pd.DataFrame): DataFrame de alertas de seguridad
    """
    
    st.subheader("🔍 Análisis de Correlaciones")
    
    # Análisis temporal
    if 'Fecha' in eventos_df.columns and 'Fecha Declarada' in alertas_df.columns:
        
        # Crear series temporales
        eventos_por_dia = eventos_df.groupby(eventos_df['Fecha'].dt.date).size()
        alertas_por_dia = alertas_df.groupby(alertas_df['Fecha Declarada'].dt.date).size()
        
        # Combinar en un DataFrame
        correlacion_df = pd.DataFrame({
            'Eventos': eventos_por_dia,
            'Alertas': alertas_por_dia
        }).fillna(0)
        
        # Gráfico de correlación temporal
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Eventos por Día', 'Alertas por Día'),
            shared_xaxes=True
        )
        
        fig.add_trace(
            go.Scatter(
                x=correlacion_df.index,
                y=correlacion_df['Eventos'],
                mode='lines+markers',
                name='Eventos',
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=correlacion_df.index,
                y=correlacion_df['Alertas'],
                mode='lines+markers',
                name='Alertas',
                line=dict(color='blue')
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Correlación Temporal: Eventos vs Alertas",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Calcular coeficiente de correlación
        if len(correlacion_df) > 1:
            correlacion_coef = correlacion_df['Eventos'].corr(correlacion_df['Alertas'])
            st.metric(
                "Coeficiente de Correlación",
                f"{correlacion_coef:.3f}",
                help="Correlación entre -1 y 1. Valores cercanos a 1 indican correlación positiva fuerte."
            )

def create_velocity_analysis(eventos_df: pd.DataFrame):
    """
    Crear análisis de velocidades de eventos
    
    Args:
        eventos_df (pd.DataFrame): DataFrame de eventos geotécnicos
    """
    
    velocity_columns = [
        'Velocidad Promedio (mm/h)',
        'Velocidad Máxima Últimas 12hrs. (mm/h)',
        'Velocidad Anterior a Velocidad Máxima (mm/h)'
    ]
    
    available_columns = [col for col in velocity_columns if col in eventos_df.columns]
    
    if available_columns:
        st.subheader("🚀 Análisis de Velocidades")
        
        # Distribución de velocidades
        fig = make_subplots(
            rows=1, cols=len(available_columns),
            subplot_titles=available_columns
        )
        
        for i, col in enumerate(available_columns):
            velocidades = eventos_df[col].dropna()
            
            fig.add_trace(
                go.Histogram(
                    x=velocidades,
                    name=col.replace(' (mm/h)', ''),
                    nbinsx=20
                ),
                row=1, col=i+1
            )
        
        fig.update_layout(
            title="Distribución de Velocidades",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estadísticas de velocidades
        st.subheader("📊 Estadísticas de Velocidades")
        
        stats_data = []
        for col in available_columns:
            velocidades = eventos_df[col].dropna()
            if len(velocidades) > 0:
                stats_data.append({
                    'Tipo': col.replace(' (mm/h)', ''),
                    'Promedio': f"{velocidades.mean():.2f}",
                    'Máximo': f"{velocidades.max():.2f}",
                    'Mínimo': f"{velocidades.min():.2f}",
                    'Desv. Estándar': f"{velocidades.std():.2f}"
                })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True)
