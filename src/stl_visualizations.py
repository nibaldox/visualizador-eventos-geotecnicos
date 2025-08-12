"""
Módulo de visualización para archivos STL

Provee funciones para visualizar mallas 3D STL con Plotly, y métricas en Streamlit.
"""

from typing import Optional
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from .stl_loader import STLLoader


def create_stl_mesh_figure(stl_loader: STLLoader, color: str = "#8c564b", opacity: float = 0.8) -> go.Figure:
    """
    Crear una figura 3D de Plotly a partir de un STLLoader.
    """
    fig = go.Figure()

    if stl_loader.vertices is None or stl_loader.faces is None:
        return fig

    x = stl_loader.vertices[:, 0]
    y = stl_loader.vertices[:, 1]
    z = stl_loader.vertices[:, 2]
    i = stl_loader.faces[:, 0]
    j = stl_loader.faces[:, 1]
    k = stl_loader.faces[:, 2]

    mesh3d = go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        flatshading=True,
        name="Malla STL",
        hovertemplate="<b>Vértice</b><br>x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}<extra></extra>",
    )

    fig.add_trace(mesh3d)

    # Configuración de escena: ejes en metros y aspecto cúbico
    fig.update_layout(
        title="Malla STL",
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
        ),
        height=700,
        showlegend=False,
    )

    return fig


def render_stl_metrics(stl_loader: STLLoader) -> None:
    """Mostrar métricas claves de la malla STL en Streamlit."""
    summary = stl_loader.get_summary()
    if not summary:
        st.warning("No hay métricas disponibles del STL")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vértices", f"{summary['vertices_count']:,}")
    with col2:
        st.metric("Caras", f"{summary['faces_count']:,}")
    with col3:
        size = summary["size"]
        st.metric("Dimensiones", f"{size['width']:.1f}×{size['height']:.1f}×{size['depth']:.1f} m")
    with col4:
        if summary.get("surface_area") is not None:
            st.metric("Área Superficie", f"{summary['surface_area']:.1f} m²")
        else:
            st.metric("Área Superficie", "N/D")

    # Centro de gravedad y volumen si están
    extra_cols = st.columns(2)
    with extra_cols[0]:
        cog = summary.get("center_of_gravity")
        if cog:
            st.write(f"**Centro de Gravedad**: ({cog[0]:.2f}, {cog[1]:.2f}, {cog[2]:.2f}) m")
        else:
            st.write("**Centro de Gravedad**: N/D")
    with extra_cols[1]:
        volume = summary.get("volume")
        if volume is not None:
            st.write(f"**Volumen**: {volume:.1f} m³")
        else:
            st.write("**Volumen**: N/D")


