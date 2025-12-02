import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from s3_loader import load_municipios_data, load_geojson_municipios
import unicodedata

# Configuracion de la pagina
st.set_page_config(
    page_title="Dashboard Inmobiliario Cantabria",
    page_icon="🏠",
    layout="wide"
)

# Funcion para normalizar nombres de municipios
def normalizar_municipio(nombre):
    """Normaliza el nombre del municipio para hacer matching"""
    if pd.isna(nombre):
        return nombre

    # Remover acentos
    nombre = ''.join(c for c in unicodedata.normalize('NFD', str(nombre))
                     if unicodedata.category(c) != 'Mn')

    # Casos especiales
    mapeo = {
        'El Astillero': 'Astillero (El)',
        'Cabuerniga (Valle de)': 'Cabuerniga',
        'Ribamontan al Mar': 'Ribamontán al Mar',
        'Ribamontan al Monte': 'Ribamontán al Monte',
        'Penagos': 'Penagos',
        'Penarrubia': 'Peñarrubia',
        'Bareyo': 'Bareyo',
    }

    return mapeo.get(nombre, nombre)

# Titulo principal - version compacta
st.title("🏠 Dashboard Inmobiliario - Cantabria")

# Cargar datos desde S3
try:
    df = load_municipios_data()

    # Obtener datos mas recientes por municipio
    df_reciente = df.sort_values('fecha').groupby('municipio').tail(1)

    # Cargar GeoJSON de municipios desde S3
    geojson_municipios = load_geojson_municipios()

    # Obtener todos los municipios del GeoJSON
    municipios_geojson = [f['properties']['NOMBRE'] for f in geojson_municipios['features']]

    # Preparar datos para el mapa - normalizar nombres
    df_mapa = df_reciente[['municipio', 'precio_m2']].copy()
    df_mapa['municipio_norm'] = df_mapa['municipio'].apply(normalizar_municipio)

    # Crear DataFrame completo con TODOS los municipios del GeoJSON
    municipios_con_datos = dict(zip(df_mapa['municipio_norm'], df_mapa.to_dict('records')))

    # Lista completa de todos los municipios
    todos_municipios = []

    for mun_geo in municipios_geojson:
        if mun_geo in municipios_con_datos:
            # Municipio con datos
            todos_municipios.append(municipios_con_datos[mun_geo])
        else:
            # Municipio sin datos - asignar un precio especial para que aparezca gris
            todos_municipios.append({
                'municipio': mun_geo,
                'municipio_norm': mun_geo,
                'precio_m2': -1,  # Valor especial para municipios sin datos
            })

    df_mapa_completo = pd.DataFrame(todos_municipios)

    # Preparar escala de colores personalizada
    precio_min_real = df_mapa['precio_m2'].min()
    precio_max_real = df_mapa['precio_m2'].max()

    # Crear escala de colores personalizada: gris para -1, luego el gradiente normal
    colorscale = [
        [0, 'lightgray'],  # -1 = sin datos
        [0.001, 'lightgray'],
        [0.001, '#2d7f2e'],  # Verde (barato)
        [0.5, '#ffeb84'],    # Amarillo (medio)
        [1.0, '#d73027']     # Rojo (caro)
    ]

    # Calcular variaciones mensuales para todos los municipios
    df_sorted = df.sort_values(['municipio', 'fecha'])
    df_sorted['variacion_mensual'] = df_sorted.groupby('municipio')['precio_m2'].pct_change() * 100

    # Obtener la ultima variacion mensual para cada municipio
    df_ultimas_variaciones = df_sorted.groupby('municipio').tail(1)[['municipio', 'variacion_mensual', 'precio_m2']].copy()
    df_ultimas_variaciones = df_ultimas_variaciones.dropna(subset=['variacion_mensual'])

    # Top 5 municipios con mayores variaciones positivas y negativas
    top_5_positivas = df_ultimas_variaciones.nlargest(5, 'variacion_mensual')
    top_5_negativas = df_ultimas_variaciones.nsmallest(5, 'variacion_mensual')

    # Crear mapa coropletico de municipios
    fig_choropleth = px.choropleth_mapbox(
        df_mapa_completo,
        geojson=geojson_municipios,
        locations='municipio_norm',
        featureidkey="properties.NOMBRE",
        color='precio_m2',
        color_continuous_scale=colorscale,
        range_color=(-1, precio_max_real),
        mapbox_style="carto-positron",
        zoom=7.8,
        center={"lat": 43.25, "lon": -4.0},
        opacity=0.8,
        labels={'precio_m2': 'Precio €/m²'},
        hover_name='municipio',
        hover_data={
            'municipio': False,
            'precio_m2': ':.2f',
            'municipio_norm': False
        }
    )

    # Actualizar bordes de los municipios
    fig_choropleth.update_traces(
        marker_line_width=1.5,
        marker_line_color='white'
    )

    # Ajustar la barra de colores para que no muestre el -1
    fig_choropleth.update_coloraxes(
        colorbar=dict(
            tickvals=[precio_min_real, (precio_min_real + precio_max_real) / 2, precio_max_real],
            ticktext=[f'{precio_min_real:.0f}', f'{(precio_min_real + precio_max_real) / 2:.0f}', f'{precio_max_real:.0f}']
        )
    )

    fig_choropleth.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=700
    )

    # Layout en 3 columnas: Subidas | Mapa | Bajadas
    col_subidas, col_mapa, col_bajadas = st.columns([1, 2, 1])

    with col_subidas:
        st.markdown("### 📈 Top 5 Subidas")

        for idx, row in top_5_positivas.iterrows():
            st.markdown(f"**🔴 {row['municipio']}**")
            st.caption(f"Precio: **{row['precio_m2']:.0f} €/m²**")
            st.markdown(f"<span style='color: red; font-weight: bold; font-size: 1.2em;'>{row['variacion_mensual']:+.2f}%</span>", unsafe_allow_html=True)
            st.markdown("")  # Espacio

    with col_mapa:
        st.markdown("### 🗺️ Mapa de Precios")
        st.plotly_chart(fig_choropleth, use_container_width=True)

    with col_bajadas:
        st.markdown("### 📉 Top 5 Bajadas")

        for idx, row in top_5_negativas.iterrows():
            st.markdown(f"**🟢 {row['municipio']}**")
            st.caption(f"Precio: **{row['precio_m2']:.0f} €/m²**")
            st.markdown(f"<span style='color: green; font-weight: bold; font-size: 1.2em;'>{row['variacion_mensual']:+.2f}%</span>", unsafe_allow_html=True)
            st.markdown("")  # Espacio

except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Asegúrate de que los datos están disponibles en S3.")
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {str(e)}")
    import traceback
    st.error(f"Detalle del error: {traceback.format_exc()}")
