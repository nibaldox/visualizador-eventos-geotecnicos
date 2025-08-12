"""
Módulo para visualizar archivos DXF en el visualizador geotécnico
Integra datos DXF con eventos y alertas geotécnicas

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
from .dxf_loader import DXFLoader
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Colores por defecto para capas DXF
DEFAULT_LAYER_COLORS = {
    'default': '#808080',  # Gris
    '0': '#FFFFFF',        # Blanco
    'CONTOUR': '#8B4513',  # Marrón para contornos
    'ROADS': '#FFD700',    # Dorado para caminos
    'STRUCTURES': '#FF4500', # Rojo-naranja para estructuras
    'BOUNDARIES': '#32CD32', # Verde lima para límites
    'TEXT': '#000000',     # Negro para texto
    'DIMENSIONS': '#0000FF' # Azul para dimensiones
}

def get_layer_color(layer_name: str, color_code: int = 256) -> str:
    """
    Obtener color para una capa DXF
    
    Args:
        layer_name (str): Nombre de la capa
        color_code (int): Código de color DXF
        
    Returns:
        str: Color en formato hexadecimal
    """
    # Colores AutoCAD estándar (simplificados)
    autocad_colors = {
        1: '#FF0000',  # Rojo
        2: '#FFFF00',  # Amarillo
        3: '#00FF00',  # Verde
        4: '#00FFFF',  # Cian
        5: '#0000FF',  # Azul
        6: '#FF00FF',  # Magenta
        7: '#FFFFFF',  # Blanco
        8: '#808080',  # Gris
        9: '#C0C0C0'   # Gris claro
    }
    
    # Si es BYLAYER (256), usar color por nombre de capa
    if color_code == 256:
        return DEFAULT_LAYER_COLORS.get(layer_name.upper(), DEFAULT_LAYER_COLORS['default'])
    
    # Usar color AutoCAD si está disponible
    return autocad_colors.get(color_code, DEFAULT_LAYER_COLORS['default'])

def create_dxf_base_map(dxf_loader: DXFLoader, selected_layers: List[str] = None, 
                       show_lines: bool = True, show_polylines: bool = True, 
                       show_circles: bool = True, show_text: bool = False) -> go.Figure:
    """
    Crear mapa base con elementos DXF
    
    Args:
        dxf_loader (DXFLoader): Instancia del cargador DXF
        selected_layers (List[str]): Capas seleccionadas
        show_lines (bool): Mostrar líneas
        show_polylines (bool): Mostrar polilíneas
        show_circles (bool): Mostrar círculos
        show_text (bool): Mostrar texto
        
    Returns:
        go.Figure: Figura de Plotly con elementos DXF
    """
    fig = go.Figure()
    
    try:
        # Extraer líneas
        if show_lines:
            lines_df = dxf_loader.extract_lines(selected_layers)
            if not lines_df.empty:
                for layer in lines_df['layer'].unique():
                    layer_lines = lines_df[lines_df['layer'] == layer]
                    
                    # Crear trazas para líneas de esta capa
                    x_coords = []
                    y_coords = []
                    
                    for _, line in layer_lines.iterrows():
                        x_coords.extend([line['start_x'], line['end_x'], None])
                        y_coords.extend([line['start_y'], line['end_y'], None])
                    
                    color = get_layer_color(layer, layer_lines.iloc[0]['color'])
                    
                    fig.add_trace(go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        mode='lines',
                        name=f'Líneas - {layer}',
                        line=dict(color=color, width=1),
                        hovertemplate=f'<b>Capa:</b> {layer}<br>' +
                                    '<b>Tipo:</b> Línea<br>' +
                                    '<b>X:</b> %{x:.2f}<br>' +
                                    '<b>Y:</b> %{y:.2f}<extra></extra>',
                        legendgroup=f'dxf_{layer}'
                    ))
        
        # Extraer polilíneas
        if show_polylines:
            polylines_df = dxf_loader.extract_polylines(selected_layers)
            if not polylines_df.empty:
                for layer in polylines_df['layer'].unique():
                    layer_polylines = polylines_df[polylines_df['layer'] == layer]
                    
                    for idx, polyline in layer_polylines.iterrows():
                        points = polyline['points']
                        if isinstance(points, list) and len(points) >= 2:
                            x_coords = [p[0] for p in points]
                            y_coords = [p[1] for p in points]
                            
                            # Cerrar polilínea si es necesaria
                            if polyline['closed'] and len(points) > 2:
                                x_coords.append(points[0][0])
                                y_coords.append(points[0][1])
                            
                            color = get_layer_color(layer, polyline['color'])
                            
                            fig.add_trace(go.Scatter(
                                x=x_coords,
                                y=y_coords,
                                mode='lines',
                                name=f'Polilínea - {layer}',
                                line=dict(color=color, width=2),
                                hovertemplate=f'<b>Capa:</b> {layer}<br>' +
                                            '<b>Tipo:</b> Polilínea<br>' +
                                            f'<b>Vértices:</b> {len(points)}<br>' +
                                            '<b>X:</b> %{x:.2f}<br>' +
                                            '<b>Y:</b> %{y:.2f}<extra></extra>',
                                legendgroup=f'dxf_{layer}',
                                showlegend=(idx == 0)  # Solo mostrar leyenda para el primer elemento
                            ))
        
        # Extraer círculos
        if show_circles:
            circles_df = dxf_loader.extract_circles(selected_layers)
            if not circles_df.empty:
                for layer in circles_df['layer'].unique():
                    layer_circles = circles_df[circles_df['layer'] == layer]
                    
                    for idx, circle in layer_circles.iterrows():
                        # Generar puntos del círculo
                        theta = np.linspace(0, 2*np.pi, 50)
                        x_circle = circle['center_x'] + circle['radius'] * np.cos(theta)
                        y_circle = circle['center_y'] + circle['radius'] * np.sin(theta)
                        
                        color = get_layer_color(layer, circle['color'])
                        
                        fig.add_trace(go.Scatter(
                            x=x_circle,
                            y=y_circle,
                            mode='lines',
                            name=f'Círculos - {layer}',
                            line=dict(color=color, width=1),
                            fill='none',
                            hovertemplate=f'<b>Capa:</b> {layer}<br>' +
                                        '<b>Tipo:</b> Círculo<br>' +
                                        f'<b>Centro:</b> ({circle["center_x"]:.2f}, {circle["center_y"]:.2f})<br>' +
                                        f'<b>Radio:</b> {circle["radius"]:.2f}<br>' +
                                        '<b>X:</b> %{x:.2f}<br>' +
                                        '<b>Y:</b> %{y:.2f}<extra></extra>',
                            legendgroup=f'dxf_{layer}',
                            showlegend=(idx == 0)
                        ))
        
        # Extraer texto
        if show_text:
            text_df = dxf_loader.extract_text(selected_layers)
            if not text_df.empty:
                for layer in text_df['layer'].unique():
                    layer_text = text_df[text_df['layer'] == layer]
                    
                    color = get_layer_color(layer, layer_text.iloc[0]['color'])
                    
                    fig.add_trace(go.Scatter(
                        x=layer_text['x'],
                        y=layer_text['y'],
                        mode='markers+text',
                        name=f'Texto - {layer}',
                        text=layer_text['text'],
                        textposition='middle center',
                        textfont=dict(color=color, size=8),
                        marker=dict(color=color, size=4, symbol='circle'),
                        hovertemplate='<b>Capa:</b> ' + layer + '<br>' +
                                    '<b>Tipo:</b> Texto<br>' +
                                    '<b>Texto:</b> %{text}<br>' +
                                    '<b>X:</b> %{x:.2f}<br>' +
                                    '<b>Y:</b> %{y:.2f}<extra></extra>',
                        legendgroup=f'dxf_{layer}'
                    ))
        
        # Configurar layout
        fig.update_layout(
            title='Mapa Base DXF',
            xaxis_title='Este (m)',
            yaxis_title='Norte (m)',
            showlegend=True,
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Mantener aspecto 1:1
        fig.update_yaxis(scaleanchor="x", scaleratio=1)
        # Grilla fija cada 500 m (gris muy suave)
        fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
        fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
        
    except Exception as e:
        logger.error(f"Error al crear mapa base DXF: {e}")
        st.error(f"Error al crear visualización DXF: {e}")
    
    return fig

def create_dxf_with_events_map(dxf_loader: DXFLoader, eventos_df: pd.DataFrame, 
                              alertas_df: pd.DataFrame = None, 
                              selected_layers: List[str] = None,
                              show_dxf_elements: Dict[str, bool] = None) -> go.Figure:
    """
    Crear mapa combinado con elementos DXF y datos geotécnicos
    
    Args:
        dxf_loader (DXFLoader): Instancia del cargador DXF
        eventos_df (pd.DataFrame): DataFrame de eventos
        alertas_df (pd.DataFrame): DataFrame de alertas (opcional)
        selected_layers (List[str]): Capas DXF seleccionadas
        show_dxf_elements (Dict[str, bool]): Elementos DXF a mostrar
        
    Returns:
        go.Figure: Figura combinada
    """
    if show_dxf_elements is None:
        show_dxf_elements = {
            'lines': True,
            'polylines': True,
            'circles': True,
            'text': False
        }
    
    # Crear mapa base DXF
    fig = create_dxf_base_map(
        dxf_loader, 
        selected_layers,
        show_lines=show_dxf_elements.get('lines', True),
        show_polylines=show_dxf_elements.get('polylines', True),
        show_circles=show_dxf_elements.get('circles', True),
        show_text=show_dxf_elements.get('text', False)
    )
    
    try:
        # Agregar eventos geotécnicos
        if not eventos_df.empty and 'Este' in eventos_df.columns and 'Norte' in eventos_df.columns:
            fig.add_trace(go.Scatter(
                x=eventos_df['Este'],
                y=eventos_df['Norte'],
                mode='markers',
                name='Eventos Geotécnicos',
                marker=dict(
                    color='red',
                    size=8,
                    symbol='circle',
                    line=dict(color='darkred', width=1)
                ),
                hovertemplate='<b>Evento Geotécnico</b><br>' +
                            '<b>Este:</b> %{x:.2f}<br>' +
                            '<b>Norte:</b> %{y:.2f}<br>' +
                            '<b>Fecha:</b> %{customdata[0]}<br>' +
                            '<b>Zona:</b> %{customdata[1]}<extra></extra>',
                customdata=eventos_df[['Fecha', 'Zona']].values if 'Fecha' in eventos_df.columns and 'Zona' in eventos_df.columns else None,
                legendgroup='geotechnical_data'
            ))
        
        # Agregar alertas si están disponibles
        if alertas_df is not None and not alertas_df.empty and 'Este' in alertas_df.columns and 'Norte' in alertas_df.columns:
            # Alertas abiertas
            alertas_abiertas = alertas_df[alertas_df['Estado'] == 'Abierta'] if 'Estado' in alertas_df.columns else alertas_df
            if not alertas_abiertas.empty:
                fig.add_trace(go.Scatter(
                    x=alertas_abiertas['Este'],
                    y=alertas_abiertas['Norte'],
                    mode='markers',
                    name='Alertas Abiertas',
                    marker=dict(
                        color='yellow',
                        size=6,
                        symbol='triangle-up',
                        line=dict(color='orange', width=1)
                    ),
                    hovertemplate='<b>Alerta Abierta</b><br>' +
                                '<b>Este:</b> %{x:.2f}<br>' +
                                '<b>Norte:</b> %{y:.2f}<br>' +
                                '<b>Fecha:</b> %{customdata[0]}<br>' +
                                '<b>Zona:</b> %{customdata[1]}<extra></extra>',
                    customdata=alertas_abiertas[['Fecha Inicio', 'Zona']].values if 'Fecha Inicio' in alertas_abiertas.columns and 'Zona' in alertas_abiertas.columns else None,
                    legendgroup='geotechnical_data'
                ))
            
            # Alertas cerradas
            alertas_cerradas = alertas_df[alertas_df['Estado'] == 'Cerrada'] if 'Estado' in alertas_df.columns else pd.DataFrame()
            if not alertas_cerradas.empty:
                fig.add_trace(go.Scatter(
                    x=alertas_cerradas['Este'],
                    y=alertas_cerradas['Norte'],
                    mode='markers',
                    name='Alertas Cerradas',
                    marker=dict(
                        color='green',
                        size=6,
                        symbol='triangle-down',
                        line=dict(color='darkgreen', width=1)
                    ),
                    hovertemplate='<b>Alerta Cerrada</b><br>' +
                                '<b>Este:</b> %{x:.2f}<br>' +
                                '<b>Norte:</b> %{y:.2f}<br>' +
                                '<b>Fecha:</b> %{customdata[0]}<br>' +
                                '<b>Zona:</b> %{customdata[1]}<extra></extra>',
                    customdata=alertas_cerradas[['Fecha Inicio', 'Zona']].values if 'Fecha Inicio' in alertas_cerradas.columns and 'Zona' in alertas_cerradas.columns else None,
                    legendgroup='geotechnical_data'
                ))
        
        # Actualizar título
        fig.update_layout(
            title='Mapa Integrado: DXF + Datos Geotécnicos',
            xaxis_title='Este (m)',
            yaxis_title='Norte (m)',
            showlegend=True,
            hovermode='closest'
        )
        # Grilla fija cada 500 m (gris muy suave) y aspecto 1:1 ya definido en base map
        fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
        fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", gridwidth=0.5, dtick=500)
        
    except Exception as e:
        logger.error(f"Error al crear mapa integrado: {e}")
        st.error(f"Error al integrar datos con DXF: {e}")
    
    return fig

def create_dxf_layers_summary(dxf_loader: DXFLoader) -> pd.DataFrame:
    """
    Crear resumen de capas DXF para mostrar en tabla
    
    Args:
        dxf_loader (DXFLoader): Instancia del cargador DXF
        
    Returns:
        pd.DataFrame: Resumen de capas
    """
    try:
        layers_info = dxf_loader.get_layers_info()
        
        if not layers_info:
            return pd.DataFrame()
        
        summary_data = []
        for layer_name, info in layers_info.items():
            summary_data.append({
                'Capa': layer_name,
                'Entidades': info['entities_count'],
                'Visible': '✓' if info['visible'] else '✗',
                'Congelada': '✓' if info['frozen'] else '✗',
                'Color': info['color']
            })
        
        return pd.DataFrame(summary_data)
        
    except Exception as e:
        logger.error(f"Error al crear resumen de capas: {e}")
        return pd.DataFrame()

def create_dxf_statistics_chart(dxf_loader: DXFLoader) -> go.Figure:
    """
    Crear gráfico de estadísticas del archivo DXF
    
    Args:
        dxf_loader (DXFLoader): Instancia del cargador DXF
        
    Returns:
        go.Figure: Gráfico de barras con estadísticas
    """
    try:
        summary = dxf_loader.get_summary()
        
        if not summary or 'entities' not in summary:
            return go.Figure()
        
        entities = summary['entities']
        
        # Crear gráfico de barras
        fig = go.Figure(data=[
            go.Bar(
                x=list(entities.keys()),
                y=list(entities.values()),
                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'],
                text=list(entities.values()),
                textposition='auto',
                hovertemplate='<b>Tipo:</b> %{x}<br>' +
                            '<b>Cantidad:</b> %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f'Estadísticas del Archivo DXF<br><sub>Total: {summary.get("total_entities", 0)} entidades en {summary.get("layers_count", 0)} capas</sub>',
            xaxis_title='Tipo de Entidad',
            yaxis_title='Cantidad',
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error al crear gráfico de estadísticas: {e}")
        return go.Figure()
