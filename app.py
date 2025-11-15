import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Mapa de Calor - Viviendas Cantabria",
    page_icon="🏠",
    layout="wide"
)

# Título principal
st.title("🏠 Mapa de Calor de Viviendas en Cantabria")
st.markdown("### Análisis de Precio por Metro Cuadrado")

# Función para cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('data/data_prueba.csv')

    # Calcular precio por metro cuadrado
    df['precio_m2'] = df['precio'] / df['m2_construidos']

    # Extraer municipio de la ubicación
    df['municipio'] = df['ubicacion'].apply(lambda x: x.split('|')[-2].strip() if pd.notna(x) and '|' in x else 'Desconocido')

    # Limpiar datos nulos en coordenadas
    df = df.dropna(subset=['latitud', 'longitud', 'precio_m2'])

    return df

# Cargar datos
try:
    df = load_data()

    # Sidebar con filtros
    st.sidebar.header("⚙️ Filtros")

    # Filtro por municipio
    municipios = ['Todos'] + sorted(df['municipio'].unique().tolist())
    municipio_seleccionado = st.sidebar.selectbox("Selecciona Municipio", municipios)

    # Filtro por rango de precio
    precio_min = int(df['precio'].min())
    precio_max = int(df['precio'].max())
    rango_precio = st.sidebar.slider(
        "Rango de Precio (€)",
        precio_min,
        precio_max,
        (precio_min, precio_max)
    )

    # Filtro por habitaciones
    habitaciones = st.sidebar.multiselect(
        "Número de Habitaciones",
        options=sorted(df['habitaciones'].dropna().unique()),
        default=sorted(df['habitaciones'].dropna().unique())
    )

    # Aplicar filtros
    df_filtered = df.copy()

    if municipio_seleccionado != 'Todos':
        df_filtered = df_filtered[df_filtered['municipio'] == municipio_seleccionado]

    df_filtered = df_filtered[
        (df_filtered['precio'] >= rango_precio[0]) &
        (df_filtered['precio'] <= rango_precio[1])
    ]

    if habitaciones:
        df_filtered = df_filtered[df_filtered['habitaciones'].isin(habitaciones)]

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Propiedades", len(df_filtered))

    with col2:
        avg_price = df_filtered['precio'].mean()
        st.metric("Precio Promedio", f"€{avg_price:,.0f}")

    with col3:
        avg_price_m2 = df_filtered['precio_m2'].mean()
        st.metric("Precio/m² Promedio", f"€{avg_price_m2:,.0f}")

    with col4:
        avg_size = df_filtered['m2_construidos'].mean()
        st.metric("Tamaño Promedio", f"{avg_size:.0f} m²")

    st.markdown("---")

    # Crear dos columnas para el mapa y estadísticas
    col_map, col_stats = st.columns([2, 1])

    with col_map:
        st.subheader("📍 Mapa de Calor por Precio/m²")

        # Verificar si hay datos para mostrar
        if len(df_filtered) > 0:
            # Crear mapa centrado en Cantabria
            center_lat = df_filtered['latitud'].mean()
            center_lon = df_filtered['longitud'].mean()

            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=10,
                tiles='OpenStreetMap'
            )

            # Preparar datos para el mapa de calor
            heat_data = []

            # Normalizar precio_m2 para el mapa de calor
            min_precio_m2 = df_filtered['precio_m2'].min()
            max_precio_m2 = df_filtered['precio_m2'].max()

            for idx, row in df_filtered.iterrows():
                # Normalizar el peso entre 0 y 1
                if max_precio_m2 > min_precio_m2:
                    peso = (row['precio_m2'] - min_precio_m2) / (max_precio_m2 - min_precio_m2)
                else:
                    peso = 0.5

                heat_data.append([row['latitud'], row['longitud'], peso])

                # Añadir marcador con información
                color = 'red' if row['precio_m2'] > avg_price_m2 else 'blue' if row['precio_m2'] < avg_price_m2 * 0.8 else 'orange'

                popup_html = f"""
                <div style="font-family: Arial; font-size: 12px; width: 200px;">
                    <b>{row['municipio']}</b><br>
                    <b>Precio:</b> €{row['precio']:,.0f}<br>
                    <b>Precio/m²:</b> €{row['precio_m2']:,.0f}<br>
                    <b>Tamaño:</b> {row['m2_construidos']:.0f} m²<br>
                    <b>Habitaciones:</b> {int(row['habitaciones']) if pd.notna(row['habitaciones']) else 'N/A'}<br>
                    <b>Baños:</b> {int(row['banos']) if pd.notna(row['banos']) else 'N/A'}
                </div>
                """

                folium.CircleMarker(
                    location=[row['latitud'], row['longitud']],
                    radius=8,
                    popup=folium.Popup(popup_html, max_width=250),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.7
                ).add_to(m)

            # Añadir capa de mapa de calor
            if heat_data:
                plugins.HeatMap(
                    heat_data,
                    min_opacity=0.3,
                    max_zoom=13,
                    radius=25,
                    blur=25,
                    gradient={
                        0.0: 'blue',
                        0.3: 'lime',
                        0.5: 'yellow',
                        0.7: 'orange',
                        1.0: 'red'
                    }
                ).add_to(m)

            # Añadir control de capas
            folium.LayerControl().add_to(m)

            # Mostrar mapa
            st_folium(m, width=800, height=600)

            # Leyenda
            st.markdown("""
            **Leyenda del Mapa:**
            - 🔴 Rojo: Precio/m² por encima del promedio
            - 🟠 Naranja: Precio/m² cerca del promedio
            - 🔵 Azul: Precio/m² por debajo del promedio (más de 20%)
            - Mapa de calor: Intensidad según precio/m² (azul=bajo, rojo=alto)
            """)
        else:
            st.warning("No hay datos disponibles con los filtros seleccionados.")

    with col_stats:
        st.subheader("📊 Estadísticas")

        if len(df_filtered) > 0:
            # Gráfico de distribución de precio/m²
            fig_hist = px.histogram(
                df_filtered,
                x='precio_m2',
                nbins=20,
                title='Distribución de Precio/m²',
                labels={'precio_m2': 'Precio/m² (€)', 'count': 'Frecuencia'},
                color_discrete_sequence=['#1f77b4']
            )
            fig_hist.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)

            # Gráfico de precio por municipio
            if len(df_filtered['municipio'].unique()) > 1:
                precio_municipio = df_filtered.groupby('municipio')['precio_m2'].mean().sort_values(ascending=False)

                fig_bar = px.bar(
                    x=precio_municipio.values,
                    y=precio_municipio.index,
                    orientation='h',
                    title='Precio/m² Promedio por Municipio',
                    labels={'x': 'Precio/m² (€)', 'y': 'Municipio'},
                    color=precio_municipio.values,
                    color_continuous_scale='Reds'
                )
                fig_bar.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            # Tabla de estadísticas detalladas
            st.markdown("#### Estadísticas Detalladas")
            stats_df = df_filtered.groupby('municipio').agg({
                'precio': 'mean',
                'precio_m2': 'mean',
                'm2_construidos': 'mean',
                'habitaciones': 'mean'
            }).round(0)

            stats_df.columns = ['Precio Promedio (€)', 'Precio/m² (€)', 'Tamaño (m²)', 'Habitaciones']
            st.dataframe(stats_df, use_container_width=True)

    # Sección de datos detallados
    st.markdown("---")
    st.subheader("📋 Datos Detallados")

    # Mostrar tabla con datos filtrados
    if len(df_filtered) > 0:
        display_df = df_filtered[[
            'municipio', 'precio', 'precio_m2', 'm2_construidos',
            'habitaciones', 'banos', 'direccion'
        ]].copy()

        display_df.columns = [
            'Municipio', 'Precio (€)', 'Precio/m² (€)', 'Tamaño (m²)',
            'Habitaciones', 'Baños', 'Dirección'
        ]

        display_df = display_df.round(0)
        st.dataframe(display_df, use_container_width=True, height=300)

        # Botón de descarga
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos filtrados (CSV)",
            data=csv,
            file_name='viviendas_cantabria_filtrado.csv',
            mime='text/csv'
        )

except FileNotFoundError:
    st.error("❌ No se encontró el archivo de datos. Por favor, asegúrate de que existe el archivo 'data/data_prueba.csv'")
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Mapa de Calor de Viviendas en Cantabria | Datos actualizados</p>
</div>
""", unsafe_allow_html=True)
