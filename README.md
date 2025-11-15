# Mapa de Calor de Viviendas en Cantabria 🏠

Aplicación interactiva de Streamlit para visualizar propiedades inmobiliarias en Cantabria mediante un mapa de calor basado en el precio por metro cuadrado.

## Características

- **Mapa de calor interactivo**: Visualiza la densidad de precios por metro cuadrado en diferentes zonas de Cantabria
- **Filtros avanzados**: Filtra por municipio, rango de precio y número de habitaciones
- **Métricas en tiempo real**: Visualiza estadísticas clave como precio promedio, precio/m² y tamaño promedio
- **Gráficos interactivos**: Histogramas y gráficos de barras con Plotly
- **Marcadores informativos**: Click en los marcadores del mapa para ver detalles de cada propiedad
- **Exportación de datos**: Descarga los datos filtrados en formato CSV

## Instalación

### Requisitos previos

- Python 3.8 o superior
- pip

### Pasos de instalación

1. Clona el repositorio:
```bash
git clone <url-del-repositorio>
cd viviendas_cantabria_streamlit
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

Para ejecutar la aplicación:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Estructura del proyecto

```
viviendas_cantabria_streamlit/
├── app.py                 # Aplicación principal de Streamlit
├── data/
│   └── data_prueba.csv   # Datos de propiedades
├── requirements.txt      # Dependencias del proyecto
└── README.md            # Este archivo
```

## Datos

El archivo `data/data_prueba.csv` contiene información de propiedades con los siguientes campos:

- **precio**: Precio de la propiedad en euros
- **m2_construidos**: Metros cuadrados construidos
- **m2_utiles**: Metros cuadrados útiles
- **habitaciones**: Número de habitaciones
- **banos**: Número de baños
- **ubicacion**: Ubicación completa de la propiedad
- **latitud/longitud**: Coordenadas geográficas
- **direccion**: Dirección de la propiedad
- Y más campos...

## Funcionalidades del mapa

### Código de colores de marcadores

- 🔴 **Rojo**: Precio/m² por encima del promedio
- 🟠 **Naranja**: Precio/m² cerca del promedio
- 🔵 **Azul**: Precio/m² por debajo del promedio (más de 20% menos)

### Mapa de calor

El mapa de calor muestra la intensidad de precios por zona:
- **Azul**: Precios bajos por m²
- **Verde/Amarillo**: Precios medios por m²
- **Naranja/Rojo**: Precios altos por m²

## Personalización

Para usar tus propios datos, asegúrate de que tu archivo CSV contenga al menos las siguientes columnas:

- `precio`: Precio de la propiedad
- `m2_construidos`: Superficie en metros cuadrados
- `latitud`: Coordenada de latitud
- `longitud`: Coordenada de longitud
- `ubicacion`: Ubicación (debe contener el municipio separado por `|`)

## Tecnologías utilizadas

- **Streamlit**: Framework para la interfaz web
- **Folium**: Mapas interactivos
- **Plotly**: Gráficos interactivos
- **Pandas**: Manipulación y análisis de datos
- **NumPy**: Operaciones numéricas

## Licencia

Este proyecto está bajo licencia MIT.

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.
