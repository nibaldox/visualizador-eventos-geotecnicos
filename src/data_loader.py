"""
Módulo para cargar y procesar datos de eventos geotécnicos y alertas
Maneja la lectura de archivos Excel y validación de datos

Autor: Sistema de Análisis Geotécnico
Fecha: Julio 2025
"""

import pandas as pd
import os
import streamlit as st
from typing import Tuple, Optional
import logging
import warnings
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Clase para cargar y procesar datos de eventos geotécnicos y alertas de seguridad
    """
    
    def __init__(self, data_path: str = "data-input"):
        """
        Inicializar el cargador de datos
        
        Args:
            data_path (str): Ruta a la carpeta que contiene los archivos Excel
        """
        self.data_path = data_path
        self.eventos_file = "Listado de Eventos [2025.1 - 2025.22] - 07_07_2025.xlsx"
        self.alertas_file = "Listado de Alertas de Seguridad [2025.1 - 2025.95] - 07_07_2025.xlsx"
    
    def load_eventos(self) -> Optional[pd.DataFrame]:
        """
        Cargar datos de eventos geotécnicos desde archivo Excel
        
        Returns:
            pd.DataFrame: DataFrame con los datos de eventos o None si hay error
        """
        try:
            file_path = os.path.join(self.data_path, self.eventos_file)
            
            if not os.path.exists(file_path):
                logger.error(f"Archivo de eventos no encontrado: {file_path}")
                return None
            
            # Usar caché basado en mtime del archivo
            mtime = os.path.getmtime(file_path)

            @st.cache_data(show_spinner=False)
            def _read_excel_cached(path: str, ts: float) -> pd.DataFrame:
                return pd.read_excel(path)

            # Cargar datos
            df = _read_excel_cached(file_path, mtime)
            
            # Validar columnas esperadas
            expected_columns = [
                'id', 'Tipo', 'Vigilante', 'Fecha', 'Fecha UTC', 'Zona monitoreo',
                'Pared', 'Este', 'Norte', 'Cota', 'Alerta de Seguridad Asociada',
                'Tiempo de Activación (h)', 'Altura Banco (m)', 'Altura Falla (m)',
                'Desplazamiento Acumulado (mm)', 'Velocidad Promedio (mm/h)',
                'Velocidad Máxima Últimas 12hrs. (mm/h)', 
                'Velocidad Anterior a Velocidad Máxima (mm/h)',
                'Volumen (ton)', 'Detectado por Sistema', 'Radar Principal',
                'Mecanismos falla', 'Fotografía después del evento',
                'Gráfico de desplazamientos Vs. tiempo'
            ]
            
            # Verificar que las columnas principales existan
            missing_columns = [col for col in expected_columns[:10] if col not in df.columns]
            if missing_columns:
                logger.info(f"Columnas faltantes en eventos: {missing_columns}")
            
            # Procesar fechas (formato dd/mm/aaaa hh:mm)
            def parse_date_flexible(date_series):
                """Parsear fechas con múltiples formatos posibles"""
                if date_series.empty:
                    return date_series
                
                # Limpiar caracteres especiales y espacios extra
                cleaned_series = date_series.astype(str).str.strip()
                cleaned_series = cleaned_series.str.replace(r'^[^\d]', '', regex=True)  # Remover caracteres no numéricos al inicio
                
                # Intentar diferentes formatos
                formats_to_try = [
                    '%d/%m/%Y %H:%M',  # dd/mm/aaaa hh:mm
                    '%d/%m/%Y',        # dd/mm/aaaa
                    '%d-%m-%Y %H:%M',  # dd-mm-aaaa hh:mm
                    '%d-%m-%Y',        # dd-mm-aaaa
                ]
                
                result = pd.Series([pd.NaT] * len(cleaned_series), index=cleaned_series.index)
                
                for fmt in formats_to_try:
                    mask = result.isna()
                    if mask.any():
                        try:
                            result[mask] = pd.to_datetime(cleaned_series[mask], format=fmt, errors='coerce')
                        except:
                            continue
                
                # Si aún hay valores sin parsear, intentar formato automático
                mask = result.isna()
                if mask.any():
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        result[mask] = pd.to_datetime(cleaned_series[mask], errors='coerce', dayfirst=True, cache=True)
                
                return result
            
            if 'Fecha' in df.columns:
                df['Fecha'] = parse_date_flexible(df['Fecha'])
            
            if 'Fecha UTC' in df.columns:
                df['Fecha UTC'] = parse_date_flexible(df['Fecha UTC'])
            
            # Procesar coordenadas numéricas
            numeric_columns = ['Este', 'Norte', 'Cota', 'Altura Banco (m)', 
                             'Altura Falla (m)', 'Desplazamiento Acumulado (mm)',
                             'Velocidad Promedio (mm/h)', 'Volumen (ton)']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Eventos cargados exitosamente: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar eventos: {str(e)}")
            return None
    
    def load_alertas(self) -> Optional[pd.DataFrame]:
        """
        Cargar datos de alertas de seguridad desde archivo Excel
        
        Returns:
            pd.DataFrame: DataFrame con los datos de alertas o None si hay error
        """
        try:
            file_path = os.path.join(self.data_path, self.alertas_file)
            
            if not os.path.exists(file_path):
                logger.error(f"Archivo de alertas no encontrado: {file_path}")
                return None
            
            # Usar caché basado en mtime del archivo
            mtime = os.path.getmtime(file_path)

            @st.cache_data(show_spinner=False)
            def _read_excel_cached(path: str, ts: float) -> pd.DataFrame:
                return pd.read_excel(path)

            # Cargar datos
            df = _read_excel_cached(file_path, mtime)
            
            # Validar columnas esperadas
            expected_columns = [
                'id', 'Estatus', 'Vigilante', 'Fecha Declarada', 'Fecha Declarada UTC',
                'Evento', 'Comportamiento o Velocidad', 'Nivel de Exposición',
                'Versión Original', 'Zona de Monitoreo', 'Localización General',
                'Pared', 'Este', 'Norte', 'Cota', 'Observaciones', 'Estado',
                'Fecha de Cierre', 'Responsable de Cierre', 'Geotécnico Operativo',
                'Notificación Telefónica', 'Notificación por Correo',
                'Desplazamiento Últimas 12 hrs. (mm)',
                'Velocidad Promedio Últimas 12 hrs. (mm/h)',
                'Velocidad Máxima Últimas 12 hrs. (mm/h)'
            ]
            
            # Verificar que las columnas principales existan
            missing_columns = [col for col in expected_columns[:10] if col not in df.columns]
            if missing_columns:
                logger.info(f"Columnas faltantes en alertas: {missing_columns}")
            
            # Procesar fechas (formato dd/mm/aaaa hh:mm)
            def parse_date_flexible_alerts(date_series):
                """Parsear fechas con múltiples formatos posibles para alertas"""
                if date_series.empty:
                    return date_series
                
                # Limpiar caracteres especiales y espacios extra
                cleaned_series = date_series.astype(str).str.strip()
                cleaned_series = cleaned_series.str.replace(r'^[^\d]', '', regex=True)  # Remover caracteres no numéricos al inicio
                
                # Intentar diferentes formatos
                formats_to_try = [
                    '%d/%m/%Y %H:%M',  # dd/mm/aaaa hh:mm
                    '%d/%m/%Y',        # dd/mm/aaaa
                    '%d-%m-%Y %H:%M',  # dd-mm-aaaa hh:mm
                    '%d-%m-%Y',        # dd-mm-aaaa
                ]
                
                result = pd.Series([pd.NaT] * len(cleaned_series), index=cleaned_series.index)
                
                for fmt in formats_to_try:
                    mask = result.isna()
                    if mask.any():
                        try:
                            result[mask] = pd.to_datetime(cleaned_series[mask], format=fmt, errors='coerce')
                        except:
                            continue
                
                # Si aún hay valores sin parsear, intentar formato automático
                mask = result.isna()
                if mask.any():
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        result[mask] = pd.to_datetime(cleaned_series[mask], errors='coerce', dayfirst=True, cache=True)
                
                return result
            
            date_columns = ['Fecha Declarada', 'Fecha Declarada UTC', 'Fecha de Cierre']
            for col in date_columns:
                if col in df.columns:
                    df[col] = parse_date_flexible_alerts(df[col])
            
            # Procesar coordenadas numéricas
            numeric_columns = ['Este', 'Norte', 'Cota', 
                             'Desplazamiento Últimas 12 hrs. (mm)',
                             'Velocidad Promedio Últimas 12 hrs. (mm/h)',
                             'Velocidad Máxima Últimas 12 hrs. (mm/h)']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Alertas cargadas exitosamente: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar alertas: {str(e)}")
            return None

    def load_eventos_from_filelike(self, uploaded_file) -> Optional[pd.DataFrame]:
        """
        Cargar eventos desde un archivo subido (Excel/CSV/TXT) usando el uploader de Streamlit.

        Args:
            uploaded_file: Archivo subido (Streamlit UploadedFile)

        Returns:
            DataFrame procesado o None si hay error.
        """
        try:
            name = getattr(uploaded_file, 'name', 'uploaded')
            ext = Path(name).suffix.lower()

            # Leer según extensión
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(uploaded_file)
            elif ext in ['.csv']:
                df = pd.read_csv(uploaded_file)
            elif ext in ['.txt']:
                # Intento de inferencia de separador
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
            else:
                st.error(f"Extensión de archivo no soportada para eventos: {ext}")
                return None

            # Procesamiento similar a load_eventos
            expected_columns = [
                'id', 'Tipo', 'Vigilante', 'Fecha', 'Fecha UTC', 'Zona monitoreo',
                'Pared', 'Este', 'Norte', 'Cota', 'Alerta de Seguridad Asociada',
                'Tiempo de Activación (h)', 'Altura Banco (m)', 'Altura Falla (m)',
                'Desplazamiento Acumulado (mm)', 'Velocidad Promedio (mm/h)',
                'Velocidad Máxima Últimas 12hrs. (mm/h)', 
                'Velocidad Anterior a Velocidad Máxima (mm/h)',
                'Volumen (ton)', 'Detectado por Sistema', 'Radar Principal',
                'Mecanismos falla', 'Fotografía después del evento',
                'Gráfico de desplazamientos Vs. tiempo'
            ]

            missing_columns = [col for col in expected_columns[:10] if col not in df.columns]
            if missing_columns:
                logger.info(f"Columnas faltantes en eventos (upload): {missing_columns}")

            def parse_date_flexible(date_series):
                if date_series.empty:
                    return date_series
                cleaned_series = date_series.astype(str).str.strip()
                cleaned_series = cleaned_series.str.replace(r'^[^\d]', '', regex=True)
                formats_to_try = ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%d-%m-%Y %H:%M', '%d-%m-%Y']
                result = pd.Series([pd.NaT] * len(cleaned_series), index=cleaned_series.index)
                for fmt in formats_to_try:
                    mask = result.isna()
                    if mask.any():
                        try:
                            result[mask] = pd.to_datetime(cleaned_series[mask], format=fmt, errors='coerce')
                        except Exception:
                            continue
                mask = result.isna()
                if mask.any():
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        result[mask] = pd.to_datetime(cleaned_series[mask], errors='coerce', dayfirst=True, cache=True)
                return result

            if 'Fecha' in df.columns:
                df['Fecha'] = parse_date_flexible(df['Fecha'])
            if 'Fecha UTC' in df.columns:
                df['Fecha UTC'] = parse_date_flexible(df['Fecha UTC'])

            numeric_columns = ['Este', 'Norte', 'Cota', 'Altura Banco (m)', 
                             'Altura Falla (m)', 'Desplazamiento Acumulado (mm)',
                             'Velocidad Promedio (mm/h)', 'Volumen (ton)']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"Eventos (upload) cargados: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Error al cargar eventos desde upload: {str(e)}")
            st.error(f"Error al cargar eventos: {str(e)}")
            return None
    
    def load_all_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Cargar todos los datos (eventos y alertas)
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Tupla con DataFrames de eventos y alertas
        """
        eventos_df = self.load_eventos()
        alertas_df = self.load_alertas()
        
        return eventos_df, alertas_df

    def load_alertas_from_filelike(self, uploaded_file) -> Optional[pd.DataFrame]:
        """
        Cargar alertas desde archivo subido (Excel/CSV/TXT).

        Args:
            uploaded_file: Archivo subido de Streamlit

        Returns:
            DataFrame procesado o None si hay error.
        """
        try:
            name = getattr(uploaded_file, 'name', 'uploaded')
            ext = Path(name).suffix.lower()

            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(uploaded_file)
            elif ext in ['.csv']:
                df = pd.read_csv(uploaded_file)
            elif ext in ['.txt']:
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
            else:
                st.error(f"Extensión de archivo no soportada para alertas: {ext}")
                return None

            expected_columns = [
                'id', 'Estatus', 'Vigilante', 'Fecha Declarada', 'Fecha Declarada UTC',
                'Evento', 'Comportamiento o Velocidad', 'Nivel de Exposición',
                'Versión Original', 'Zona de Monitoreo', 'Localización General',
                'Pared', 'Este', 'Norte', 'Cota', 'Observaciones', 'Estado',
                'Fecha de Cierre', 'Responsable de Cierre', 'Geotécnico Operativo',
                'Notificación Telefónica', 'Notificación por Correo',
                'Desplazamiento Últimas 12 hrs. (mm)',
                'Velocidad Promedio Últimas 12 hrs. (mm/h)',
                'Velocidad Máxima Últimas 12 hrs. (mm/h)'
            ]
            missing_columns = [col for col in expected_columns[:10] if col not in df.columns]
            if missing_columns:
                logger.info(f"Columnas faltantes en alertas (upload): {missing_columns}")

            def parse_date_flexible_alerts(date_series):
                if date_series.empty:
                    return date_series
                cleaned_series = date_series.astype(str).str.strip()
                cleaned_series = cleaned_series.str.replace(r'^[^\d]', '', regex=True)
                formats_to_try = ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%d-%m-%Y %H:%M', '%d-%m-%Y']
                result = pd.Series([pd.NaT] * len(cleaned_series), index=cleaned_series.index)
                for fmt in formats_to_try:
                    mask = result.isna()
                    if mask.any():
                        try:
                            result[mask] = pd.to_datetime(cleaned_series[mask], format=fmt, errors='coerce')
                        except Exception:
                            continue
                mask = result.isna()
                if mask.any():
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        result[mask] = pd.to_datetime(cleaned_series[mask], errors='coerce', dayfirst=True, cache=True)
                return result

            for col in ['Fecha Declarada', 'Fecha Declarada UTC', 'Fecha de Cierre']:
                if col in df.columns:
                    df[col] = parse_date_flexible_alerts(df[col])

            numeric_columns = ['Este', 'Norte', 'Cota', 
                             'Desplazamiento Últimas 12 hrs. (mm)',
                             'Velocidad Promedio Últimas 12 hrs. (mm/h)',
                             'Velocidad Máxima Últimas 12 hrs. (mm/h)']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"Alertas (upload) cargadas: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Error al cargar alertas desde upload: {str(e)}")
            st.error(f"Error al cargar alertas: {str(e)}")
            return None
    
    def get_data_summary(self, eventos_df: pd.DataFrame, alertas_df: pd.DataFrame) -> dict:
        """
        Obtener resumen estadístico de los datos
        
        Args:
            eventos_df (pd.DataFrame): DataFrame de eventos
            alertas_df (pd.DataFrame): DataFrame de alertas
            
        Returns:
            dict: Diccionario con estadísticas resumidas
        """
        summary = {
            'eventos': {
                'total': len(eventos_df) if eventos_df is not None else 0,
                'fecha_min': eventos_df['Fecha'].min() if eventos_df is not None and 'Fecha' in eventos_df.columns else None,
                'fecha_max': eventos_df['Fecha'].max() if eventos_df is not None and 'Fecha' in eventos_df.columns else None,
                'zonas_unicas': eventos_df['Zona monitoreo'].nunique() if eventos_df is not None and 'Zona monitoreo' in eventos_df.columns else 0,
                'tipos_unicos': eventos_df['Tipo'].nunique() if eventos_df is not None and 'Tipo' in eventos_df.columns else 0
            },
            'alertas': {
                'total': len(alertas_df) if alertas_df is not None else 0,
                'fecha_min': alertas_df['Fecha Declarada'].min() if alertas_df is not None and 'Fecha Declarada' in alertas_df.columns else None,
                'fecha_max': alertas_df['Fecha Declarada'].max() if alertas_df is not None and 'Fecha Declarada' in alertas_df.columns else None,
                'estados_unicos': alertas_df['Estado'].nunique() if alertas_df is not None and 'Estado' in alertas_df.columns else 0,
                'estatus_unicos': alertas_df['Estatus'].nunique() if alertas_df is not None and 'Estatus' in alertas_df.columns else 0
            }
        }
        
        return summary
    
    def validate_data_integrity(self, eventos_df: pd.DataFrame, alertas_df: pd.DataFrame) -> dict:
        """
        Validar la integridad de los datos cargados
        
        Args:
            eventos_df (pd.DataFrame): DataFrame de eventos
            alertas_df (pd.DataFrame): DataFrame de alertas
            
        Returns:
            dict: Diccionario con resultados de validación
        """
        validation_results = {
            'eventos': {
                'duplicados': eventos_df.duplicated().sum() if eventos_df is not None else 0,
                'valores_nulos': eventos_df.isnull().sum().sum() if eventos_df is not None else 0,
                'coordenadas_validas': 0,
                'fechas_validas': 0
            },
            'alertas': {
                'duplicados': alertas_df.duplicated().sum() if alertas_df is not None else 0,
                'valores_nulos': alertas_df.isnull().sum().sum() if alertas_df is not None else 0,
                'coordenadas_validas': 0,
                'fechas_validas': 0
            }
        }
        
        # Validar coordenadas de eventos
        if eventos_df is not None and all(col in eventos_df.columns for col in ['Este', 'Norte']):
            coords_validas = eventos_df[['Este', 'Norte']].notna().all(axis=1).sum()
            validation_results['eventos']['coordenadas_validas'] = coords_validas
        
        # Validar fechas de eventos
        if eventos_df is not None and 'Fecha' in eventos_df.columns:
            fechas_validas = eventos_df['Fecha'].notna().sum()
            validation_results['eventos']['fechas_validas'] = fechas_validas
        
        # Validar coordenadas de alertas
        if alertas_df is not None and all(col in alertas_df.columns for col in ['Este', 'Norte']):
            coords_validas = alertas_df[['Este', 'Norte']].notna().all(axis=1).sum()
            validation_results['alertas']['coordenadas_validas'] = coords_validas
        
        # Validar fechas de alertas
        if alertas_df is not None and 'Fecha Declarada' in alertas_df.columns:
            fechas_validas = alertas_df['Fecha Declarada'].notna().sum()
            validation_results['alertas']['fechas_validas'] = fechas_validas
        
        return validation_results
