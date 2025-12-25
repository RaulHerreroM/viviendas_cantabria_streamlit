import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from comarcas_municipios import obtener_comarca
from coordenadas_municipios import obtener_coordenadas
from s3_loader import load_municipios_data, load_distritos_data, load_geojson_municipios, load_portales_data
import json
import unicodedata

# Configuracion de la pagina
st.set_page_config(
    page_title="Precios Inmobiliarios Cantabria",
    page_icon="🏠",
    layout="wide"
)

# Funcion para normalizar nombres de municipios
def normalizar_municipio(nombre):
    """Normaliza el nombre del municipio para hacer matching con el GeoJSON"""
    if pd.isna(nombre):
        return nombre

    nombre_str = str(nombre).strip()

    # Mapeo directo de nombres que difieren entre datos y GeoJSON
    mapeo_exacto = {
        # Formato "El X" -> "X (El)" y "Los X" -> "X (Los)"
        'El Astillero': 'Astillero (El)',
        'Los Corrales de Buelna': 'Corrales de Buelna (Los)',

        # Nombres con acentos diferentes
        'Barcena de Cicero': 'Bárcena de Cicero',
        'Cabezon de la Sal': 'Cabezón de la Sal',
        'Ribamontan al Mar': 'Ribamontán al Mar',
        'Ribamontan al Monte': 'Ribamontán al Monte',
        'Reocin': 'Reocín',
        'Solorzano': 'Solórzano',
        'Udias': 'Udías',
        'Valdaliga': 'Valdáliga',
        'Santa Maria de Cayon': 'Santa María de Cayón',
        'Lierganes': 'Liérganes',
        'Pielagos': 'Piélagos',

        # Nombres de distritos/localidades que no son municipios oficiales
        # Estos se mapean a sus municipios correspondientes
        'Ajo': 'Bareyo',  # Ajo es una localidad de Bareyo
        'Beranga': 'Bareyo',  # Beranga es parte de Bareyo
        'Boo': 'Piélagos',  # Boo es parte de Piélagos
        'Cudon': 'Miengo',  # Cudón es parte de Miengo
        'Guarnizo': 'Camargo',  # Guarnizo es parte de Camargo
        'Hoznayo': 'Entrambasaguas',  # Hoznayo es parte de Entrambasaguas
        'Isla': 'Arnuero',  # Isla es parte de Arnuero
        'Mogro': 'Miengo',  # Mogro es parte de Miengo
        'Pontejos': 'Marina de Cudeyo',  # Pontejos es parte de Marina de Cudeyo
        'Puente San Miguel': 'Reocín',  # Puente San Miguel es parte de Reocín
        'Solares': 'Medio Cudeyo',  # Solares es parte de Medio Cudeyo
        'Soto de la Marina': 'Marina de Cudeyo',  # Soto de la Marina es parte de Marina de Cudeyo
        'Vargas': 'Puente Viesgo',  # Vargas es parte de Puente Viesgo

        # Nombres con variaciones
        'Campoo de Enmedio': 'Enmedio',
    }

    return mapeo_exacto.get(nombre_str, nombre_str)

# Titulo principal
st.title("📊 Precios del Metro Cuadrado en Cantabria")
st.markdown("### Analisis de precios inmobiliarios por municipio")

# Cargar datos desde S3
# Nota: Las funciones load_municipios_data() y load_distritos_data()
# ya vienen con @st.cache_data del modulo s3_loader

try:
    df = load_municipios_data()
    df_distritos = load_distritos_data()
    df_portales = load_portales_data()

    # Agregar comarca a cada municipio
    df['comarca'] = df['municipio'].apply(obtener_comarca)
    df_portales['comarca'] = df_portales['municipio'].apply(obtener_comarca)

    # Obtener lista de municipios disponibles (solo los que tienen datos)
    municipios_disponibles = sorted(df['municipio'].unique())
    distritos_disponibles = sorted(df_distritos['distrito'].unique())

    # Sidebar para configuracion
    st.sidebar.header("⚙️ Configuracion")

    # Selector de vista
    vista = st.sidebar.radio(
        "Selecciona vista:",
        options=["Mapa Geografico", "Mapa de Comarcas", "Mapa Portales", "Series Temporales"]
    )

    if vista == "Mapa Geografico":
        st.subheader("🗺️ Mapa Geográfico de Cantabria por Municipios")

        # Obtener datos mas recientes por municipio
        df_reciente = df.sort_values('fecha').groupby('municipio').tail(1)

        # Cargar GeoJSON de municipios desde S3
        geojson_municipios = load_geojson_municipios()

        # Obtener todos los municipios del GeoJSON
        municipios_geojson = [f['properties']['NOMBRE'] for f in geojson_municipios['features']]

        # Preparar datos para el mapa - normalizar nombres
        df_mapa = df_reciente[['municipio', 'precio_m2', 'comarca']].copy()
        df_mapa['municipio_norm'] = df_mapa['municipio'].apply(normalizar_municipio)

        # Crear DataFrame completo con TODOS los municipios del GeoJSON
        municipios_con_datos = dict(zip(df_mapa['municipio_norm'], df_mapa.to_dict('records')))

        # Lista completa de todos los municipios
        todos_municipios = []
        municipios_sin_datos_count = 0
        municipios_con_datos_count = 0
        for mun_geo in municipios_geojson:
            if mun_geo in municipios_con_datos:
                # Municipio con datos
                todos_municipios.append(municipios_con_datos[mun_geo])
                municipios_con_datos_count += 1
            else:
                # Municipio sin datos - asignar un precio especial para que aparezca gris
                municipios_sin_datos_count += 1
                todos_municipios.append({
                    'municipio': mun_geo,
                    'municipio_norm': mun_geo,
                    'precio_m2': -1,  # Valor especial para municipios sin datos
                    'comarca': 'Sin datos'
                })

        assert municipios_con_datos_count == len(municipios_con_datos)
        df_mapa_completo = pd.DataFrame(todos_municipios)
        municipios_sin_datos = municipios_sin_datos_count > 0

        # Preparar escala de colores personalizada
        # Crear una escala que incluya gris para municipios sin datos
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
                'comarca': True,
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
            height=650
        )

        st.plotly_chart(fig_choropleth, use_container_width=True)

        # Mostrar informacion sobre municipios sin datos
        if municipios_sin_datos:
            st.info(f"ℹ️ {municipios_sin_datos_count} municipios no tienen datos de precios y aparecen en gris en el mapa.")

        st.markdown("""
        **Cómo leer este mapa:**
        - Cada zona coloreada representa un **municipio** de Cantabria
        - 🔴 **Rojo**: Municipios con precios más altos
        - 🟡 **Amarillo**: Municipios con precios medios
        - 🟢 **Verde**: Municipios con precios más bajos
        - ⚪ **Gris/Blanco**: Municipios sin datos disponibles
        - Pasa el ratón sobre cada municipio para ver detalles
        - Puedes hacer zoom y desplazarte por el mapa
        """)

        # Treemap jerarquico por comarca y municipio
        st.markdown("---")
        st.subheader("📊 Vista Detallada por Municipio")

        df_reciente_sorted = df_reciente.sort_values('precio_m2', ascending=False)

        fig_treemap = px.treemap(
            df_reciente_sorted,
            path=['comarca', 'municipio'],
            values='precio_m2',
            color='precio_m2',
            color_continuous_scale='RdYlGn_r',
            title='Distribución de Precios por Comarca y Municipio',
            labels={'precio_m2': 'Precio €/m²'},
            hover_data={'precio_m2': ':.2f'}
        )

        fig_treemap.update_traces(
            textposition='middle center',
            textfont=dict(size=11),
            marker=dict(line=dict(width=2, color='white'))
        )

        fig_treemap.update_layout(
            height=600,
            margin=dict(t=50, l=0, r=0, b=0)
        )

        st.plotly_chart(fig_treemap, use_container_width=True)

        # Mapa de calor por comarca
        st.markdown("---")
        st.subheader("📊 Comparativa de Comarcas")

        df_comarcas = df_reciente.groupby('comarca').agg({
            'precio_m2': 'mean',
            'municipio': 'count'
        }).reset_index()
        df_comarcas.columns = ['comarca', 'precio_medio', 'num_municipios']
        df_comarcas = df_comarcas.sort_values('precio_medio', ascending=True)

        fig_heatmap = px.bar(
            df_comarcas,
            y='comarca',
            x='precio_medio',
            orientation='h',
            color='precio_medio',
            color_continuous_scale='RdYlGn_r',
            text='precio_medio',
            title='Precio Medio por Comarca',
            labels={'precio_medio': 'Precio Medio €/m²', 'comarca': ''}
        )

        fig_heatmap.update_traces(
            texttemplate='%{text:.0f} €/m²',
            textposition='outside'
        )

        fig_heatmap.update_layout(
            height=500,
            showlegend=False,
            xaxis_title="Precio Medio (€/m²)",
            yaxis_title=""
        )

        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Estadisticas generales
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        precio_min = df_reciente['precio_m2'].min()
        precio_max = df_reciente['precio_m2'].max()

        with col1:
            st.metric("Municipios con datos", len(df_reciente))
        with col2:
            st.metric("Precio Medio Regional", f"{df_reciente['precio_m2'].mean():.2f} €/m²")
        with col3:
            st.metric("Rango de Precios", f"{precio_min:.0f} - {precio_max:.0f} €/m²")

        # Top 10 municipios mas caros y mas baratos
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Top 10 Municipios Más Caros")
            top_caros = df_reciente.nlargest(10, 'precio_m2')[['municipio', 'precio_m2', 'comarca']]
            for idx, row in top_caros.iterrows():
                st.write(f"**{row['municipio']}** ({row['comarca']}): {row['precio_m2']:.2f} €/m²")

        with col2:
            st.subheader("📉 Top 10 Municipios Más Baratos")
            top_baratos = df_reciente.nsmallest(10, 'precio_m2')[['municipio', 'precio_m2', 'comarca']]
            for idx, row in top_baratos.iterrows():
                st.write(f"**{row['municipio']}** ({row['comarca']}): {row['precio_m2']:.2f} €/m²")

    elif vista == "Mapa de Comarcas":
        st.subheader("🗺️ Mapa de Precios por Comarca")

        # Obtener datos mas recientes por municipio
        df_reciente = df.sort_values('fecha').groupby('municipio').tail(1)

        # Calcular precio medio por comarca
        df_comarcas = df_reciente.groupby('comarca').agg({
            'precio_m2': 'mean',
            'municipio': 'count'
        }).reset_index()
        df_comarcas.columns = ['comarca', 'precio_medio_m2', 'num_municipios']

        # Crear grafico de barras horizontal por comarca
        fig_mapa = px.bar(
            df_comarcas.sort_values('precio_medio_m2', ascending=True),
            x='precio_medio_m2',
            y='comarca',
            orientation='h',
            color='precio_medio_m2',
            color_continuous_scale='Viridis',
            labels={'precio_medio_m2': 'Precio Medio (€/m²)', 'comarca': 'Comarca'},
            title='Precio Medio por Metro Cuadrado por Comarca (Ultimo Mes Disponible)',
            text='precio_medio_m2'
        )

        fig_mapa.update_traces(
            texttemplate='%{text:.0f} €/m²',
            textposition='outside'
        )

        fig_mapa.update_layout(
            height=600,
            showlegend=False,
            xaxis_title="Precio Medio (€/m²)",
            yaxis_title="Comarca"
        )

        st.plotly_chart(fig_mapa, use_container_width=True)

        # Tabla resumen por comarca
        st.markdown("---")
        st.subheader("📊 Resumen por Comarca")

        # Crear tabla mas detallada
        df_resumen = df_reciente.groupby('comarca').agg({
            'precio_m2': ['mean', 'min', 'max', 'count']
        }).reset_index()
        df_resumen.columns = ['Comarca', 'Precio Medio', 'Precio Minimo', 'Precio Maximo', 'Num. Municipios']

        # Formatear la tabla
        df_resumen['Precio Medio'] = df_resumen['Precio Medio'].apply(lambda x: f"{x:.2f} €/m²")
        df_resumen['Precio Minimo'] = df_resumen['Precio Minimo'].apply(lambda x: f"{x:.2f} €/m²")
        df_resumen['Precio Maximo'] = df_resumen['Precio Maximo'].apply(lambda x: f"{x:.2f} €/m²")

        st.dataframe(
            df_resumen.sort_values('Comarca'),
            use_container_width=True,
            hide_index=True
        )

        # Lista de municipios por comarca
        with st.expander("📍 Ver municipios por comarca"):
            for comarca in sorted(df_reciente['comarca'].unique()):
                municipios_comarca = df_reciente[df_reciente['comarca'] == comarca].sort_values('precio_m2', ascending=False)
                st.markdown(f"**{comarca}**")
                for _, row in municipios_comarca.iterrows():
                    st.write(f"- {row['municipio']}: {row['precio_m2']:.2f} €/m²")
                st.markdown("---")

    elif vista == "Mapa Portales":
        st.subheader("🗺️ Mapa de Precios en Portales de Venta (Idealista + Fotocasa)")

        # A. Preparación de Datos
        # Obtener datos mas recientes para portales y catastro
        df_portales_reciente = df_portales.sort_values('fecha').groupby('municipio').tail(1)
        df_cadastral_reciente = df.sort_values('fecha').groupby('municipio').tail(1)

        # Eliminar duplicados por si acaso (tomando el último registro)
        df_portales_reciente = df_portales_reciente.drop_duplicates(subset=['municipio'], keep='last')
        df_cadastral_reciente = df_cadastral_reciente.drop_duplicates(subset=['municipio'], keep='last')

        # Cargar GeoJSON de municipios desde S3
        geojson_municipios = load_geojson_municipios()
        municipios_geojson = [f['properties']['NOMBRE'] for f in geojson_municipios['features']]

        # Preparar datos de portales con normalizacion
        df_portales_mapa = df_portales_reciente[['municipio', 'precio_m2', 'comarca']].copy()
        df_portales_mapa['municipio_norm'] = df_portales_mapa['municipio'].apply(normalizar_municipio)
        df_portales_mapa = df_portales_mapa.rename(columns={'precio_m2': 'precio_portales'})

        # Eliminar duplicados después de normalización
        df_portales_mapa = df_portales_mapa.drop_duplicates(subset=['municipio_norm'], keep='last')

        # Preparar datos catastrales con normalizacion
        df_cadastral_mapa = df_cadastral_reciente[['municipio', 'precio_m2']].copy()
        df_cadastral_mapa['municipio_norm'] = df_cadastral_mapa['municipio'].apply(normalizar_municipio)
        df_cadastral_mapa = df_cadastral_mapa.rename(columns={'precio_m2': 'precio_catastro'})

        # Eliminar duplicados después de normalización
        df_cadastral_mapa = df_cadastral_mapa.drop_duplicates(subset=['municipio_norm'], keep='last')

        # Merge datasets (LEFT join para mantener todos los datos de portales)
        df_merged = pd.merge(
            df_portales_mapa,
            df_cadastral_mapa[['municipio_norm', 'precio_catastro']],
            on='municipio_norm',
            how='left'
        )

        # Calcular metricas de comparacion
        df_merged['diferencia_absoluta'] = df_merged['precio_portales'] - df_merged['precio_catastro']
        df_merged['diferencia_porcentual'] = (
            (df_merged['precio_portales'] - df_merged['precio_catastro']) /
            df_merged['precio_catastro'] * 100
        ).round(2)

        # Crear texto de comparacion para hover
        def crear_texto_comparacion(row):
            if pd.isna(row['precio_catastro']):
                return "Sin datos catastrales"
            diff_pct = row['diferencia_porcentual']
            if diff_pct > 0:
                return f"+{diff_pct:.1f}% mas caro que catastro"
            elif diff_pct < 0:
                return f"{diff_pct:.1f}% mas barato que catastro"
            else:
                return "Igual que catastro"

        df_merged['texto_comparacion'] = df_merged.apply(crear_texto_comparacion, axis=1)

        # B. Dataset Completo con Todos los Municipios del GeoJSON
        municipios_con_datos = dict(zip(df_merged['municipio_norm'], df_merged.to_dict('records')))

        todos_municipios = []
        municipios_sin_datos_count = 0
        municipios_con_datos_count = 0

        for mun_geo in municipios_geojson:
            if mun_geo in municipios_con_datos:
                todos_municipios.append(municipios_con_datos[mun_geo])
                municipios_con_datos_count += 1
            else:
                municipios_sin_datos_count += 1
                todos_municipios.append({
                    'municipio': mun_geo,
                    'municipio_norm': mun_geo,
                    'precio_portales': -1,
                    'precio_catastro': None,
                    'comarca': 'Sin datos',
                    'diferencia_porcentual': None,
                    'texto_comparacion': 'Sin datos'
                })

        df_mapa_completo = pd.DataFrame(todos_municipios)
        municipios_sin_datos = municipios_sin_datos_count > 0

        # C. Crear Mapa Choropleth Principal
        # Calcular rango de precios para la escala de color (excluyendo -1)
        precio_min_real = df_merged['precio_portales'].min()
        precio_max_real = df_merged['precio_portales'].max()

        # Escala de color personalizada: gris para sin datos, verde-amarillo-rojo para precios
        colorscale = [
            [0, 'lightgray'],
            [0.001, 'lightgray'],
            [0.001, '#2d7f2e'],  # Verde (barato)
            [0.5, '#ffeb84'],     # Amarillo (medio)
            [1.0, '#d73027']      # Rojo (caro)
        ]

        # Crear mapa coropletico
        fig_choropleth = px.choropleth_mapbox(
            df_mapa_completo,
            geojson=geojson_municipios,
            locations='municipio_norm',
            featureidkey="properties.NOMBRE",
            color='precio_portales',
            color_continuous_scale=colorscale,
            range_color=(-1, precio_max_real),
            mapbox_style="carto-positron",
            zoom=7.8,
            center={"lat": 43.25, "lon": -4.0},
            opacity=0.8,
            labels={'precio_portales': 'Precio Portales €/m²'},
            hover_name='municipio',
            hover_data={
                'municipio': False,
                'precio_portales': ':.2f',
                'precio_catastro': ':.2f',
                'comarca': True,
                'texto_comparacion': True,
                'municipio_norm': False,
                'diferencia_porcentual': False
            }
        )

        # Actualizar bordes de los municipios
        fig_choropleth.update_traces(
            marker_line_width=1.5,
            marker_line_color='white'
        )

        # Ajustar la barra de colores
        fig_choropleth.update_coloraxes(
            colorbar=dict(
                tickvals=[precio_min_real, (precio_min_real + precio_max_real) / 2, precio_max_real],
                ticktext=[f'{precio_min_real:.0f}', f'{(precio_min_real + precio_max_real) / 2:.0f}', f'{precio_max_real:.0f}']
            )
        )

        fig_choropleth.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=650
        )

        st.plotly_chart(fig_choropleth, use_container_width=True)

        # Mensajes de informacion
        if municipios_sin_datos:
            st.info(f"ℹ️ {municipios_sin_datos_count} municipios no tienen datos de portales y aparecen en gris.")

        st.markdown("""
        **Cómo leer este mapa:**
        - Muestra precios de **portales de venta** (Idealista + Fotocasa)
        - 🔴 **Rojo**: Municipios con precios más altos
        - 🟡 **Amarillo**: Municipios con precios medios
        - 🟢 **Verde**: Municipios con precios más bajos
        - ⚪ **Gris**: Municipios sin datos de portales
        - Pasa el ratón para ver la **comparación con datos catastrales**
        - Puedes hacer zoom y desplazarte por el mapa
        """)

        # D. Grafico de Barras de Comparacion
        st.markdown("---")
        st.subheader("📊 Análisis de Diferencias: Portales vs. Catastro")

        # Filtrar municipios con ambos datasets
        df_comparacion = df_merged[df_merged['precio_catastro'].notna()].copy()
        df_comparacion = df_comparacion.sort_values('diferencia_porcentual', ascending=False)

        # Crear grafico de barras de comparacion
        fig_comparison = px.bar(
            df_comparacion,
            x='diferencia_porcentual',
            y='municipio',
            orientation='h',
            color='diferencia_porcentual',
            color_continuous_scale=['#2d7f2e', '#ffeb84', '#d73027'],
            color_continuous_midpoint=0,
            title='Diferencia Porcentual: Portales vs. Catastro por Municipio',
            labels={
                'diferencia_porcentual': 'Diferencia (%)',
                'municipio': 'Municipio'
            },
            hover_data={
                'precio_portales': ':.2f',
                'precio_catastro': ':.2f'
            }
        )

        fig_comparison.update_layout(
            height=800,
            xaxis_title="Diferencia Porcentual (%)",
            yaxis_title=""
        )

        st.plotly_chart(fig_comparison, use_container_width=True)

        # E. Estadisticas Resumen
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Municipios con datos portales",
                len(df_portales_reciente)
            )

        with col2:
            st.metric(
                "Precio Medio Portales",
                f"{df_merged['precio_portales'][df_merged['precio_portales'] > 0].mean():.2f} €/m²"
            )

        with col3:
            precio_medio_catastro = df_merged['precio_catastro'].mean()
            st.metric(
                "Precio Medio Catastro",
                f"{precio_medio_catastro:.2f} €/m²"
            )

        with col4:
            diferencia_media = df_comparacion['diferencia_porcentual'].mean()
            st.metric(
                "Diferencia Media",
                f"{diferencia_media:.1f}%",
                delta=f"{diferencia_media:.1f}%"
            )

        # F. Listas Top 10
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Top 10 Municipios Más Caros (Portales)")
            top_caros = df_merged[df_merged['precio_portales'] > 0].nlargest(10, 'precio_portales')
            for idx, row in top_caros.iterrows():
                st.write(
                    f"**{row['municipio']}** ({row['comarca']}): "
                    f"{row['precio_portales']:.2f} €/m² "
                    f"({row['texto_comparacion']})"
                )

        with col2:
            st.subheader("📉 Top 10 Mayores Diferencias con Catastro")
            top_diferencias = df_comparacion.nlargest(10, 'diferencia_porcentual')
            for idx, row in top_diferencias.iterrows():
                st.write(
                    f"**{row['municipio']}**: "
                    f"{row['diferencia_porcentual']:.1f}% mas caro "
                    f"({row['precio_portales']:.0f} vs {row['precio_catastro']:.0f} €/m²)"
                )

        # G. Scatter Plot de Correlacion
        st.markdown("---")
        st.subheader("📊 Correlación Portales vs. Catastro")

        fig_scatter = px.scatter(
            df_comparacion,
            x='precio_catastro',
            y='precio_portales',
            color='diferencia_porcentual',
            size='precio_portales',
            hover_name='municipio',
            hover_data={
                'comarca': True,
                'precio_catastro': ':.2f',
                'precio_portales': ':.2f',
                'diferencia_porcentual': ':.1f'
            },
            color_continuous_scale='RdYlGn_r',
            labels={
                'precio_catastro': 'Precio Catastro (€/m²)',
                'precio_portales': 'Precio Portales (€/m²)',
                'diferencia_porcentual': 'Diferencia (%)'
            },
            title='Comparación: Precios Portales vs. Catastro'
        )

        # Añadir linea de referencia diagonal (donde los precios serian iguales)
        min_precio = min(df_comparacion['precio_catastro'].min(), df_comparacion['precio_portales'].min())
        max_precio = max(df_comparacion['precio_catastro'].max(), df_comparacion['precio_portales'].max())

        fig_scatter.add_trace(
            go.Scatter(
                x=[min_precio, max_precio],
                y=[min_precio, max_precio],
                mode='lines',
                name='Referencia (Precios Iguales)',
                line=dict(dash='dash', color='gray')
            )
        )

        fig_scatter.update_layout(height=600)

        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("""
        **Interpretación:**
        - Puntos **por encima** de la línea gris: Portales más caros que catastro
        - Puntos **por debajo** de la línea gris: Portales más baratos que catastro
        - Puntos **cerca de la línea**: Precios similares entre ambas fuentes
        """)

    else:  # Series Temporales
        # Selector de tipo de zona
        tipo_zona = st.sidebar.radio(
            "Tipo de zona:",
            options=["Municipios", "Distritos de Santander"]
        )

        # Seleccion multiple segun el tipo de zona
        if tipo_zona == "Municipios":
            zonas_seleccionadas = st.sidebar.multiselect(
                "Selecciona uno o mas municipios:",
                options=municipios_disponibles,
                default=['Santander'] if 'Santander' in municipios_disponibles else [municipios_disponibles[0]]
            )
            df_usado = df
            columna_zona = 'municipio'
        else:  # Distritos de Santander
            zonas_seleccionadas = st.sidebar.multiselect(
                "Selecciona uno o mas distritos:",
                options=distritos_disponibles,
                default=[distritos_disponibles[0]] if distritos_disponibles else []
            )
            df_usado = df_distritos
            columna_zona = 'distrito'

        # Tipo de visualizacion
        tipo_visualizacion = st.sidebar.radio(
            "Tipo de visualizacion:",
            options=["Precio Absoluto", "Variacion Mensual (%)", "Variacion Anual (%)"]
        )

        # Filtrar datos por zonas seleccionadas
        if zonas_seleccionadas:
            df_filtrado = df_usado[df_usado[columna_zona].isin(zonas_seleccionadas)].copy()
            df_filtrado = df_filtrado.sort_values([columna_zona, 'fecha'])

            # Calcular variaciones segun seleccion
            if tipo_visualizacion == "Variacion Mensual (%)":
                df_filtrado['valor'] = df_filtrado.groupby(columna_zona)['precio_m2'].pct_change() * 100
                titulo_grafico = "Variacion Mensual del Precio por m² (%)"
                ylabel = "Variacion Mensual (%)"
            elif tipo_visualizacion == "Variacion Anual (%)":
                df_filtrado['valor'] = df_filtrado.groupby(columna_zona)['precio_m2'].pct_change(periods=12) * 100
                titulo_grafico = "Variacion Anual del Precio por m² (%)"
                ylabel = "Variacion Anual (%)"
            else:
                df_filtrado['valor'] = df_filtrado['precio_m2']
                titulo_grafico = "Evolucion del Precio por m²"
                ylabel = "Precio (€/m²)"

            # Crear grafico con Plotly
            fig = go.Figure()

            for zona in zonas_seleccionadas:
                df_zona = df_filtrado[df_filtrado[columna_zona] == zona]
                fig.add_trace(go.Scatter(
                    x=df_zona['fecha'],
                    y=df_zona['valor'],
                    mode='lines+markers',
                    name=zona,
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Fecha: %{x|%B %Y}<br>' +
                                 ylabel + ': %{y:.2f}<br>' +
                                 '<extra></extra>'
                ))

            fig.update_layout(
                title=titulo_grafico,
                xaxis_title="Fecha",
                yaxis_title=ylabel,
                hovermode='x unified',
                height=600,
                template='plotly_white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            # Mostrar grafico
            st.plotly_chart(fig, use_container_width=True)

            # Estadisticas resumidas
            st.markdown("---")
            st.subheader("📈 Estadisticas Resumidas")

            cols = st.columns(len(zonas_seleccionadas))

            for idx, zona in enumerate(zonas_seleccionadas):
                df_zona = df_filtrado[df_filtrado[columna_zona] == zona]

                with cols[idx]:
                    st.markdown(f"**{zona}**")

                    if tipo_visualizacion == "Precio Absoluto":
                        precio_actual = df_zona['precio_m2'].iloc[-1]
                        precio_anterior = df_zona['precio_m2'].iloc[0]
                        variacion_total = ((precio_actual - precio_anterior) / precio_anterior) * 100

                        st.metric(
                            label="Precio Actual",
                            value=f"{precio_actual:.2f} €/m²",
                            delta=f"{variacion_total:.2f}%"
                        )
                        st.write(f"**Precio Minimo:** {df_zona['precio_m2'].min():.2f} €/m²")
                        st.write(f"**Precio Maximo:** {df_zona['precio_m2'].max():.2f} €/m²")
                        st.write(f"**Precio Medio:** {df_zona['precio_m2'].mean():.2f} €/m²")
                    else:
                        st.write(f"**Variacion Media:** {df_zona['valor'].mean():.2f}%")
                        st.write(f"**Variacion Minima:** {df_zona['valor'].min():.2f}%")
                        st.write(f"**Variacion Maxima:** {df_zona['valor'].max():.2f}%")

            # Tabla de datos
            st.markdown("---")
            with st.expander("📋 Ver tabla de datos"):
                # Preparar tabla para mostrar
                tabla_mostrar = df_filtrado[[columna_zona, 'fecha_texto', 'precio_m2']].copy()
                tabla_mostrar = tabla_mostrar.pivot(
                    index='fecha_texto',
                    columns=columna_zona,
                    values='precio_m2'
                )
                st.dataframe(tabla_mostrar, use_container_width=True)

        else:
            mensaje = "municipio" if tipo_zona == "Municipios" else "distrito"
            st.warning(f"⚠️ Por favor, selecciona al menos un {mensaje} para visualizar los datos.")

except FileNotFoundError:
    st.error("❌ No se encontro el archivo de datos. Asegurate de que existe 'data/precios_municipios_cantabria.csv'")
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {str(e)}")

# Informacion adicional en sidebar
st.sidebar.markdown("---")
st.sidebar.info(
    "**ℹ️ Informacion**\n\n"
    f"Municipios con datos: {len(municipios_disponibles) if 'municipios_disponibles' in locals() else 'N/A'}\n\n"
    "Datos actualizados de precios inmobiliarios en Cantabria."
)
