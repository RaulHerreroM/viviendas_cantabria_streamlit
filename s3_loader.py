"""
Modulo para cargar datos desde AWS S3
"""
import streamlit as st
import pandas as pd
import boto3
import json
from io import BytesIO
import os

def get_s3_config():
    """
    Obtiene la configuracion de S3 desde secrets.toml o variables de entorno
    """
    # Intentar obtener desde secrets de Streamlit
    try:
        aws_config = {
            'region_name': st.secrets.get("aws", {}).get("aws_region", "eu-west-1")
        }

        # Solo agregar credenciales si estan en secrets
        if "aws" in st.secrets:
            if "aws_access_key_id" in st.secrets["aws"]:
                aws_config['aws_access_key_id'] = st.secrets["aws"]["aws_access_key_id"]
            if "aws_secret_access_key" in st.secrets["aws"]:
                aws_config['aws_secret_access_key'] = st.secrets["aws"]["aws_secret_access_key"]

        bucket = st.secrets.get("s3", {}).get("bucket_name", "viviendas-cantabria-raul")

        return aws_config, bucket
    except:
        # Fallback a valores por defecto o variables de entorno
        aws_config = {
            'region_name': os.environ.get('AWS_REGION', 'eu-west-1')
        }

        # boto3 usara automaticamente las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY
        # o el archivo ~/.aws/credentials si existen

        bucket = os.environ.get('S3_BUCKET', 'viviendas-cantabria-raul')

        return aws_config, bucket

@st.cache_data(ttl=600)  # Cache por 10 minutos
def load_parquet_from_s3(s3_key):
    """
    Carga un archivo parquet desde S3

    Args:
        s3_key: Ruta del archivo en S3 (ej: 'raw/precios_distritos_santander.parquet')

    Returns:
        DataFrame de pandas con los datos
    """
    try:
        # Obtener configuracion
        aws_config, bucket = get_s3_config()

        # Crear cliente S3
        s3_client = boto3.client('s3', **aws_config)

        # Descargar el archivo
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)

        # Leer el contenido como parquet
        df = pd.read_parquet(BytesIO(response['Body'].read()))

        return df

    except Exception as e:
        st.error(f"Error al cargar datos desde S3 ({s3_key}): {str(e)}")
        raise e

@st.cache_data(ttl=600)  # Cache por 10 minutos
def load_json_from_s3(s3_key):
    """
    Carga un archivo JSON desde S3

    Args:
        s3_key: Ruta del archivo en S3 (ej: 'raw/municipios_cantabria.geojson')

    Returns:
        Diccionario con el contenido JSON
    """
    try:
        # Obtener configuracion
        aws_config, bucket = get_s3_config()

        # Crear cliente S3
        s3_client = boto3.client('s3', **aws_config)

        # Descargar el archivo
        response = s3_client.get_object(Bucket=bucket, Key=s3_key)

        # Leer el contenido como JSON
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)

        return data

    except Exception as e:
        st.error(f"Error al cargar JSON desde S3 ({s3_key}): {str(e)}")
        raise e

@st.cache_data(ttl=600)
def load_municipios_data():
    """
    Carga datos de precios por municipios desde S3
    """
    try:
        # Cargar datos desde S3
        df = load_parquet_from_s3('raw/precios_municipios_cantabria.parquet')

        # Renombrar columna 'distrito' a 'municipio' si es necesario
        if 'distrito' in df.columns and 'municipio' not in df.columns:
            df = df.rename(columns={'distrito': 'municipio'})

        # Procesar datos
        df['fecha'] = pd.to_datetime(df['fecha'])

        # El parquet ya deberia tener precio_m2 como numerico
        # pero lo verificamos por si acaso
        if df['precio_m2'].dtype == 'object':
            df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')

        df = df.dropna(subset=['precio_m2'])

        # Generar fecha_texto si no existe
        if 'fecha_texto' not in df.columns:
            df['fecha_texto'] = df['fecha'].dt.strftime('%Y-%m')

        return df

    except Exception as e:
        st.error(f"Error al procesar datos de municipios: {str(e)}")
        raise e

@st.cache_data(ttl=600)
def load_distritos_data():
    """
    Carga datos de precios por distritos de Santander desde S3
    """
    try:
        # Cargar datos desde S3
        df = load_parquet_from_s3('raw/precios_distritos_santander.parquet')

        # Procesar datos
        df['fecha'] = pd.to_datetime(df['fecha'])

        # El parquet ya deberia tener precio_m2 como numerico
        # pero lo verificamos por si acaso
        if df['precio_m2'].dtype == 'object':
            df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')

        df = df.dropna(subset=['precio_m2'])

        # Generar fecha_texto si no existe
        if 'fecha_texto' not in df.columns:
            df['fecha_texto'] = df['fecha'].dt.strftime('%Y-%m')

        return df

    except Exception as e:
        st.error(f"Error al procesar datos de distritos: {str(e)}")
        raise e

def load_geojson_municipios():
    """
    Carga el archivo GeoJSON de municipios desde S3
    """
    try:
        return load_json_from_s3('raw/municipios_cantabria.geojson')
    except Exception as e:
        st.error(f"Error al cargar GeoJSON de municipios: {str(e)}")
        raise e

@st.cache_data(ttl=600)
def load_portales_data():
    """
    Carga datos de precios de portales de venta (Idealista + Fotocasa) desde S3
    """
    try:
        # Cargar datos desde S3
        df = load_parquet_from_s3('raw/precios_municipios_cantabria_portales_de_venta.parquet')

        # Renombrar columna 'distrito' a 'municipio' si es necesario
        if 'distrito' in df.columns and 'municipio' not in df.columns:
            df = df.rename(columns={'distrito': 'municipio'})

        # Renombrar columna de precio: puede ser precio_m2_medio o precio_m2
        if 'precio_m2_medio' in df.columns:
            df = df.rename(columns={'precio_m2_medio': 'precio_m2'})
        elif 'precio_m2_mediano' in df.columns and 'precio_m2' not in df.columns:
            df = df.rename(columns={'precio_m2_mediano': 'precio_m2'})

        # Procesar fecha si existe
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'])
            # Generar fecha_texto si no existe
            if 'fecha_texto' not in df.columns:
                df['fecha_texto'] = df['fecha'].dt.strftime('%Y-%m')
        else:
            # Si no hay fecha, crear una fecha ficticia (datos actuales)
            import datetime
            df['fecha'] = pd.to_datetime(datetime.date.today())
            df['fecha_texto'] = df['fecha'].dt.strftime('%Y-%m')

        # El parquet ya deberia tener precio_m2 como numerico
        # pero lo verificamos por si acaso
        if 'precio_m2' in df.columns:
            if df['precio_m2'].dtype == 'object':
                df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')

            df = df.dropna(subset=['precio_m2'])
        else:
            raise ValueError("No se encontro columna de precio (precio_m2, precio_m2_medio o precio_m2_mediano)")

        return df

    except Exception as e:
        st.error(f"Error al procesar datos de portales: {str(e)}")
        raise e

@st.cache_data(ttl=600)
def load_secciones_santander_portales_data():
    """
    Carga datos de precios por secciones censales de Santander (Portales)
    """
    try:
        df = load_parquet_from_s3('raw/precios_secciones_santander_portales_de_venta.parquet')

        # Renombrar precio_m2_medio a precio_m2 para consistencia
        if 'precio_m2_medio' in df.columns:
            df = df.rename(columns={'precio_m2_medio': 'precio_m2'})

        # Asegurar tipos correctos
        if df['precio_m2'].dtype == 'object':
            df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')

        df = df.dropna(subset=['precio_m2'])
        return df

    except Exception as e:
        st.error(f"Error al procesar datos de secciones Santander: {str(e)}")
        raise e

@st.cache_data(ttl=600)
def load_geojson_santander():
    """
    Carga el archivo GeoJSON de secciones censales de Santander
    """
    try:
        return load_json_from_s3('raw/santander.geojson')
    except Exception as e:
        st.error(f"Error al cargar GeoJSON de Santander: {str(e)}")
        raise e
