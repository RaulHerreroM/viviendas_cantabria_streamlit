"""
Modulo para cargar datos desde Google Sheets
"""
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# Definir los scopes necesarios para Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

@st.cache_resource
def get_google_sheets_client():
    """
    Crea y retorna un cliente autenticado de Google Sheets
    Usa las credenciales almacenadas en secrets de Streamlit
    """
    try:
        # Obtener credenciales desde Streamlit secrets
        credentials_dict = dict(st.secrets["gcp_service_account"])

        # Crear credenciales
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )

        # Crear cliente de gspread
        client = gspread.authorize(credentials)
        return client

    except Exception as e:
        st.error(f"Error al autenticar con Google Sheets: {str(e)}")
        st.info("""
        **Configuracion requerida:**

        Para usar Google Sheets necesitas:
        1. Crear un proyecto en Google Cloud Console
        2. Habilitar Google Sheets API y Google Drive API
        3. Crear una cuenta de servicio y descargar el JSON de credenciales
        4. Compartir tu hoja de Google Sheets con el email de la cuenta de servicio
        5. Configurar las credenciales en `.streamlit/secrets.toml`

        Consulta README_GOOGLE_SHEETS.md para instrucciones detalladas.
        """)
        raise e

@st.cache_data(ttl=600)  # Cache por 10 minutos
def load_sheet_data(_client, spreadsheet_id, worksheet_name):
    """
    Carga datos desde una hoja especifica de Google Sheets

    Args:
        _client: Cliente autenticado de gspread
        spreadsheet_id: ID del documento de Google Sheets
        worksheet_name: Nombre de la hoja dentro del documento

    Returns:
        DataFrame de pandas con los datos
    """
    try:
        # Abrir el documento
        spreadsheet = _client.open_by_key(spreadsheet_id)

        # Obtener la hoja especifica
        worksheet = spreadsheet.worksheet(worksheet_name)

        # Obtener todos los valores
        data = worksheet.get_all_values()

        # Convertir a DataFrame (primera fila como headers)
        if len(data) > 0:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"Error al cargar datos de la hoja '{worksheet_name}': {str(e)}")
        raise e

@st.cache_data(ttl=600)
def load_municipios_data():
    """
    Carga datos de precios por municipios desde Google Sheets
    """
    try:
        # Obtener cliente
        client = get_google_sheets_client()

        # Obtener configuracion de secrets
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        municipios_sheet = st.secrets["google_sheets"]["municipios_sheet_name"]

        # Cargar datos
        df = load_sheet_data(client, spreadsheet_id, municipios_sheet)

        # Procesar datos
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df[df['precio_m2'] != '-']
        df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')
        df = df.dropna(subset=['precio_m2'])

        # Generar fecha_texto si no existe
        if 'fecha_texto' not in df.columns:
            df['fecha_texto'] = df['fecha'].dt.strftime('%Y-%m')

        return df

    except KeyError as e:
        st.error(f"Falta configuracion en secrets.toml: {str(e)}")
        st.info("Asegurate de configurar 'spreadsheet_id' y 'municipios_sheet_name' en [google_sheets]")
        raise e

@st.cache_data(ttl=600)
def load_distritos_data():
    """
    Carga datos de precios por distritos de Santander desde Google Sheets
    """
    try:
        # Obtener cliente
        client = get_google_sheets_client()

        # Obtener configuracion de secrets
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        distritos_sheet = st.secrets["google_sheets"]["distritos_sheet_name"]

        # Cargar datos
        df = load_sheet_data(client, spreadsheet_id, distritos_sheet)

        # Procesar datos
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df[df['precio_m2'] != '-']
        df['precio_m2'] = pd.to_numeric(df['precio_m2'], errors='coerce')
        df = df.dropna(subset=['precio_m2'])

        # Generar fecha_texto si no existe
        if 'fecha_texto' not in df.columns:
            df['fecha_texto'] = df['fecha'].dt.strftime('%Y-%m')

        return df

    except KeyError as e:
        st.error(f"Falta configuracion en secrets.toml: {str(e)}")
        st.info("Asegurate de configurar 'spreadsheet_id' y 'distritos_sheet_name' en [google_sheets]")
        raise e
