# ¿Existe riesgo de dependencia de proveedores en las importaciones de chips de España?

**Previsión de la demanda y selección de proveedores** 📉

Proyecto final · IT Academy · Data Analytics · Jessica Beltran · Noviembre de 2026 🎓

La crisis de chips de 2021–2022 paró parte de la industria española, que depende casi por completo de importarlos. Este proyecto mide esa dependencia, prevé la demanda de chips y propone cómo repartir las compras entre proveedores para reducir el riesgo. "Chips" son los semiconductores y circuitos integrados (partidas HS 8541 y 8542), sin fotovoltaica ni LED.

##🎯Objetivos e hipótesis 

| Objetivo | Hipótesis | Resultado |
|---|---|---|
| 1.🌍Riesgo de dependencia | H1: el origen está concentrado en pocos países y una parte importante es asiática | 🟡Se confirma en parte: concentración baja por país (HHI 1,290.03), pero Asia sube del 30.21 % al 41.72 % del valor tras la crisis (Mann-Whitney, p < 0.001) |
| 2.📈 Previsión de la demanda (kg) | H2: un modelo de machine learning prevé mejor que seasonal naive y Holt-Winters |❌No se confirma: XGBoost no supera a Holt-Winters; la combinación de los tres es la más precisa (MASE 1.32) y prevé 16.07 millones de kg para 2026 |
| 3.🤝 Selección de proveedores | H3: hay proveedores alternativos para repartir la demanda entre más países |🟢 Se confirma con matices: un reparto entre 24 países con un tope del 40 % por país y Asia ≤ 15 % baja el HHI en kg de 2,571.46 a 1,700.86, con un 9.80 % más de coste |

El resultado se aplica a una empresa ficticia de automoción que compra el 1 % de las importaciones españolas de chips.

##📁Estructura del repositorio

```
proyecto_semiconductores/
├── 1_eda.ipynb                 # Exploración de los datos
├── 2_ modelo_datos.ipynb       # Limpieza y modelo en estrella
├── 3_ analisis.ipynb           # Resultado 1 (dependencia) y puntuación de proveedores
├── 4_prevision.ipynb           # Resultado 2 (previsión) y reparto de la demanda
├── Resumen.py                  # Dashboard de Streamlit: página principal
├── pages/                      # Dashboard: Dependencia, Previsión, Proveedores, Caso de negocio
├── utils.py                    # Funciones comunes del dashboard
├── scripts/                    # Descarga de datos (Datacomex y Eurostat Comext)
├── datos/
│   ├── raw/                    # Datos originales descargados (no se modifican)
│   ├── procesados/             # Tablas limpias (modelo en estrella) y resultados
│   └── *_log.csv               # Registro de las descargas
├── informe/                    # Informe final en PDF
└── requirements.txt
```

##🗂️Datos

| Fuente | Uso | Archivo en `datos/raw` |
|---|---|---|
| Datacomex (Secretaría de Estado de Comercio), API | Importaciones mensuales de España por país de origen, en € y kg, 19 códigos HS6, enero 2015 – agosto 2026 | `datacomex_api_import_origen_mensual.csv` |
| Eurostat Comext (DS-045409) | Importaciones por país de expedición, para comparar | `comext_*_mensual.csv` |
| INE, Tablas Input-Output 2022 | Contexto sectorial: quién usa la electrónica importada | `cne_tio_22.xlsx` |
| INE, índice de precios de importación | Variable de prueba en la previsión | `indice_precios_ine.csv` |

Se usan años completos (2015–2025); enero–agosto de 2026 solo sirve para comprobar la previsión.

###⭐Tablas procesadas (`datos/procesados`)

- **Modelo en estrella:** `hechos_origen`, `hechos_expedicion_es`, `hechos_expedicion_ue` (hechos) y `dim_fecha`, `dim_pais_origen`, `dim_producto`, `dim_socio_comext` (dimensiones). Agregados de Comext aparte: `comext_agregados_es`, `comext_agregados_ue`.
- **Contexto sectorial:** `tio_cpa26`, `tio_importado`, `tio_ramas`, `tio_total`.
- **Resultados:** `proveedores_puntuados`, `prevision_2026`, `evaluacion_modelos`, `reparto_propuesto`, `escenarios_asia`.

##🔬Métodos

- **Dependencia:** índice de Herfindahl-Hirschman (HHI), CR3, número equivalente de proveedores, análisis ABC (80 / 95 %) y prueba U de Mann-Whitney.
- **Previsión:** seasonal naive, Holt-Winters (logaritmo, tendencia amortiguada), XGBoost con retardos y la combinación de los tres; evaluación con MASE en origen móvil (9 orígenes, horizonte 12 meses) y comprobación con 2026.
- **Proveedores:** matriz ABC-XYZ (2023–2025), puntuación ponderada (volumen, estabilidad, coste y riesgo de región) y reparto proporcional con topes por país y para Asia.

##▶️Cómo ejecutarlo

1. Instalar las librerías (Python 3.10 o superior):
   ```bash
   pip install -r requirements.txt
   ```
   En Mac, XGBoost necesita además `brew install libomp`.
2. Ejecutar los notebooks en orden: `1_eda` → `2_ modelo_datos` → `3_ analisis` → `4_prevision`. Los datos ya están descargados en `datos/raw`, así que no hace falta volver a descargarlos.
3. Abrir el dashboard desde la carpeta del proyecto:
   ```bash
   python3 -m streamlit run Resumen.py
   ```

Para volver a descargar los datos de Datacomex hace falta un token personal de su API. El script `scripts/descargar_datacomex_api.py` lo pide por pantalla (o lo lee de la variable de entorno `DATACOMEX_TOKEN`) y no lo guarda en ningún archivo.


