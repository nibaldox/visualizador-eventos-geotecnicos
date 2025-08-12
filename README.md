# 🏔️ Visualizador de Eventos Geotécnicos y Alertas de Seguridad

## Descripción del Proyecto

Este proyecto es una aplicación web interactiva desarrollada con **Streamlit** para visualizar y analizar eventos geotécnicos y alertas de seguridad de una mina a cielo abierto. La aplicación permite explorar datos de eventos ocurridos durante 2025, proporcionando herramientas avanzadas de análisis, visualización en mapas 2D/3D, gráficos interactivos y generación de reportes.

## 🚀 Características Principales

### 📊 **Dashboard Interactivo Avanzado**

- **Métricas clave** y resumen ejecutivo de eventos y alertas
- **Gráfica temporal de barras** - Evolución mensual de eventos (12 meses del 2025)
- **Mapa de eventos por mes** - Filtro interactivo con resaltado amarillo del mes seleccionado
- **Vista consolidada 2D** - Eventos, alertas y alarmas en un solo mapa
- **Mapa 3D interactivo** - Visualización espacial avanzada con elevación

### 📈 **Análisis de Altura de Falla**

- **Categorización por colores**:
  - 🟢 **Verde**: Eventos ≤ 15 metros (Altura Baja)
  - 🔵 **Azul**: Eventos >15m y ≤ 30 metros (Altura Media)
  - 🔴 **Rojo**: Eventos >30 metros (Altura Alta)
- **Gráficos especializados**: Barras, torta, histograma y scatter espacial
- **Estadísticas detalladas** por categoría de altura

### 🗺️ **Visualizaciones Espaciales**

- **Mapas 2D** con coordenadas locales (Este, Norte)
- **Mapa 3D interactivo** con múltiples vistas (Perspectiva, Superior, Lateral)
- **Scatter plots** con hover interactivo y información detallada
- **Filtros por tipo** y zona de monitoreo

### ⏰ **Análisis Temporal**

- **Timeline interactivo** de eventos geotécnicos
- **Filtros por fecha** con rangos personalizables
- **Análisis de tendencias** y patrones temporales

### 🔍 **Filtros y Análisis Avanzados**

- **Filtros por fecha, zona, tipo de evento y estado**
- **Análisis de correlaciones** entre eventos y alertas
- **Exportación de datos** en formato CSV
- **Validación automática** de coordenadas y fechas

## 📊 Datos Soportados

### Archivo de Eventos Geotécnicos

- **Archivo**: `Listado de Eventos [2025.1 - 2025.22] - 07_07_2025.xlsx`
- **Columnas principales**:
  - ID, Tipo, Vigilante, Fecha, Zona de monitoreo
  - Coordenadas (Este, Norte, Cota)
  - Parámetros técnicos (Volumen, Velocidades, Altura de falla)
  - Detección automática y radar principal

### Archivo de Alertas de Seguridad

- **Archivo**: `Listado de Alertas de Seguridad [2025.1 - 2025.95] - 07_07_2025.xlsx`
- **Columnas principales**:
  - ID, Estatus, Vigilante, Fecha Declarada, Estado
  - Zona de Monitoreo, Localización General
  - Coordenadas (Este, Norte, Cota)
  - Parámetros de velocidad y desplazamiento

## 🛠️ Stack Tecnológico

- **Python 3.8+**: Lenguaje de programación principal
- **Streamlit 1.28.1**: Framework para aplicaciones web interactivas
- **Pandas 2.1.3**: Manipulación y análisis de datos
- **Plotly 5.17.0**: Visualizaciones interactivas y gráficos
- **Folium 0.15.0**: Mapas geoespaciales interactivos
- **OpenPyXL 3.1.2**: Lectura de archivos Excel
- **NumPy 1.24.3**: Operaciones numéricas

## 📁 Estructura del Proyecto

```
visualizador-eventos-geot/
├── app.py                      # Aplicación principal de Streamlit
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Documentación del proyecto
├── .gitignore                  # Archivos a ignorar en Git
├── plan_implementacion.md      # Seguimiento del desarrollo
└── src/                        # Código fuente modular
    ├── data_loader.py          # Carga y procesamiento de datos
    ├── visualizations.py       # Funciones de visualización
    └── utils.py                # Utilidades y funciones auxiliares
```

## 🔧 Instalación y Configuración

### Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**

   ```bash
   git clone <url-del-repositorio>
   cd visualizador-eventos-geot
   ```

2. **Crear entorno virtual (recomendado)**

   ```bash
   python -m venv venv
   
   # En Windows
   venv\Scripts\activate
   
   # En Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Uso de la Aplicación

### Ejecutar la aplicación

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador web en `http://localhost:8501`

### 📁 Cargar Datos

La aplicación requiere que subas tus propios archivos Excel con los datos:

1. **En la barra lateral**, encontrarás la sección "📁 Cargar Archivos"
2. **Sube al menos un archivo**:
   - **📊 Eventos Geotécnicos**: Archivo Excel con datos de eventos ocurridos
   - **🚨 Alertas de Seguridad**: Archivo Excel con datos de alertas y su estado
3. **Formatos soportados**: `.xlsx`, `.xls`
4. **Una vez cargados**, la aplicación procesará automáticamente los datos

### Navegación por la Interfaz

#### 📊 Dashboard Interactivo Avanzado

- **Métricas principales**: Total de eventos, alertas, detección automática
- **Gráfica temporal de barras**: Evolución mensual de eventos (12 meses del 2025)
- **Mapa de eventos por mes**: Filtro interactivo con resaltado amarillo del mes seleccionado
- **Vista consolidada 2D**: Eventos, alertas y alarmas en un solo mapa scatter
- **Mapa 3D interactivo**: Visualización espacial avanzada con elevación
- **Controles 3D**: Vistas Perspectiva, Superior, Lateral y superficie base opcional

#### 📈 Análisis de Eventos

- **Timeline detallado**: Visualización cronológica de todos los eventos
- **Scatter plot espacial**: Ubicación de eventos con coordenadas locales
- **Análisis de altura de falla**: Categorización por rangos de altura:
  - 🟢 **Verde**: ≤ 15 metros (Altura Baja)
  - 🔵 **Azul**: >15m y ≤ 30 metros (Altura Media)
  - 🔴 **Rojo**: >30 metros (Altura Alta)
- **Gráficos especializados**: Barras, torta, histograma y scatter espacial por altura
- **Estadísticas detalladas**: Resumen por categoría de altura de falla
- **Distribución por zona**: Gráfico de barras por zona de monitoreo
- **Filtros interactivos**: Por fecha, zona y tipo de evento

#### 🚨 Análisis de Alertas

- **Scatter plot de alertas**: Ubicación geoespacial con códigos de color por estado
- **Estados de alertas**: Distribución por estado (Abierto/Cerrado)
- **Estadísticas del mapa**: Alertas abiertas, cerradas y zonas afectadas

#### 🗺️ Mapas Interactivos

- **Coordenadas locales**: Sistema Este-Norte para ubicación precisa
- **Hover interactivo**: Información detallada al pasar el mouse
- **Filtros por tipo**: Eventos vs alertas/alarmas
- **Zoom y navegación**: Controles interactivos para exploración detallada

#### 📋 Datos Detallados

- **Tablas completas**: Visualización de todos los datos filtrados
- **Exportación**: Descarga de datos en formato CSV
- **Búsqueda y ordenamiento**: Funcionalidades nativas de Streamlit

### Filtros Disponibles

- **Rango de fechas**: Selección de período específico
- **Zonas de monitoreo**: Filtro múltiple por zonas
- **Tipos de evento**: Filtro múltiple por categorías
- **Estados de alerta**: Filtro por estado (Abierto/Cerrado)

## 📈 Funcionalidades Avanzadas

### Análisis de Correlaciones

- Correlación temporal entre eventos y alertas
- Coeficiente de correlación estadística
- Visualización de patrones temporales

### Categorización Automática

- **Velocidades**: Muy Bajo, Bajo, Moderado, Alto, Muy Alto
- **Volúmenes**: Pequeño, Mediano, Grande, Muy Grande
- **Estados visuales**: Códigos de color en mapas

### Validación de Datos

- Verificación de integridad de coordenadas
- Validación de rangos de fechas
- Detección de valores faltantes o inconsistentes

## 🔍 Solución de Problemas

### Errores Comunes

1. **"Error al cargar los archivos de datos"**
   - Verificar que los archivos Excel estén en la carpeta `data-input/`
   - Comprobar que los nombres de archivo coincidan exactamente
   - Asegurar que los archivos no estén corruptos

2. **"ModuleNotFoundError"**
   - Verificar que todas las dependencias estén instaladas: `pip install -r requirements.txt`
   - Activar el entorno virtual si se está usando uno

3. **"No hay datos que mostrar"**
   - Revisar los filtros aplicados en la barra lateral
   - Verificar que el rango de fechas incluya datos válidos

4. **Problemas de rendimiento**
   - Reducir el rango de fechas para datasets muy grandes
   - Cerrar otras aplicaciones que consuman memoria

### Logs y Debugging

- Los logs se muestran en la consola donde se ejecuta Streamlit
- Usar `--logger.level=debug` para más información detallada

## 🤝 Contribución y Desarrollo

### Principios de Código Limpio Aplicados

- **Funciones pequeñas y específicas**: Cada función tiene una responsabilidad única
- **Nombres descriptivos**: Variables y funciones con nombres claros
- **Documentación completa**: Docstrings en todas las funciones
- **Manejo de errores**: Try-catch apropiados con logging
- **Modularidad**: Separación clara entre carga de datos, visualización y utilidades

### Estructura Modular

- `data_loader.py`: Responsable únicamente de cargar y validar datos
- `visualizations.py`: Contiene todas las funciones de gráficos y mapas
- `utils.py`: Funciones auxiliares reutilizables
- `app.py`: Interfaz principal y orquestación

### Agregar Nuevas Funcionalidades

1. Seguir los principios de clean code establecidos
2. Documentar todas las funciones nuevas
3. Agregar manejo de errores apropiado
4. Actualizar este README si es necesario

## 📝 Licencia

Este proyecto está desarrollado para análisis interno de seguridad geotécnica. Todos los derechos reservados.

## 📞 Soporte

Para reportar problemas o solicitar nuevas funcionalidades, contactar al equipo de desarrollo del sistema de análisis geotécnico.

---

**Desarrollado por  N.A.V. para mejorar la seguridad en operaciones mineras**
