import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from comarcas_municipios import obtener_comarca
from coordenadas_municipios import obtener_coordenadas
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

# Titulo principal
st.title("📊 Precios del Metro Cuadrado en Cantabria")
st.markdown("### Analisis de precios inmobiliarios por municipio")

# Cargar datos
@st.cache_data
def load_data():
    # Intentar diferentes encodings
    for encoding in ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']:
        try:
            df = pd.read_csv('data/precios_municipios_cantabria.csv', encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    # Convertir fecha a datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    # Filtrar valores nulos en precio_m2
    df = df[df['precio_m2'] != '-']
    df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')
    df = df.dropna(subset=['precio_m2'])
    return df

try:
    df = load_data()

    # Agregar comarca a cada municipio
    df['comarca'] = df['municipio'].apply(obtener_comarca)

    # Obtener lista de municipios disponibles (solo los que tienen datos)
    municipios_disponibles = sorted(df['municipio'].unique())

    # Sidebar para configuracion
    st.sidebar.header("⚙️ Configuracion")

    # Selector de vista
    vista = st.sidebar.radio(
        "Selecciona vista:",
        options=["Mapa Geografico", "Mapa de Comarcas", "Series Temporales"]
    )

    if vista == "Mapa Geografico":
        st.subheader("🗺️ Mapa Geográfico de Cantabria por Municipios")

        # Obtener datos mas recientes por municipio
        df_reciente = df.sort_values('fecha').groupby('municipio').tail(1)

        # Cargar GeoJSON de municipios
        with open('data/municipios_cantabria.geojson', 'r', encoding='utf-8') as f:
            geojson_municipios = json.load(f)

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

        for mun_geo in municipios_geojson:
            if mun_geo in municipios_con_datos:
                # Municipio con datos
                todos_municipios.append(municipios_con_datos[mun_geo])
            else:
                # Municipio sin datos - asignar un precio especial para que aparezca gris
                municipios_sin_datos_count += 1
                todos_municipios.append({
                    'municipio': mun_geo,
                    'municipio_norm': mun_geo,
                    'precio_m2': -1,  # Valor especial para municipios sin datos
                    'comarca': 'Sin datos'
                })

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

    else:  # Series Temporales
        # Seleccion multiple de municipios
        municipios_seleccionados = st.sidebar.multiselect(
            "Selecciona uno o mas municipios:",
            options=municipios_disponibles,
            default=['Santander'] if 'Santander' in municipios_disponibles else [municipios_disponibles[0]]
        )

        # Tipo de visualizacion
        tipo_visualizacion = st.sidebar.radio(
            "Tipo de visualizacion:",
            options=["Precio Absoluto", "Variacion Mensual (%)", "Variacion Anual (%)"]
        )

        # Filtrar datos por municipios seleccionados
        if municipios_seleccionados:
            df_filtrado = df[df['municipio'].isin(municipios_seleccionados)].copy()
            df_filtrado = df_filtrado.sort_values(['municipio', 'fecha'])

            # Calcular variaciones segun seleccion
            if tipo_visualizacion == "Variacion Mensual (%)":
                df_filtrado['valor'] = df_filtrado.groupby('municipio')['precio_m2'].pct_change() * 100
                titulo_grafico = "Variacion Mensual del Precio por m² (%)"
                ylabel = "Variacion Mensual (%)"
            elif tipo_visualizacion == "Variacion Anual (%)":
                df_filtrado['valor'] = df_filtrado.groupby('municipio')['precio_m2'].pct_change(periods=12) * 100
                titulo_grafico = "Variacion Anual del Precio por m² (%)"
                ylabel = "Variacion Anual (%)"
            else:
                df_filtrado['valor'] = df_filtrado['precio_m2']
                titulo_grafico = "Evolucion del Precio por m²"
                ylabel = "Precio (€/m²)"

            # Crear grafico con Plotly
            fig = go.Figure()

            for municipio in municipios_seleccionados:
                df_municipio = df_filtrado[df_filtrado['municipio'] == municipio]
                fig.add_trace(go.Scatter(
                    x=df_municipio['fecha'],
                    y=df_municipio['valor'],
                    mode='lines+markers',
                    name=municipio,
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

            cols = st.columns(len(municipios_seleccionados))

            for idx, municipio in enumerate(municipios_seleccionados):
                df_municipio = df_filtrado[df_filtrado['municipio'] == municipio]

                with cols[idx]:
                    st.markdown(f"**{municipio}**")

                    if tipo_visualizacion == "Precio Absoluto":
                        precio_actual = df_municipio['precio_m2'].iloc[-1]
                        precio_anterior = df_municipio['precio_m2'].iloc[0]
                        variacion_total = ((precio_actual - precio_anterior) / precio_anterior) * 100

                        st.metric(
                            label="Precio Actual",
                            value=f"{precio_actual:.2f} €/m²",
                            delta=f"{variacion_total:.2f}%"
                        )
                        st.write(f"**Precio Minimo:** {df_municipio['precio_m2'].min():.2f} €/m²")
                        st.write(f"**Precio Maximo:** {df_municipio['precio_m2'].max():.2f} €/m²")
                        st.write(f"**Precio Medio:** {df_municipio['precio_m2'].mean():.2f} €/m²")
                    else:
                        st.write(f"**Variacion Media:** {df_municipio['valor'].mean():.2f}%")
                        st.write(f"**Variacion Minima:** {df_municipio['valor'].min():.2f}%")
                        st.write(f"**Variacion Maxima:** {df_municipio['valor'].max():.2f}%")

            # Tabla de datos
            st.markdown("---")
            with st.expander("📋 Ver tabla de datos"):
                # Preparar tabla para mostrar
                tabla_mostrar = df_filtrado[['municipio', 'fecha_texto', 'precio_m2']].copy()
                tabla_mostrar = tabla_mostrar.pivot(
                    index='fecha_texto',
                    columns='municipio',
                    values='precio_m2'
                )
                st.dataframe(tabla_mostrar, use_container_width=True)

        else:
            st.warning("⚠️ Por favor, selecciona al menos un municipio para visualizar los datos.")

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
