# 📡 Dashboard de Cobertura Móvil (Perú)

Aplicación interactiva en **Streamlit** que permite visualizar, explorar y analizar la **cobertura móvil** por tecnología (2G, 3G, 4G, 5G) a nivel de centros poblados.  
El proyecto está optimizado para trabajar con datasets grandes, usando **SQLite como cache** y consultas SQL dinámicas para mantener un rendimiento fluido incluso con archivos extensos.

---

## 🚀 Características principales

### 🧱 Arquitectura y rendimiento
- **Carga flexible** de datos (`.xlsx` o `.csv`) desde archivo local o URL.
- **ETL cacheado en SQLite**: los datos crudos se normalizan en una tabla “larga” (`coverage_long`) con índices (`tech`, `CentroPoblado`, `Ambito`).
- **Consultas SQL directas** (`SELECT ... WHERE tech = ?`) para cada visualización.
- **Caching inteligente** con `@st.cache_data` y `@st.cache_resource`.
- **Modo persistente WAL** en SQLite para lecturas rápidas.

### 📊 Visualizaciones interactivas
- **Mapa de cobertura** por tecnología (2G, 3G, 4G, 5G) con Pydeck (colores según intensidad de cobertura).
- **Estadísticas generales** de cobertura por tecnología (media, mediana, máximo, mínimo).
- **Comparación por Centro Poblado**:
  - Soporta **multiselección** de CPs.
  - Calcula estadísticas agregadas entre todos los seleccionados.
  - Opción para mostrar detalle de filas utilizadas.

### 💅 Interfaz y usabilidad
- Limpieza automática de nombres (`_pretty_cp`) → convierte etiquetas como `06_de_agosto` → `06 de agosto`.
- Sidebar de configuración: carga de datos, parámetros de rendimiento, opciones de visualización.
- Etiquetas y tooltips en español, UI responsiva y clara.

---

## 🗂️ Estructura del proyecto

#### ├── app.py # App principal de Streamlit (interfaz + visualizaciones)
#### ├── load_data.py # Lectura, cache y consultas SQL
#### ├── processing.py # Limpieza y preprocesamiento (custom del usuario)
#### ├── viz.py # Funciones auxiliares de visualización (Pydeck)
#### ├── utils.py # Decoradores y helpers generales
#### ├── data/
#### │ └── coverage.db # Cache SQLite autogenerada
#### └── reqs.txt # Dependencias del proyecto

---

## ⚙️ Instalación y ejecución
### 1️⃣ Clonar el repositorio
git clone https://github.com/tcormenof-dev/Prototipo-App-Streamlit.git
cd <tu-repo>
### 2️⃣ Crear entorno virtual (recomendado)
python -m venv .ven
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
### 3️⃣ Instalar dependencias
pip install -r requirements.txt

Dependencias principales:

streamlit

pandas

altair

pydeck

requests

sqlite3 (builtin)

### 4️⃣ Ejecutar el dashboard
streamlit run app.py

## 🧠 Cómo funciona internamente

Lectura flexible (load_data.read_data_flexible)

Acepta .xlsx o .csv desde URL o ruta local.

Si es URL, se descarga con cabecera User-Agent para evitar error 418.

Convierte automáticamente columnas como CentroPoblado a texto.

Construcción del cache SQL (build_sql_cache_long)

Normaliza los datos: columnas _CG y _CG+CAR → % cobertura por tecnología.

Genera una tabla larga:
CentroPoblado | Latitud | Longitud | Ambito | tech | pct

Crea índices para consultas rápidas.

Consultas y visualizaciones

q_map_by_tech: puntos del mapa filtrados por tecnología.

q_values_by_tech: valores por tecnología (para estadísticas globales).

q_values_by_cps: datos filtrados por varios CPs (para análisis agregados).

## 🧩 Personalización

Puedes modificar processing.py para definir tu propia función clean_df(df) si tu dataset requiere limpieza adicional.

Si tu archivo tiene otros nombres de columnas, ajusta los “id columns” en build_sql_cache_long.

Para datasets más grandes, puedes reemplazar SQLite por DuckDB sin cambiar la lógica SQL.

## 🛠️ Autor y créditos

Autor: @<tcormenof-dev>
Colaboración IA: ChatGPT (GPT-5)
Institución: Universidad de Pacífico — Proyecto de análisis de datos y automatización.

## 📜 Licencia

Este proyecto se distribuye bajo licencia MIT, por lo que puedes modificarlo y reutilizarlo libremente citando la fuente.
