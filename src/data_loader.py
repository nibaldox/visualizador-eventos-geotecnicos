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
from io import BytesIO

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """
    Clase para cargar y procesar datos de eventos geotécnicos y alertas de seguridad
    """
    
    def __init__(self):
        """
        Inicializar el cargador de datos
        
        Esta clase se encarga de procesar archivos Excel subidos por el usuario
        con datos de eventos geotécnicos y alertas de seguridad.
        """
    
    def load_eventos_from_upload(self, uploaded_file) -> Optional[pd.DataFrame]:
        """
        Cargar datos de eventos geotécnicos desde archivo subido
        
        Args:
            uploaded_file: Archivo subido desde st.file_uploader
            
        Returns:
            pd.DataFrame: DataFrame con los datos de eventos o None si hay error
        """
        try:
            if uploaded_file is None:
                return None
                
            # Obtener el nombre del archivo para determinar el formato
            file_name = uploaded_file.name.lower()
            
            # Cargar datos según el tipo de archivo
            if file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            elif file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith('.txt'):
                # Intentar CSV con delimitador de tabulación primero
                try:
                    df = pd.read_csv(uploaded_file, sep='\t')
                except:
                    # Si falla, intentar con otros delimitadores comunes
                    uploaded_file.seek(0)  # Resetear posición del archivo
                    df = pd.read_csv(uploaded_file, sep=';')
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_name}")
            
            # Procesar datos igual que en load_eventos
            df = self._process_eventos_data(df)
            
            logger.info(f"Eventos cargados exitosamente desde archivo subido: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar eventos desde archivo subido: {str(e)}")
            st.error(f"Error al cargar archivo de eventos: {str(e)}")
            return None
    
    def load_alertas_from_upload(self, uploaded_file) -> Optional[pd.DataFrame]:
        """
        Cargar datos de alertas desde archivo subido
        
        Args:
            uploaded_file: Archivo subido desde st.file_uploader
            
        Returns:
            pd.DataFrame: DataFrame con los datos de alertas o None si hay error
        """
        try:
            if uploaded_file is None:
                return None
                
            # Obtener el nombre del archivo para determinar el formato
            file_name = uploaded_file.name.lower()
            
            # Cargar datos según el tipo de archivo
            if file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            elif file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith('.txt'):
                # Intentar CSV con delimitador de tabulación primero
                try:
                    df = pd.read_csv(uploaded_file, sep='\t')
                except:
                    # Si falla, intentar con otros delimitadores comunes
                    uploaded_file.seek(0)  # Resetear posición del archivo
                    df = pd.read_csv(uploaded_file, sep=';')
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_name}")
            
            # Procesar datos igual que en load_alertas
            df = self._process_alertas_data(df)
            
            logger.info(f"Alertas cargadas exitosamente desde archivo subido: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar alertas desde archivo subido: {str(e)}")
            st.error(f"Error al cargar archivo de alertas: {str(e)}")
            return None
            st.error(f"Error al cargar archivo de alertas: {str(e)}")
            return None
    
    def _process_eventos_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Procesar datos de eventos geotécnicos
        
        Args:
            df (pd.DataFrame): DataFrame crudo de eventos
            
        Returns:
            pd.DataFrame: DataFrame procesado
        """
        # Validar columnas esperadas según especificación actualizada
        expected_columns = [
            'id', 'Tipo', 'Vigilante', 'Fecha', 'Zona monitoreo',
            'Pared', 'Este', 'Norte', 'Cota', 'Alerta de Seguridad Asociada',
            'Tiempo de Activación (h)', 'Altura Banco (m)', 'Altura Falla (m)',
            'Desplazamiento Acumulado (mm)', 'Velocidad Promedio (mm/h)',
            'Velocidad Máxima Últimas 12hrs. (mm/h)', 
            'Velocidad Anterior a Velocidad Máxima (mm/h)',
            'Volumen (ton)', 'Detectado por Sistema', 'Radar Principal',
            'Mecanismos falla'
        ]
        
        # Verificar que las columnas principales existan (las primeras 10 son críticas)
        critical_columns = expected_columns[:10]
        missing_columns = [col for col in critical_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Columnas críticas faltantes en eventos: {missing_columns}")
            st.warning(f"⚠️ Columnas faltantes en el archivo de eventos: {', '.join(missing_columns)}")
        
        # Procesar fechas (formato dd/mm/aaaa hh:mm según especificación)
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
                result[mask] = pd.to_datetime(cleaned_series[mask], errors='coerce')
            
            return result
        
        if 'Fecha' in df.columns:
            df['Fecha'] = parse_date_flexible(df['Fecha'])
        
        if 'Fecha UTC' in df.columns:
            df['Fecha UTC'] = parse_date_flexible(df['Fecha UTC'])
        
        # Procesar coordenadas y valores numéricos (formato con comas decimales)
        numeric_columns = [
            'Este', 'Norte', 'Cota', 'Tiempo de Activación (h)',
            'Altura Banco (m)', 'Altura Falla (m)', 'Desplazamiento Acumulado (mm)',
            'Velocidad Promedio (mm/h)', 'Velocidad Máxima Últimas 12hrs. (mm/h)',
            'Velocidad Anterior a Velocidad Máxima (mm/h)', 'Volumen (ton)'
        ]
        
        def process_numeric_column(series):
            """Procesar columna numérica con formato de coma decimal"""
            if series.empty:
                return series
            
            # Convertir a string y limpiar
            cleaned = series.astype(str).str.strip()
            
            # Reemplazar comas por puntos para formato decimal
            cleaned = cleaned.str.replace(',', '.', regex=False)
            
            # Remover caracteres no numéricos excepto punto y signo negativo
            cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
            
            # Convertir a numérico
            return pd.to_numeric(cleaned, errors='coerce')
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = process_numeric_column(df[col])
        
        # Validar y procesar columnas de texto específicas
        text_columns = ['id', 'Tipo', 'Vigilante', 'Zona monitoreo', 'Pared', 'Detectado por Sistema', 'Radar Principal', 'Mecanismos falla']
        
        for col in text_columns:
            if col in df.columns:
                # Limpiar espacios y convertir a string
                df[col] = df[col].astype(str).str.strip()
                # Reemplazar 'nan' strings con NaN real
                df[col] = df[col].replace(['nan', 'None', ''], pd.NaT)
        
        # Validación específica para columnas críticas
        if 'id' in df.columns:
            # Verificar formato de ID (año.número)
            invalid_ids = df[~df['id'].str.match(r'^\d{4}\.\d+$', na=False)]
            if not invalid_ids.empty:
                logger.warning(f"Se encontraron {len(invalid_ids)} IDs con formato inválido")
        
        if 'Detectado por Sistema' in df.columns:
            # Normalizar valores de Sí/No
            df['Detectado por Sistema'] = df['Detectado por Sistema'].str.capitalize()
            df['Detectado por Sistema'] = df['Detectado por Sistema'].replace({'Si': 'Sí', 'NO': 'No', 'YES': 'Sí', 'yes': 'Sí', 'no': 'No'})
        
        logger.info(f"Eventos procesados: {len(df)} registros")
        return df
    
    def _process_alertas_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Procesar datos de alertas y alarmas de seguridad
        
        Args:
            df (pd.DataFrame): DataFrame crudo de alertas
            
        Returns:
            pd.DataFrame: DataFrame procesado
        """
        # Validar columnas esperadas según especificación actualizada
        expected_columns = [
            'id', 'Estatus', 'Vigilante', 'Fecha Declarada', 'Evento',
            'Comportamiento o Velocidad', 'Nivel de Exposición', 'Zona de Monitoreo',
            'Localización General', 'Pared', 'Este', 'Norte', 'Cota',
            'Estado', 'Fecha de Cierre', 'Responsable de Cierre',
            'Geotécnico Operativo', 'Notificación Telefónica', 'Notificación por Correo',
            'Desplazamiento Últimas 12 hrs. (mm)',
            'Velocidad Promedio Últimas 12 hrs. (mm/h)',
            'Velocidad Máxima Últimas 12 hrs. (mm/h)'
        ]
        
        # Verificar que las columnas críticas existan (las primeras 10 son críticas)
        critical_columns = expected_columns[:10]
        missing_columns = [col for col in critical_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Columnas críticas faltantes en alertas: {missing_columns}")
            st.warning(f"⚠️ Columnas faltantes en el archivo de alertas: {', '.join(missing_columns)}")
        
        # Procesar fechas (formato dd/mm/aaaa hh:mm según especificación)
        def parse_date_flexible_alerts(date_series):
            """Parsear fechas con formato dd/mm/aaaa hh:mm para alertas"""
            if date_series.empty:
                return date_series
            
            # Limpiar y preparar datos
            cleaned_series = date_series.astype(str).str.strip()
            
            # Remover valores vacíos o inválidos
            cleaned_series = cleaned_series.replace(['', 'nan', 'NaT', 'None'], pd.NaT)
            
            # Intentar parsear con formato específico dd/mm/yyyy hh:mm
            result = pd.to_datetime(cleaned_series, format='%d/%m/%Y %H:%M', errors='coerce', dayfirst=True)
            
            # Si hay valores sin parsear, intentar otros formatos comunes
            mask = result.isna() & cleaned_series.notna()
            if mask.any():
                # Intentar formato solo fecha dd/mm/yyyy
                result[mask] = pd.to_datetime(cleaned_series[mask], format='%d/%m/%Y', errors='coerce', dayfirst=True)
            
            # Si aún hay valores sin parsear, usar parsing flexible con dayfirst=True
            mask = result.isna() & cleaned_series.notna()
            if mask.any():
                result[mask] = pd.to_datetime(cleaned_series[mask], errors='coerce', dayfirst=True)
            
            return result
        
        # Procesar columnas de fecha
        if 'Fecha Declarada' in df.columns:
            df['Fecha Declarada'] = parse_date_flexible_alerts(df['Fecha Declarada'])
        
        if 'Fecha de Cierre' in df.columns:
            df['Fecha de Cierre'] = parse_date_flexible_alerts(df['Fecha de Cierre'])
        
        # Procesar coordenadas y valores numéricos (formato con comas decimales)
        numeric_columns = [
            'Este', 'Norte', 'Cota',
            'Desplazamiento Últimas 12 hrs. (mm)',
            'Velocidad Promedio Últimas 12 hrs. (mm/h)',
            'Velocidad Máxima Últimas 12 hrs. (mm/h)'
        ]
        
        def process_numeric_column_alerts(series):
            """Procesar columna numérica con formato de coma decimal para alertas"""
            if series.empty:
                return series
            
            # Convertir a string y limpiar
            cleaned = series.astype(str).str.strip()
            
            # Reemplazar comas por puntos para formato decimal
            cleaned = cleaned.str.replace(',', '.', regex=False)
            
            # Remover caracteres no numéricos excepto punto y signo negativo
            cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
            
            # Convertir a numérico
            return pd.to_numeric(cleaned, errors='coerce')
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = process_numeric_column_alerts(df[col])
        
        # Validar y procesar columnas de texto específicas
        text_columns = ['id', 'Estatus', 'Vigilante', 'Zona de Monitoreo', 'Pared', 'Estado', 
                       'Notificación Telefónica', 'Notificación por Correo']
        
        for col in text_columns:
            if col in df.columns:
                # Limpiar espacios y convertir a string
                df[col] = df[col].astype(str).str.strip()
                # Reemplazar 'nan' strings con NaN real
                df[col] = df[col].replace(['nan', 'None', ''], pd.NaT)
        
        # Validaciones específicas para columnas críticas de alertas
        if 'id' in df.columns:
            # Verificar formato de ID (año.número)
            invalid_ids = df[~df['id'].str.match(r'^\d{4}\.\d+$', na=False)]
            if not invalid_ids.empty:
                logger.warning(f"Se encontraron {len(invalid_ids)} IDs de alertas con formato inválido")
        
        if 'Estado' in df.columns:
            # Normalizar valores de estado
            df['Estado'] = df['Estado'].str.title()
            df['Estado'] = df['Estado'].replace({
                'Abierto': 'Abierto', 'Cerrado': 'Cerrado',
                'ABIERTO': 'Abierto', 'CERRADO': 'Cerrado',
                'Open': 'Abierto', 'Closed': 'Cerrado'
            })
        
        if 'Notificación Telefónica' in df.columns:
            # Normalizar valores booleanos
            df['Notificación Telefónica'] = df['Notificación Telefónica'].str.upper()
            df['Notificación Telefónica'] = df['Notificación Telefónica'].replace({
                'VERDADERO': 'VERDADERO', 'FALSO': 'FALSO',
                'TRUE': 'VERDADERO', 'FALSE': 'FALSO',
                'SÍ': 'VERDADERO', 'NO': 'FALSO',
                'SI': 'VERDADERO', 'YES': 'VERDADERO'
            })
        
        if 'Notificación por Correo' in df.columns:
            # Normalizar valores booleanos
            df['Notificación por Correo'] = df['Notificación por Correo'].str.upper()
            df['Notificación por Correo'] = df['Notificación por Correo'].replace({
                'VERDADERO': 'VERDADERO', 'FALSO': 'FALSO',
                'TRUE': 'VERDADERO', 'FALSE': 'FALSO',
                'SÍ': 'VERDADERO', 'NO': 'FALSO',
                'SI': 'VERDADERO', 'YES': 'VERDADERO'
            })
        
        logger.info(f"Alertas procesadas: {len(df)} registros")
        return df

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
