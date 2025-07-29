"""
Módulo de utilidades para el visualizador de eventos geotécnicos
Contiene funciones auxiliares para formateo, validación y procesamiento de datos

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple, List
import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def format_date(date_input: Union[str, datetime, pd.Timestamp], format_type: str = "display") -> str:
    """
    Formatear fechas para visualización
    
    Args:
        date_input: Fecha a formatear (string, datetime o Timestamp)
        format_type: Tipo de formato ("display", "filename", "iso")
        
    Returns:
        str: Fecha formateada como string
    """
    try:
        if pd.isna(date_input) or date_input is None:
            return "N/A"
        
        # Convertir a datetime si es necesario
        if isinstance(date_input, str):
            date_obj = pd.to_datetime(date_input)
        elif isinstance(date_input, (datetime, pd.Timestamp)):
            date_obj = date_input
        else:
            return "N/A"
        
        # Aplicar formato según el tipo (formato chileno dd/mm/aaaa)
        if format_type == "display":
            return date_obj.strftime("%d/%m/%Y %H:%M")
        elif format_type == "filename":
            return date_obj.strftime("%Y%m%d_%H%M%S")
        elif format_type == "iso":
            return date_obj.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "date_only":
            return date_obj.strftime("%d/%m/%Y")
        else:
            return date_obj.strftime("%d/%m/%Y")
            
    except Exception as e:
        logger.warning(f"Error al formatear fecha {date_input}: {str(e)}")
        return "N/A"

def validate_coordinates(este: float, norte: float) -> bool:
    """
    Validar si las coordenadas son válidas
    
    Args:
        este (float): Coordenada Este (X)
        norte (float): Coordenada Norte (Y)
        
    Returns:
        bool: True si las coordenadas son válidas
    """
    try:
        # Verificar que no sean NaN o None
        if pd.isna(este) or pd.isna(norte) or este is None or norte is None:
            return False
        
        # Verificar que sean números
        if not isinstance(este, (int, float)) or not isinstance(norte, (int, float)):
            return False
        
        # Verificar rangos razonables (ajustar según la ubicación de la mina)
        # Estos rangos son aproximados para coordenadas UTM en Chile
        if not (200000 <= este <= 800000):
            return False
        
        if not (6000000 <= norte <= 8000000):
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error al validar coordenadas ({este}, {norte}): {str(e)}")
        return False

def clean_numeric_column(series: pd.Series) -> pd.Series:
    """
    Limpiar y convertir una serie a valores numéricos
    
    Args:
        series (pd.Series): Serie a limpiar
        
    Returns:
        pd.Series: Serie con valores numéricos limpios
    """
    try:
        # Convertir a string primero para limpiar
        cleaned = series.astype(str)
        
        # Remover caracteres no numéricos excepto punto, coma y signo negativo
        cleaned = cleaned.str.replace(r'[^\d.,-]', '', regex=True)
        
        # Reemplazar comas por puntos para decimales
        cleaned = cleaned.str.replace(',', '.')
        
        # Convertir a numérico
        cleaned = pd.to_numeric(cleaned, errors='coerce')
        
        return cleaned
        
    except Exception as e:
        logger.warning(f"Error al limpiar columna numérica: {str(e)}")
        return series

def calculate_distance(este1: float, norte1: float, este2: float, norte2: float) -> float:
    """
    Calcular distancia euclidiana entre dos puntos
    
    Args:
        este1, norte1: Coordenadas del primer punto
        este2, norte2: Coordenadas del segundo punto
        
    Returns:
        float: Distancia en metros
    """
    try:
        if not all(validate_coordinates(e, n) for e, n in [(este1, norte1), (este2, norte2)]):
            return np.nan
        
        distance = np.sqrt((este2 - este1)**2 + (norte2 - norte1)**2)
        return distance
        
    except Exception as e:
        logger.warning(f"Error al calcular distancia: {str(e)}")
        return np.nan

def categorize_velocity(velocity: float) -> str:
    """
    Categorizar velocidad según rangos de riesgo
    
    Args:
        velocity (float): Velocidad en mm/h
        
    Returns:
        str: Categoría de riesgo
    """
    try:
        if pd.isna(velocity) or velocity is None:
            return "No definido"
        
        if velocity < 0.1:
            return "Muy Bajo"
        elif velocity < 1.0:
            return "Bajo"
        elif velocity < 5.0:
            return "Moderado"
        elif velocity < 20.0:
            return "Alto"
        else:
            return "Muy Alto"
            
    except Exception as e:
        logger.warning(f"Error al categorizar velocidad {velocity}: {str(e)}")
        return "No definido"

def categorize_volume(volume: float) -> str:
    """
    Categorizar volumen según rangos de magnitud
    
    Args:
        volume (float): Volumen en toneladas
        
    Returns:
        str: Categoría de magnitud
    """
    try:
        if pd.isna(volume) or volume is None:
            return "No definido"
        
        if volume < 100:
            return "Pequeño"
        elif volume < 1000:
            return "Mediano"
        elif volume < 10000:
            return "Grande"
        else:
            return "Muy Grande"
            
    except Exception as e:
        logger.warning(f"Error al categorizar volumen {volume}: {str(e)}")
        return "No definido"

def generate_event_summary(evento: pd.Series) -> str:
    """
    Generar resumen textual de un evento
    
    Args:
        evento (pd.Series): Serie con datos del evento
        
    Returns:
        str: Resumen del evento
    """
    try:
        summary_parts = []
        
        # ID y tipo
        event_id = evento.get('id', 'N/A')
        event_type = evento.get('Tipo', 'N/A')
        summary_parts.append(f"Evento {event_id} - {event_type}")
        
        # Fecha
        fecha = evento.get('Fecha')
        if pd.notna(fecha):
            fecha_str = format_date(fecha, "display")
            summary_parts.append(f"Fecha: {fecha_str}")
        
        # Zona y ubicación
        zona = evento.get('Zona monitoreo', 'N/A')
        pared = evento.get('Pared', 'N/A')
        summary_parts.append(f"Ubicación: {zona} - {pared}")
        
        # Volumen
        volumen = evento.get('Volumen (ton)')
        if pd.notna(volumen):
            vol_category = categorize_volume(volumen)
            summary_parts.append(f"Volumen: {volumen:,.0f} ton ({vol_category})")
        
        # Velocidad máxima
        vel_max = evento.get('Velocidad Máxima Últimas 12hrs. (mm/h)')
        if pd.notna(vel_max):
            vel_category = categorize_velocity(vel_max)
            summary_parts.append(f"Vel. Máx: {vel_max:.2f} mm/h ({vel_category})")
        
        # Detección
        detectado = evento.get('Detectado por Sistema', 'N/A')
        if detectado == 'Si':
            radar = evento.get('Radar Principal', 'N/A')
            summary_parts.append(f"Detectado por: {radar}")
        
        return " | ".join(summary_parts)
        
    except Exception as e:
        logger.warning(f"Error al generar resumen de evento: {str(e)}")
        return f"Evento {evento.get('id', 'N/A')} - Error en resumen"

def generate_alert_summary(alerta: pd.Series) -> str:
    """
    Generar resumen textual de una alerta
    
    Args:
        alerta (pd.Series): Serie con datos de la alerta
        
    Returns:
        str: Resumen de la alerta
    """
    try:
        summary_parts = []
        
        # ID y estatus
        alert_id = alerta.get('id', 'N/A')
        estatus = alerta.get('Estatus', 'N/A')
        summary_parts.append(f"Alerta {alert_id} - {estatus}")
        
        # Estado
        estado = alerta.get('Estado', 'N/A')
        summary_parts.append(f"Estado: {estado}")
        
        # Fecha
        fecha = alerta.get('Fecha Declarada')
        if pd.notna(fecha):
            fecha_str = format_date(fecha, "display")
            summary_parts.append(f"Declarada: {fecha_str}")
        
        # Zona
        zona = alerta.get('Zona de Monitoreo', 'N/A')
        summary_parts.append(f"Zona: {zona}")
        
        # Velocidad
        vel_max = alerta.get('Velocidad Máxima Últimas 12 hrs. (mm/h)')
        if pd.notna(vel_max):
            vel_category = categorize_velocity(vel_max)
            summary_parts.append(f"Vel. Máx: {vel_max:.2f} mm/h ({vel_category})")
        
        # Vigilante
        vigilante = alerta.get('Vigilante', 'N/A')
        if vigilante != 'N/A':
            summary_parts.append(f"Vigilante: {vigilante}")
        
        return " | ".join(summary_parts)
        
    except Exception as e:
        logger.warning(f"Error al generar resumen de alerta: {str(e)}")
        return f"Alerta {alerta.get('id', 'N/A')} - Error en resumen"

def filter_by_date_range(df: pd.DataFrame, date_column: str, 
                        start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Filtrar DataFrame por rango de fechas
    
    Args:
        df (pd.DataFrame): DataFrame a filtrar
        date_column (str): Nombre de la columna de fecha
        start_date (datetime): Fecha de inicio
        end_date (datetime): Fecha de fin
        
    Returns:
        pd.DataFrame: DataFrame filtrado
    """
    try:
        if date_column not in df.columns:
            logger.warning(f"Columna {date_column} no encontrada en DataFrame")
            return df
        
        # Convertir fechas a datetime si es necesario
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # Aplicar filtro
        mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
        filtered_df = df[mask].copy()
        
        return filtered_df
        
    except Exception as e:
        logger.warning(f"Error al filtrar por fechas: {str(e)}")
        return df

def export_to_excel(dataframes: dict, filename: str) -> bool:
    """
    Exportar múltiples DataFrames a un archivo Excel
    
    Args:
        dataframes (dict): Diccionario con nombre_hoja: DataFrame
        filename (str): Nombre del archivo de salida
        
    Returns:
        bool: True si la exportación fue exitosa
    """
    try:
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Archivo Excel exportado exitosamente: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error al exportar Excel: {str(e)}")
        return False

def get_color_scale(values: List[float], color_scheme: str = "RdYlGn_r") -> List[str]:
    """
    Generar escala de colores para valores numéricos
    
    Args:
        values (List[float]): Lista de valores numéricos
        color_scheme (str): Esquema de colores de Plotly
        
    Returns:
        List[str]: Lista de colores en formato hex
    """
    try:
        import plotly.express as px
        
        # Normalizar valores entre 0 y 1
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return ['#1f77b4'] * len(values)  # Color único si todos los valores son iguales
        
        normalized = [(v - min_val) / (max_val - min_val) for v in values]
        
        # Obtener colores de la escala
        colors = px.colors.sample_colorscale(color_scheme, normalized)
        
        return colors
        
    except Exception as e:
        logger.warning(f"Error al generar escala de colores: {str(e)}")
        return ['#1f77b4'] * len(values)  # Color por defecto

def validate_data_quality(df: pd.DataFrame, required_columns: List[str]) -> dict:
    """
    Validar calidad de datos en un DataFrame
    
    Args:
        df (pd.DataFrame): DataFrame a validar
        required_columns (List[str]): Lista de columnas requeridas
        
    Returns:
        dict: Reporte de calidad de datos
    """
    try:
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_columns': [],
            'null_counts': {},
            'duplicate_rows': 0,
            'data_types': {},
            'quality_score': 0.0
        }
        
        # Verificar columnas faltantes
        report['missing_columns'] = [col for col in required_columns if col not in df.columns]
        
        # Contar valores nulos por columna
        report['null_counts'] = df.isnull().sum().to_dict()
        
        # Contar filas duplicadas
        report['duplicate_rows'] = df.duplicated().sum()
        
        # Tipos de datos
        report['data_types'] = df.dtypes.astype(str).to_dict()
        
        # Calcular score de calidad (0-100)
        total_cells = len(df) * len(df.columns)
        null_cells = sum(report['null_counts'].values())
        missing_col_penalty = len(report['missing_columns']) * 10
        duplicate_penalty = report['duplicate_rows'] * 2
        
        if total_cells > 0:
            completeness = (1 - null_cells / total_cells) * 100
            quality_score = max(0, completeness - missing_col_penalty - duplicate_penalty)
            report['quality_score'] = round(quality_score, 2)
        
        return report
        
    except Exception as e:
        logger.error(f"Error al validar calidad de datos: {str(e)}")
        return {'error': str(e)}

def create_backup_filename(base_name: str, extension: str = ".xlsx") -> str:
    """
    Crear nombre de archivo de respaldo con timestamp
    
    Args:
        base_name (str): Nombre base del archivo
        extension (str): Extensión del archivo
        
    Returns:
        str: Nombre de archivo con timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_backup_{timestamp}{extension}"
