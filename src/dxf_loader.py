"""
Módulo para cargar y procesar archivos DXF para visualización geotécnica
Extrae líneas, polígonos, puntos y texto de archivos DXF de AutoCAD

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

import ezdxf
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DXFLoader:
    """
    Clase para cargar y procesar archivos DXF
    """
    
    def __init__(self):
        """
        Inicializar el cargador DXF
        """
        self.doc = None
        self.layers_data = {}
        self.bounds = None
        
    def load_dxf_file(self, file_path: str) -> bool:
        """
        Cargar archivo DXF desde ruta
        
        Args:
            file_path (str): Ruta al archivo DXF
            
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario
        """
        try:
            self.doc = ezdxf.readfile(file_path)
            logger.info(f"Archivo DXF cargado exitosamente: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error al cargar archivo DXF: {e}")
            st.error(f"Error al cargar archivo DXF: {e}")
            return False
    
    def load_dxf_from_bytes(self, file_bytes: bytes, filename: str) -> bool:
        """
        Cargar archivo DXF desde bytes (para Streamlit file uploader)
        
        Args:
            file_bytes (bytes): Contenido del archivo DXF
            filename (str): Nombre del archivo
            
        Returns:
            bool: True si se cargó exitosamente, False en caso contrario
        """
        try:
            # Crear archivo temporal
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name
            
            # Cargar desde archivo temporal
            success = self.load_dxf_file(tmp_file_path)
            
            # Limpiar archivo temporal
            os.unlink(tmp_file_path)
            
            if success:
                logger.info(f"Archivo DXF cargado desde bytes: {filename}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error al cargar archivo DXF desde bytes: {e}")
            st.error(f"Error al cargar archivo DXF: {e}")
            return False
    
    def get_layers_info(self) -> Dict[str, Dict]:
        """
        Obtener información de todas las capas del DXF
        
        Returns:
            Dict: Información de capas con conteos de entidades
        """
        if not self.doc:
            return {}
        
        layers_info = {}
        
        try:
            # Obtener información de capas
            for layer in self.doc.layers:
                layers_info[layer.dxf.name] = {
                    'name': layer.dxf.name,
                    'color': getattr(layer.dxf, 'color', 7),  # Color por defecto
                    'visible': not layer.is_off(),
                    'frozen': layer.is_frozen(),
                    'entities_count': 0
                }
            
            # Contar entidades por capa
            msp = self.doc.modelspace()
            for entity in msp:
                layer_name = entity.dxf.layer
                if layer_name in layers_info:
                    layers_info[layer_name]['entities_count'] += 1
                    
        except Exception as e:
            logger.error(f"Error al obtener información de capas: {e}")
            
        return layers_info
    
    def extract_lines(self, selected_layers: List[str] = None) -> pd.DataFrame:
        """
        Extraer líneas del archivo DXF
        
        Args:
            selected_layers (List[str]): Capas a procesar (None para todas)
            
        Returns:
            pd.DataFrame: DataFrame con líneas extraídas
        """
        if not self.doc:
            return pd.DataFrame()
        
        lines_data = []
        
        try:
            msp = self.doc.modelspace()
            
            for entity in msp.query('LINE'):
                layer_name = entity.dxf.layer
                
                # Filtrar por capas seleccionadas
                if selected_layers and layer_name not in selected_layers:
                    continue
                
                start_point = entity.dxf.start
                end_point = entity.dxf.end
                
                lines_data.append({
                    'layer': layer_name,
                    'type': 'LINE',
                    'start_x': start_point.x,
                    'start_y': start_point.y,
                    'start_z': getattr(start_point, 'z', 0),
                    'end_x': end_point.x,
                    'end_y': end_point.y,
                    'end_z': getattr(end_point, 'z', 0),
                    'color': getattr(entity.dxf, 'color', 256),  # 256 = BYLAYER
                    'length': (end_point - start_point).magnitude
                })
                
        except Exception as e:
            logger.error(f"Error al extraer líneas: {e}")
        
        return pd.DataFrame(lines_data)
    
    def extract_polylines(self, selected_layers: List[str] = None) -> pd.DataFrame:
        """
        Extraer polilíneas del archivo DXF
        
        Args:
            selected_layers (List[str]): Capas a procesar (None para todas)
            
        Returns:
            pd.DataFrame: DataFrame con polilíneas extraídas
        """
        if not self.doc:
            return pd.DataFrame()
        
        polylines_data = []
        
        try:
            msp = self.doc.modelspace()
            
            # Procesar LWPOLYLINE (Lightweight Polyline)
            for entity in msp.query('LWPOLYLINE'):
                layer_name = entity.dxf.layer
                
                if selected_layers and layer_name not in selected_layers:
                    continue
                
                points = []
                for point in entity.get_points():
                    points.append([point[0], point[1]])
                
                if len(points) >= 2:
                    polylines_data.append({
                        'layer': layer_name,
                        'type': 'LWPOLYLINE',
                        'points': points,
                        'closed': entity.closed,
                        'color': getattr(entity.dxf, 'color', 256),
                        'vertices_count': len(points)
                    })
            
            # Procesar POLYLINE (Polyline 3D)
            for entity in msp.query('POLYLINE'):
                layer_name = entity.dxf.layer
                
                if selected_layers and layer_name not in selected_layers:
                    continue
                
                points = []
                for vertex in entity.vertices:
                    point = vertex.dxf.location
                    points.append([point.x, point.y, getattr(point, 'z', 0)])
                
                if len(points) >= 2:
                    polylines_data.append({
                        'layer': layer_name,
                        'type': 'POLYLINE',
                        'points': points,
                        'closed': entity.is_closed,
                        'color': getattr(entity.dxf, 'color', 256),
                        'vertices_count': len(points)
                    })
                    
        except Exception as e:
            logger.error(f"Error al extraer polilíneas: {e}")
        
        return pd.DataFrame(polylines_data)
    
    def extract_circles(self, selected_layers: List[str] = None) -> pd.DataFrame:
        """
        Extraer círculos del archivo DXF
        
        Args:
            selected_layers (List[str]): Capas a procesar (None para todas)
            
        Returns:
            pd.DataFrame: DataFrame con círculos extraídos
        """
        if not self.doc:
            return pd.DataFrame()
        
        circles_data = []
        
        try:
            msp = self.doc.modelspace()
            
            for entity in msp.query('CIRCLE'):
                layer_name = entity.dxf.layer
                
                if selected_layers and layer_name not in selected_layers:
                    continue
                
                center = entity.dxf.center
                radius = entity.dxf.radius
                
                circles_data.append({
                    'layer': layer_name,
                    'type': 'CIRCLE',
                    'center_x': center.x,
                    'center_y': center.y,
                    'center_z': getattr(center, 'z', 0),
                    'radius': radius,
                    'color': getattr(entity.dxf, 'color', 256),
                    'area': np.pi * radius ** 2
                })
                
        except Exception as e:
            logger.error(f"Error al extraer círculos: {e}")
        
        return pd.DataFrame(circles_data)
    
    def extract_text(self, selected_layers: List[str] = None) -> pd.DataFrame:
        """
        Extraer texto del archivo DXF
        
        Args:
            selected_layers (List[str]): Capas a procesar (None para todas)
            
        Returns:
            pd.DataFrame: DataFrame con texto extraído
        """
        if not self.doc:
            return pd.DataFrame()
        
        text_data = []
        
        try:
            msp = self.doc.modelspace()
            
            # Procesar TEXT
            for entity in msp.query('TEXT'):
                layer_name = entity.dxf.layer
                
                if selected_layers and layer_name not in selected_layers:
                    continue
                
                insert_point = entity.dxf.insert
                
                text_data.append({
                    'layer': layer_name,
                    'type': 'TEXT',
                    'text': entity.dxf.text,
                    'x': insert_point.x,
                    'y': insert_point.y,
                    'z': getattr(insert_point, 'z', 0),
                    'height': entity.dxf.height,
                    'rotation': getattr(entity.dxf, 'rotation', 0),
                    'color': getattr(entity.dxf, 'color', 256)
                })
            
            # Procesar MTEXT (Multiline Text)
            for entity in msp.query('MTEXT'):
                layer_name = entity.dxf.layer
                
                if selected_layers and layer_name not in selected_layers:
                    continue
                
                insert_point = entity.dxf.insert
                
                text_data.append({
                    'layer': layer_name,
                    'type': 'MTEXT',
                    'text': entity.text,
                    'x': insert_point.x,
                    'y': insert_point.y,
                    'z': getattr(insert_point, 'z', 0),
                    'height': entity.dxf.char_height,
                    'rotation': getattr(entity.dxf, 'rotation', 0),
                    'color': getattr(entity.dxf, 'color', 256)
                })
                
        except Exception as e:
            logger.error(f"Error al extraer texto: {e}")
        
        return pd.DataFrame(text_data)
    
    def get_drawing_bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Obtener los límites del dibujo (bounding box)
        
        Returns:
            Tuple: (min_x, min_y, max_x, max_y) o None si hay error
        """
        if not self.doc:
            return None
        
        try:
            # Extraer todas las entidades para calcular bounds
            lines_df = self.extract_lines()
            polylines_df = self.extract_polylines()
            circles_df = self.extract_circles()
            
            all_x = []
            all_y = []
            
            # Agregar puntos de líneas
            if not lines_df.empty:
                all_x.extend(lines_df['start_x'].tolist())
                all_x.extend(lines_df['end_x'].tolist())
                all_y.extend(lines_df['start_y'].tolist())
                all_y.extend(lines_df['end_y'].tolist())
            
            # Agregar puntos de círculos
            if not circles_df.empty:
                for _, circle in circles_df.iterrows():
                    all_x.extend([circle['center_x'] - circle['radius'], 
                                 circle['center_x'] + circle['radius']])
                    all_y.extend([circle['center_y'] - circle['radius'], 
                                 circle['center_y'] + circle['radius']])
            
            # Agregar puntos de polilíneas
            if not polylines_df.empty:
                for _, polyline in polylines_df.iterrows():
                    points = polyline['points']
                    if isinstance(points, list):
                        for point in points:
                            if len(point) >= 2:
                                all_x.append(point[0])
                                all_y.append(point[1])
            
            if all_x and all_y:
                return (min(all_x), min(all_y), max(all_x), max(all_y))
            
        except Exception as e:
            logger.error(f"Error al calcular límites del dibujo: {e}")
        
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen del archivo DXF cargado
        
        Returns:
            Dict: Resumen con estadísticas del archivo
        """
        if not self.doc:
            return {}
        
        try:
            layers_info = self.get_layers_info()
            lines_df = self.extract_lines()
            polylines_df = self.extract_polylines()
            circles_df = self.extract_circles()
            text_df = self.extract_text()
            bounds = self.get_drawing_bounds()
            
            summary = {
                'layers_count': len(layers_info),
                'layers': list(layers_info.keys()),
                'entities': {
                    'lines': len(lines_df),
                    'polylines': len(polylines_df),
                    'circles': len(circles_df),
                    'text': len(text_df)
                },
                'total_entities': len(lines_df) + len(polylines_df) + len(circles_df) + len(text_df),
                'bounds': bounds,
                'drawing_size': None
            }
            
            if bounds:
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                summary['drawing_size'] = {'width': width, 'height': height}
            
            return summary
            
        except Exception as e:
            logger.error(f"Error al generar resumen: {e}")
            return {}
