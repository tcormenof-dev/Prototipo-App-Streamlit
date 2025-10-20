# Prototipo-App-Streamlit
# Prototipo Streamlit – Análisis y Visualización de Datos

Este proyecto es un **dashboard interactivo en Streamlit** que permite **cargar, limpiar, explorar y visualizar datos** desde archivos CSV.  
Sirve como prototipo académico o base para futuros desarrollos analíticos con `pandas` y `Altair`.

---

## Características principales

- **Carga flexible de CSVs** (desde archivo, ruta o buffer).  
- **Limpieza automática**: normaliza strings, detecta tipos numéricos y elimina duplicados.  
- **Análisis rápido**:
  - Resumen de valores faltantes.  
  - Métricas descriptivas (filas, columnas, estadísticas).  
- **Visualización interactiva**:
  - Histogramas, barras y líneas por columna.  
  - Gráficos de barras agrupadas con agregaciones (`count`, `sum`, `mean`, `median`).  
- **Optimización de rendimiento**:  
  - Decoradores personalizados (`@log_timing`) para medir tiempos.  
  - Caché de Streamlit (`@st.cache_data`) para evitar recálculos innecesarios.  

---

## Estructura del proyecto
prototipo_streamlit/

│

├── app.py               # Script principal de Streamlit (interfaz y flujo general) 

├── load_data.py         # Funciones para leer CSVs de distintas fuentes 

├── processing.py        # Limpieza y análisis básico del DataFrame 

├── viz.py               # Gráficos interactivos con Altair 

├── utils.py             # Decoradores y utilidades (logging, timing) 

├── reqs.txt             # Dependencias del entorno 

└── README.md            # Documentación del proyecto


## Para la ejecución:
git clone https://github.com/usuario/prototipo-streamlit.git
cd prototipo-streamlit

## Se recomienda crear un entorno
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r reqs.txt

## Para ejecutar un el app
streamlit run app.py

# Uso:
Carga uno o más archivos CSV desde la barra lateral.
Ajusta el separador (sep) y encoding si es necesario.
Visualiza:
Vista previa de los datos crudos.
Tabla limpia con limpieza aplicada.
Métricas y valores faltantes.
Gráficos interactivos según la columna o agrupación seleccionada.

## Decoradores y rendimiento
El proyecto usa un decorador personalizado @log_timing (definido en utils.py) para medir el tiempo de ejecución de cada función clave y mostrarlo en consola.
Cada función también está cacheada con @st.cache_data(show_spinner=False) para mejorar el rendimiento en Streamlit.

## Dependencias principales
pandas>=2.0.0 
numpy>=1.24.0 
streamlit>=1.37.0 
pyarrow>=14.0.0 
pytest>=7.4.0
