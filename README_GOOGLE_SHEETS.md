# Configuración de Google Sheets para Viviendas Cantabria

Esta aplicación ahora obtiene los datos directamente desde Google Sheets en lugar de archivos CSV locales.

## Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Preparar Google Sheets](#preparar-google-sheets)
3. [Configurar Google Cloud Platform](#configurar-google-cloud-platform)
4. [Configurar Credenciales Localmente](#configurar-credenciales-localmente)
5. [Configurar en Streamlit Cloud](#configurar-en-streamlit-cloud)
6. [Solución de Problemas](#solución-de-problemas)

---

## Configuración Inicial

### Requisitos Previos

- Una cuenta de Google
- Acceso a Google Cloud Platform (gratuito para comenzar)
- Los datos en archivos CSV que quieras migrar a Google Sheets

---

## Preparar Google Sheets

### 1. Crear una nueva hoja de cálculo de Google Sheets

1. Ve a [Google Sheets](https://sheets.google.com)
2. Crea una nueva hoja de cálculo
3. Nombra el documento (ej: "Datos Viviendas Cantabria")

### 2. Importar los datos CSV

Necesitas crear **dos hojas** dentro del mismo documento:

#### Hoja 1: Datos de Municipios
1. Crea una hoja llamada `precios_municipios_cantabria`
2. Importa el archivo `data/precios_municipios_cantabria.csv`:
   - Archivo > Importar > Subir
   - Selecciona tu archivo CSV
   - Tipo de importador: "Insertar hojas nuevas"
   - Separador: Detectar automáticamente

**Estructura esperada:**
```
municipio | fecha | precio_m2 | (otras columnas opcionales)
```

#### Hoja 2: Datos de Distritos de Santander
1. Crea una hoja llamada `precios_distritos_santander`
2. Importa el archivo `data/precios_distritos_santander.csv`

**Estructura esperada:**
```
distrito | fecha | precio_m2 | (otras columnas opcionales)
```

### 3. Obtener el ID del documento

En la URL de tu Google Sheet:
```
https://docs.google.com/spreadsheets/d/TU_ID_AQUI/edit
```

Copia el `TU_ID_AQUI` - lo necesitarás más adelante.

---

## Configurar Google Cloud Platform

### 1. Crear un proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Anota el **Project ID**

### 2. Habilitar las APIs necesarias

1. En el menú de navegación, ve a **APIs & Services > Library**
2. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

### 3. Crear una Cuenta de Servicio

1. Ve a **APIs & Services > Credentials**
2. Haz clic en **Create Credentials > Service Account**
3. Completa los detalles:
   - Nombre: `streamlit-sheets-reader` (o el que prefieras)
   - Descripción: "Cuenta para leer Google Sheets desde Streamlit"
4. Haz clic en **Create and Continue**
5. Rol: Selecciona **Viewer** (solo lectura)
6. Haz clic en **Continue** y luego **Done**

### 4. Crear una clave JSON

1. En la lista de cuentas de servicio, haz clic en la que acabas de crear
2. Ve a la pestaña **Keys**
3. Haz clic en **Add Key > Create New Key**
4. Selecciona **JSON**
5. Haz clic en **Create**
6. Se descargará un archivo JSON - **guárdalo en un lugar seguro**

### 5. Compartir el Google Sheet con la Cuenta de Servicio

1. Abre el archivo JSON descargado
2. Busca el campo `client_email` - tendrá un formato como:
   ```
   streamlit-sheets-reader@tu-proyecto.iam.gserviceaccount.com
   ```
3. Ve a tu Google Sheet
4. Haz clic en **Compartir** (esquina superior derecha)
5. Pega el email de la cuenta de servicio
6. Asegúrate de que tenga permisos de **Viewer** (Lector)
7. **Desmarca** "Notify people" si no quieres enviar un email
8. Haz clic en **Share**

---

## Configurar Credenciales Localmente

### 1. Crear el archivo secrets.toml

1. Copia el archivo de ejemplo:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Abre `.streamlit/secrets.toml` en tu editor de texto

### 2. Rellenar la configuración de Google Sheets

```toml
[google_sheets]
spreadsheet_id = "TU_SPREADSHEET_ID_AQUI"  # Del paso "Preparar Google Sheets"
municipios_sheet_name = "precios_municipios_cantabria"
distritos_sheet_name = "precios_distritos_santander"
```

### 3. Rellenar las credenciales de la cuenta de servicio

Abre el archivo JSON descargado y copia los valores a tu `secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto-id"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nTU_CLAVE_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-sheets-reader@tu-proyecto.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

**IMPORTANTE:**
- El archivo `secrets.toml` NO debe subirse a git (ya está en `.gitignore`)
- Ten cuidado con los saltos de línea en `private_key` - deben mantenerse como `\n`

### 4. Probar localmente

```bash
streamlit run app.py
```

Si todo está configurado correctamente, la aplicación cargará los datos desde Google Sheets.

---

## Configurar en Streamlit Cloud

### 1. Subir tu código a GitHub

Asegúrate de que tu repositorio incluya:
- `app.py` (modificado)
- `google_sheets_loader.py` (nuevo)
- `requirements.txt` (actualizado)
- `.gitignore` (debe incluir `.streamlit/secrets.toml`)

**NO subas** el archivo `secrets.toml` a GitHub.

### 2. Configurar secretos en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io/)
2. Despliega tu aplicación
3. Ve a **Settings > Secrets**
4. Copia y pega el contenido **completo** de tu archivo local `.streamlit/secrets.toml`
5. Haz clic en **Save**
6. La aplicación se reiniciará automáticamente

---

## Solución de Problemas

### Error: "Error al autenticar con Google Sheets"

**Causas posibles:**
- Las credenciales en `secrets.toml` están mal formateadas
- Falta algún campo en las credenciales
- El formato del `private_key` está incorrecto

**Solución:**
- Verifica que todos los campos del JSON estén copiados correctamente
- Asegúrate de que `private_key` mantenga los `\n` para los saltos de línea
- Compara tu `secrets.toml` con el archivo JSON original

### Error: "Insufficient Permission"

**Causas posibles:**
- No compartiste el Google Sheet con el email de la cuenta de servicio
- Los permisos son insuficientes

**Solución:**
1. Ve al Google Sheet
2. Haz clic en **Compartir**
3. Verifica que el email de la cuenta de servicio (`client_email`) esté en la lista
4. Asegúrate de que tenga permisos de **Viewer** como mínimo

### Error: "Worksheet not found"

**Causas posibles:**
- El nombre de la hoja en `secrets.toml` no coincide con el nombre en Google Sheets
- Hay espacios extra o errores tipográficos

**Solución:**
- Verifica que los nombres en `municipios_sheet_name` y `distritos_sheet_name` coincidan **exactamente** con los nombres de las hojas en Google Sheets
- Los nombres distinguen mayúsculas/minúsculas

### Error: "Google Sheets API has not been used in project"

**Causas posibles:**
- No habilitaste las APIs necesarias

**Solución:**
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a **APIs & Services > Library**
4. Busca y habilita:
   - Google Sheets API
   - Google Drive API

### Los datos no se actualizan

**Causa:**
- Streamlit cachea los datos por 10 minutos (configurado en `@st.cache_data(ttl=600)`)

**Solución:**
- Espera 10 minutos para que expire el caché
- O presiona `C` en la aplicación de Streamlit para limpiar el caché
- O modifica el parámetro `ttl` en `google_sheets_loader.py`

---

## Actualizar los Datos

Para actualizar los datos:

1. Edita directamente el Google Sheet
2. Los cambios se reflejarán en la aplicación después de 10 minutos (o al limpiar el caché)

**Ventajas de usar Google Sheets:**
- No necesitas redesplegar la aplicación para actualizar datos
- Múltiples personas pueden actualizar los datos colaborativamente
- Historial de cambios incluido en Google Sheets
- Interfaz familiar para usuarios no técnicos

---

## Estructura de Datos Requerida

### Hoja: precios_municipios_cantabria

Columnas requeridas:
- `municipio`: Nombre del municipio (texto)
- `fecha`: Fecha en formato reconocible (YYYY-MM-DD recomendado)
- `precio_m2`: Precio por metro cuadrado (número o texto numérico)

Columnas opcionales:
- `fecha_texto`: Si no existe, se genera automáticamente como YYYY-MM

### Hoja: precios_distritos_santander

Columnas requeridas:
- `distrito`: Nombre del distrito (texto)
- `fecha`: Fecha en formato reconocible
- `precio_m2`: Precio por metro cuadrado (número o texto numérico)

Columnas opcionales:
- `fecha_texto`: Si no existe, se genera automáticamente

---

## Seguridad

- **NUNCA** compartas tu archivo `secrets.toml`
- **NUNCA** subas las credenciales a un repositorio público
- Usa el archivo `.gitignore` para excluir `secrets.toml`
- Rota las claves periódicamente desde Google Cloud Console
- Usa permisos mínimos necesarios (solo lectura para esta aplicación)

---

## Recursos Adicionales

- [Documentación de Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)

---

## Soporte

Si tienes problemas:

1. Revisa la sección de **Solución de Problemas**
2. Verifica que todos los pasos se completaron correctamente
3. Revisa los logs de error en Streamlit para más detalles
