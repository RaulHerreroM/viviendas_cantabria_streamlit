# Sistema de Análisis y Predicción de Precios Inmobiliarios en Cantabria

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.31.0-red.svg)
![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Lambda-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema completo de análisis de mercado inmobiliario en Cantabria que integra scraping de múltiples fuentes, procesamiento ETL, machine learning y visualización interactiva.

## Tabla de Contenidos

- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Componentes del Sistema](#componentes-del-sistema)
- [Fuentes de Datos](#fuentes-de-datos)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Instalación y Configuración](#instalación-y-configuración)
- [Uso de la Aplicación](#uso-de-la-aplicación)
- [API de Predicción](#api-de-predicción)
- [Estructura de Datos](#estructura-de-datos)
- [Pipeline de Datos](#pipeline-de-datos)
- [Estructura del Proyecto](#estructura-del-proyecto)

---

## Arquitectura del Sistema

El proyecto implementa un pipeline completo de datos inmobiliarios desde la extracción hasta la visualización:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FUENTES DE DATOS                              │
├─────────────────────────────────────────────────────────────────┤
│  [Idealista]  [Fotocasa]              [Catastro]                │
│       │            │                        │                    │
│       └────────────┴────────────────────────┘                    │
│                         │                                        │
│                    [Scrapers]                                    │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE                                  │
├─────────────────────────────────────────────────────────────────┤
│  • Deduplicación entre portales (Idealista + Fotocasa)          │
│  • Limpieza de datos (valores nulos, outliers)                  │
│  • Normalización de formatos                                    │
│  • Enriquecimiento (coordenadas, comarcas)                      │
└─────────────────────────┼────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│              DATA PROCESSING & AGGREGATION                       │
├─────────────────────────────────────────────────────────────────┤
│  • Agregación por provincia/municipio/sección censal            │
│  • Cálculo de estadísticas (media, min, max, percentiles)       │
│  • Feature engineering para ML                                  │
│  • Generación de series temporales                              │
│  • Exportación a Parquet                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                   MACHINE LEARNING                               │
├─────────────────────────────────────────────────────────────────┤
│  • Modelo: Gradient Boosting Regressor                          │
│  • Features: municipio, m², habitaciones, baños, etc.           │
│  • Entrenamiento periódico con nuevos datos                     │
│  • Validación y métricas de rendimiento                         │
└─────────────────────────┼────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DEPLOYMENT & STORAGE                           │
├─────────────────────────────────────────────────────────────────┤
│  • AWS S3: Almacenamiento de datos (Parquet + GeoJSON)          │
│  • AWS Lambda: Servicio de predicción                           │
│  • API Gateway: Endpoint REST para predicciones                 │
└─────────────────────────┼────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│              VISUALIZACIÓN (STREAMLIT APP)                       │
├─────────────────────────────────────────────────────────────────┤
│  • Mapa Geográfico (choropleth por municipio)                   │
│  • Mapa de Comarcas (agregación provincial)                     │
│  • Comparación Portales vs Catastro                             │
│  • Mapa Santander (secciones censales)                          │
│  • Series Temporales                                            │
│  • Predicción de Precios (integración API)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Componentes del Sistema

### 1. Data Collection (Scraping)

**Portales Inmobiliarios** (Repositorio separado)
- **Idealista**: Portal principal de viviendas en España
- **Fotocasa**: Segundo portal más utilizado
- **Campos extraídos**: precio, m², habitaciones, baños, ubicación, coordenadas, calificación energética
- **Frecuencia**: Actualización periódica (diaria/semanal)

**Datos del Catastro** (Repositorio separado)
- Valores de referencia oficiales por municipio
- Datos históricos para análisis temporal
- Referencia para comparación con precios de mercado

### 2. ETL Pipeline

**Deduplicación**
- Eliminación de anuncios duplicados entre Idealista y Fotocasa
- Algoritmos de matching por ubicación y características
- Consolidación de información de múltiples fuentes

**Limpieza de Datos**
- Tratamiento de valores nulos
- Detección y eliminación de outliers
- Validación de coordenadas geográficas
- Normalización de nombres de municipios (acentos, variantes)

**Agregación Geográfica**
- Agregación por municipio (~150 municipios en Cantabria)
- Agregación por comarca (10 comarcas)
- Agregación por sección censal (Santander)

### 3. Machine Learning Model

**Modelo**: Gradient Boosting Regressor

**Features Utilizadas**:
- Ubicación (municipio, latitud, longitud)
- Características físicas (m² construidos, m² útiles)
- Composición (habitaciones, baños)
- Tipo de vivienda (piso, casa, dúplex, etc.)
- Calificación energética
- Variables temporales (fecha)

**Entrenamiento**:
- Reentrenamiento periódico con nuevos datos
- Validación cruzada para evitar overfitting
- Métricas: RMSE, MAE, R²
- Versionado de modelos

**Deployment**:
- Modelo empaquetado en AWS Lambda
- Endpoint REST vía API Gateway
- Respuestas en tiempo real (<500ms)

### 4. API de Predicción

**Endpoint**: `https://nlv0wy2dj3.execute-api.eu-west-1.amazonaws.com/prod/predict`

**Método**: POST

**Autenticación**: API Key (header: `x-api-key`)

**Request Schema**:
```json
{
  "municipio": "string (required)",
  "tipo": "string (optional: Piso, Casa, Dúplex, etc.)",
  "m2_construidos": "float (optional)",
  "m2_utiles": "float (optional)",
  "habitaciones": "int (optional)",
  "banos": "int (optional)",
  "calificacion_energetica": "string (optional: A, B, C, D, E, F, G)",
  "latitud": "float (optional)",
  "longitud": "float (optional)"
}
```

**Response Schema**:
```json
{
  "precio_estimado": 185000.0,
  "precio_m2": 2312.5,
  "rango_inferior": 165000.0,
  "rango_superior": 205000.0,
  "confianza": "alta"
}
```

Ver sección [API de Predicción](#api-de-predicción) para ejemplos de uso.

### 5. Visualización Streamlit

La aplicación web ofrece **6 vistas interactivas**:

#### Vista 1: Mapa Geográfico
- Mapa choropleth de todos los municipios de Cantabria
- Color codificado por precio/m²
- Treemap por comarca y municipio
- Top 10 municipios más caros/baratos

#### Vista 2: Mapa de Comarcas
- Gráfico de barras horizontales por comarca
- Tabla resumen con estadísticas (min, max, media)
- Lista expandible de municipios por comarca

#### Vista 3: Comparación Portales vs Catastro
- Comparativa de precios entre portales inmobiliarios y catastro
- Diferencias porcentuales destacadas
- Scatter plot de correlación
- Top 10 municipios con mayores diferencias

#### Vista 4: Mapa Santander (Secciones Censales)
- Vista granular por secciones censales dentro de Santander
- GeoJSON de límites geográficos
- Datos de portales inmobiliarios

#### Vista 5: Series Temporales
- Evolución histórica de precios
- Selección por municipio o distrito
- Visualizaciones:
  - Precios absolutos
  - Variación mensual (%)
  - Variación anual (%)
- Gráficos interactivos con Plotly

#### Vista 6: Predicción de Precios
- Formulario interactivo para introducir características
- Integración con API Lambda
- Resultados: precio estimado, precio/m², rango, confianza
- Detalles técnicos del request/response

---

## Fuentes de Datos

| Fuente | Tipo | Descripción | Actualización |
|--------|------|-------------|---------------|
| **Idealista** | Portales | Anuncios de viviendas en venta/alquiler | Diaria/Semanal |
| **Fotocasa** | Portales | Anuncios de viviendas en venta/alquiler | Diaria/Semanal |
| **Catastro** | Oficial | Valores de referencia del catastro | Trimestral |
| **GeoJSON Municipios** | Geográfico | Límites administrativos de municipios | Estática |
| **GeoJSON Santander** | Geográfico | Secciones censales de Santander | Estática |

**Almacenamiento**: AWS S3 (bucket: `viviendas-cantabria-raul`)

**Formato**: Parquet (optimizado para análisis) y JSON (datos geográficos)

---

## Tecnologías Utilizadas

### Data Collection & Processing
- **Python 3.11**: Lenguaje principal
- **Pandas**: Manipulación de datos
- **NumPy**: Operaciones numéricas
- **PyArrow**: Lectura/escritura de Parquet
- **Selenium**: Web scraping (inferido)

### Machine Learning
- **Scikit-learn**: Gradient Boosting Regressor
- **Pandas**: Feature engineering
- **Joblib**: Serialización de modelos

### Cloud Infrastructure
- **AWS S3**: Almacenamiento de datos
- **AWS Lambda**: Servicio de predicción
- **API Gateway**: Endpoint REST
- **boto3**: AWS SDK para Python
- **s3fs**: Sistema de archivos S3

### Visualization & Frontend
- **Streamlit 1.31.0**: Framework web interactivo
- **Plotly 5.18.0**: Gráficos interactivos
- **streamlit-folium**: Integración Streamlit-Folium
- **GeoPandas**: Manipulación de datos geográficos

### Utilities
- **python-dotenv**: Gestión de variables de entorno
- **requests**: Llamadas HTTP a API
- **gspread**: Integración con Google Sheets (legacy)

---

## Instalación y Configuración

### Requisitos Previos

- Python 3.11 o superior
- Cuenta de AWS con acceso a S3
- API Key para el servicio de predicción (solicitar al administrador)

### Opción 1: Instalación con Poetry (Recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/viviendas_cantabria_streamlit.git
cd viviendas_cantabria_streamlit

# Instalar dependencias con Poetry
poetry install

# Activar el entorno virtual
poetry shell

# Ejecutar la aplicación
streamlit run app.py
```

### Opción 2: Instalación con pip

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/viviendas_cantabria_streamlit.git
cd viviendas_cantabria_streamlit

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

### Configuración de AWS

Crear el archivo `.streamlit/secrets.toml` (usar `.streamlit/secrets.toml.example` como plantilla):

```toml
[aws]
aws_access_key_id = "TU_ACCESS_KEY_ID"
aws_secret_access_key = "TU_SECRET_ACCESS_KEY"
aws_region = "eu-west-1"

[s3]
bucket_name = "viviendas-cantabria-raul"
```

**Alternativa**: Configurar credenciales AWS mediante variables de entorno o AWS CLI:

```bash
export AWS_ACCESS_KEY_ID="tu_access_key"
export AWS_SECRET_ACCESS_KEY="tu_secret_key"
export AWS_DEFAULT_REGION="eu-west-1"
```

### API Key para Predicciones

La API Key se introduce directamente en la interfaz de Streamlit en la vista "Predicción de Precios". No es necesaria para las demás vistas.

### Verificar Instalación

La aplicación debería abrirse automáticamente en `http://localhost:8501`. Si no es así, abrir manualmente en el navegador.

---

## Uso de la Aplicación

### Navegación Principal

Utiliza el menú lateral izquierdo para cambiar entre las 6 vistas disponibles:

1. **Mapa Geográfico**: Vista general de precios por municipio
2. **Mapa de Comarcas**: Análisis agregado por comarca
3. **Mapa Portales**: Comparación portales vs catastro
4. **Mapa Santander Portales**: Vista detallada de Santander
5. **Series Temporales**: Evolución histórica de precios
6. **Predicción**: Estimador de precio de viviendas

### Características Generales

- **Filtros Interactivos**: Selecciona municipios, rangos de precio, fechas
- **Métricas en Tiempo Real**: Estadísticas clave actualizadas dinámicamente
- **Gráficos Interactivos**: Hover, zoom, pan en todos los gráficos Plotly
- **Exportación de Datos**: Descarga datos filtrados en CSV
- **Caché Inteligente**: Datos cacheados 10 minutos para mejor rendimiento

### Casos de Uso Típicos

**Investigador de Mercado**:
1. Vista "Mapa Geográfico" para overview de precios
2. Vista "Series Temporales" para tendencias
3. Vista "Comparación Portales" para validar precios de mercado

**Comprador de Vivienda**:
1. Vista "Predicción" para estimar valor justo
2. Vista "Mapa Santander" para comparar zonas específicas
3. Vista "Series Temporales" para ver evolución de precios

**Analista de Datos**:
1. Exportar datos desde cualquier vista
2. Usar filtros avanzados para segmentación
3. Análisis de correlaciones en vista "Portales vs Catastro"


---

## Pipeline de Datos

### Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: EXTRACCIÓN                                              │
│ Frecuencia: Diaria/Semanal                                      │
├─────────────────────────────────────────────────────────────────┤
│ 1.1 Scraping de Idealista                                       │
│     → Anuncios de viviendas en venta                            │
│     → Metadata: precio, m², ubicación, características          │
│                                                                 │
│ 1.2 Scraping de Fotocasa                                        │
│     → Anuncios de viviendas en venta                            │
│     → Mismos campos que Idealista                               │
│                                                                 │
│ 1.3 Scraping de Catastro                                        │
│     → Valores de referencia por municipio                       │
│     → Series históricas trimestrales                            │
│                                                                 │
│ Output: Raw CSV/JSON files                                      │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: TRANSFORMACIÓN (ETL)                                    │
│ Procesamiento: Batch                                            │
├─────────────────────────────────────────────────────────────────┤
│ 2.1 Deduplicación Cross-Platform                                │
│     → Matching por coordenadas (radio 50m)                      │
│     → Matching por dirección normalizada                        │
│     → Selección de precio más actualizado                       │
│                                                                 │
│ 2.2 Limpieza de Datos                                           │
│     → Eliminación de valores nulos críticos                     │
│     → Detección de outliers (IQR, Z-score)                      │
│     → Validación de rangos (precio > 0, m² > 10)                │
│     → Corrección de tipos de datos                              │
│                                                                 │
│ 2.3 Normalización                                               │
│     → Nombres de municipios (acentos, mayúsculas)               │
│     → Formatos de fecha (ISO 8601)                              │
│     → Unidades (€, m²)                                          │
│                                                                 │
│ 2.4 Enriquecimiento                                             │
│     → Lookup de coordenadas (coordenadas_municipios.py)         │
│     → Asignación de comarca (comarcas_municipios.py)            │
│     → Cálculo de precio/m²                                      │
│     → Geocoding de direcciones faltantes                        │
│                                                                 │
│ Output: Cleaned pandas DataFrames                               │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: AGREGACIÓN Y PRECÁLCULO                                 │
│ Procesamiento: Batch                                            │
├─────────────────────────────────────────────────────────────────┤
│ 3.1 Agregación por Municipio                                    │
│     → Precio medio, min, max                                    │
│     → Percentiles (25, 50, 75)                                  │
│     → Count de propiedades                                      │
│     → Group by: municipio + fecha                               │
│                                                                 │
│ 3.2 Agregación por Comarca                                      │
│     → Estadísticas agregadas a nivel comarca                    │
│     → Weighted average por población                            │
│                                                                 │
│ 3.3 Agregación por Sección Censal (Santander)                   │
│     → Vista granular para la capital                            │
│     → Join con GeoJSON de secciones                             │
│                                                                 │
│ 3.4 Series Temporales                                           │
│     → Resampling mensual/trimestral                             │
│     → Cálculo de variaciones (MoM, YoY)                         │
│     → Interpolación de valores faltantes                        │
│                                                                 │
│ 3.5 Exportación a Parquet                                       │
│     → Compresión snappy                                         │
│     → Particionado por fecha (opcional)                         │
│                                                                 │
│ Output: precios_*.parquet files                                 │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: CARGA A S3                                              │
│ Frecuencia: Al finalizar ETL                                    │
├─────────────────────────────────────────────────────────────────┤
│ 4.1 Upload a S3                                                 │
│     → Bucket: viviendas-cantabria-raul                          │
│     → Path: data/processed/YYYY-MM-DD/                          │
│     → Versionado automático (S3 versioning)                     │
│                                                                 │
│ 4.2 Metadata                                                    │
│     → Timestamp de generación                                   │
│     → Checksum (MD5)                                            │
│     → Número de registros                                       │
│                                                                 │
│ Output: Datos disponibles para consumo                          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 5: ENTRENAMIENTO ML (Periódico)                            │
│ Frecuencia: Mensual / Al acumular N nuevos registros            │
├─────────────────────────────────────────────────────────────────┤
│ 5.1 Feature Engineering                                         │
│     → Variables categóricas (municipio, tipo) → One-hot         │
│     → Variables numéricas → Scaling                             │
│     → Features derivadas (precio/habitación, etc.)              │
│                                                                 │
│ 5.2 Split Train/Validation/Test                                 │
│     → 70% train, 15% validation, 15% test                       │
│     → Split temporal (evitar data leakage)                      │
│                                                                 │
│ 5.3 Entrenamiento Gradient Boosting                             │
│     → Hyperparameter tuning (GridSearch/RandomSearch)           │
│     → Cross-validation (K-Fold)                                 │
│     → Early stopping                                            │
│                                                                 │
│ 5.4 Evaluación                                                  │
│     → Métricas: RMSE, MAE, R², MAPE                             │
│     → Análisis de residuos                                      │
│     → Feature importance                                        │
│                                                                 │
│ 5.5 Serialización                                               │
│     → Joblib dump del modelo                                    │
│     → Versionado (model_v1.0.0.pkl)                             │
│                                                                 │
│ Output: Modelo entrenado (.pkl)                                 │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 6: DEPLOYMENT                                              │
│ Trigger: Tras validar nuevo modelo                              │
├─────────────────────────────────────────────────────────────────┤
│ 6.1 Package Lambda                                              │
│     → Modelo + dependencies en deployment package               │
│     → Lambda layer con scikit-learn, pandas                     │
│                                                                 │
│ 6.2 Deploy a AWS Lambda                                         │
│     → Update function code                                      │
│     → Configurar timeout (30s), memoria (512MB)                 │
│     → Variables de entorno (S3_BUCKET, MODEL_VERSION)           │
│                                                                 │
│ 6.3 Update API Gateway                                          │
│     → Configurar rate limiting                                  │
│     → API keys y usage plans                                    │
│     → CORS configuration                                        │
│                                                                 │
│ Output: API endpoint activa                                     │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FASE 7: CONSUMO (STREAMLIT APP)                                 │
│ Disponibilidad: 24/7                                            │
├─────────────────────────────────────────────────────────────────┤
│ 7.1 Carga de Datos desde S3                                     │
│     → s3_loader.py con @st.cache_data                           │
│     → TTL: 10 minutos                                           │
│                                                                 │
│ 7.2 Renderizado Interactivo                                     │
│     → 6 vistas con Streamlit components                         │
│     → Plotly charts, Folium maps                                │
│                                                                 │
│ 7.3 Llamadas a API de Predicción                                │
│     → On-demand desde vista "Predicción"                        │
│     → Authenticated requests (API key)                          │
│                                                                 │
│ Output: Insights para el usuario final                          │
└─────────────────────────────────────────────────────────────────┘
```