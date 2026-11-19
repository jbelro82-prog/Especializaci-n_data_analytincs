"""Descarga mensual de importaciones de España por PAIS DE ORIGEN (API de DataComex,
Secretaria de Estado de Comercio) para los 19 codigos HS6 de las partidas 8541 y 8542.

Documentacion de la API: https://datacomex.comercio.es/Data/AyudaApi
Una llamada por codigo y por anio (pe=H<anio> -> los meses de ese anio), con
f=I (importaciones), pa=ALL (todos los paises), pr=TOTAL (total nacional).
Asi cada llamada es pequenia y queda lejos del limite de 1.000.000 de filas.

Uso:
  1. Inicia sesion en DataComex y pulsa "Obtener token" (pagina de ayuda de la API).
  2. python3 descargar_datacomex_api.py
     El script pide el token por pantalla (no se guarda en ningun archivo).
     Tambien se puede pasar en la variable de entorno DATACOMEX_TOKEN.

Salida: ../datos/raw/datacomex_api_import_origen_mensual.csv  (campos tal como los da la API)
        ../datos/datacomex_api_log.csv                         (una fila por llamada)
"""
import csv, getpass, os, sys, time
from pathlib import Path
import requests

BASE = "https://comercio.serviciosmin.gob.es/DatacomexAPI/ObtenerDatos"
RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "datos" / "raw" / "datacomex_api_import_origen_mensual.csv"
LOG = RAIZ / "datos" / "datacomex_api_log.csv"

PRODUCTOS = [
    # 8541 (diodos, transistores, fotovoltaica y LED)
    "854110", "854121", "854129", "854130", "854140", "854141", "854142", "854143", "854149",
    "854150", "854151", "854159", "854160", "854190",
    # 8542 (circuitos integrados)
    "854231", "854232", "854233", "854239", "854290",
]
ANIOS = range(2015, 2027)
CAMPOS = ["flujo", "periodo", "pais", "id_pais", "prov", "id_prov", "taric", "euros", "kilos", "mensaje"]


def llamar(token, taric, anio, intentos=3):
    params = {"f": "I", "pe": f"H{anio}", "pa": "ALL", "ta": taric, "pr": "TOTAL"}
    cabecera = {"Authorization": f"Bearer {token}"}
    for i in range(intentos):
        try:
            r = requests.get(BASE, params=params, headers=cabecera, timeout=120)
            if r.status_code in (401, 403):
                sys.exit(f"Token no valido o caducado (HTTP {r.status_code}). Pide uno nuevo y vuelve a ejecutar.")
            r.raise_for_status()
            js = r.json()
            # La API devuelve {"Resultados": [...]}; si viene null, la consulta supera los limites
            if isinstance(js, dict) and "Resultados" in js:
                js = js["Resultados"] if js["Resultados"] is not None else []
            return js, r.status_code
        except (requests.RequestException, ValueError) as e:
            error = str(e)
            time.sleep(5 * (i + 1))
    return None, error


def main():
    token = os.environ.get("DATACOMEX_TOKEN") or getpass.getpass("Pega el token de DataComex: ").strip()
    if not token:
        sys.exit("Sin token no se puede descargar.")

    # Prueba con una sola llamada antes de lanzar las 228
    datos, estado = llamar(token, "854231", 2023)
    if not isinstance(datos, list):
        sys.exit(f"La llamada de prueba no ha devuelto una lista de datos. Respuesta: {str(datos)[:500]} / {estado}")
    print(f"Prueba correcta: 854231 en 2023 -> {len(datos)} filas. Ejemplo: {datos[0] if datos else 'sin filas'}")

    filas_total = 0
    with open(OUT, "w", newline="", encoding="utf-8") as fo, open(LOG, "w", newline="", encoding="utf-8") as fl:
        out = csv.DictWriter(fo, fieldnames=CAMPOS, extrasaction="ignore")
        log = csv.writer(fl)
        out.writeheader()
        log.writerow(["taric", "anio", "filas", "estado"])
        for taric in PRODUCTOS:
            for anio in ANIOS:
                datos, estado = llamar(token, taric, anio)
                if datos is None or not isinstance(datos, list):
                    n, estado = 0, f"ERROR o null: {estado}"
                else:
                    n = len(datos)
                    out.writerows(datos)
                    filas_total += n
                log.writerow([taric, anio, n, estado])
                print(f"{taric} {anio}: {n} filas ({estado})")
                time.sleep(1)  # no saturar el servidor
    print(f"\nTerminado: {filas_total} filas en {OUT}")
    print(f"Revisa el log ({LOG}): los codigos antiguos y nuevos de 2022 tendran 0 filas en los anios en que no existen.")


if __name__ == "__main__":
    main()
