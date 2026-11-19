"""Descarga los NOMBRES (etiquetas) de productos y socios que usa Eurostat Comext (DS-045409).
No modifica ninguna tabla anterior: crea dos archivos nuevos en ../datos/raw/
  comext_etiquetas_productos.csv   (codigo, descripcion)
  comext_etiquetas_socios.csv      (codigo, nombre)
Uso:  python3 descargar_etiquetas_comext.py   (desde la carpeta scripts)
"""
import csv, sys, time
from pathlib import Path
import requests

BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
OUT = Path(__file__).resolve().parent.parent / "datos" / "raw"
PRODUCTOS = ["854110","854121","854129","854130","854140","854141","854142","854143","854149",
             "854150","854151","854159","854160","854190","854231","854232","854233","854239","854290"]
MESES_PRUEBA = ["2016-01", "2018-01", "2020-01", "2022-06", "2024-01", "2025-06"]

def pedir(params):
    for n in range(4):
        try:
            r = requests.get(BASE, params=params, timeout=120)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (400, 404):
                return None
        except requests.RequestException as e:
            print("  red:", e)
        time.sleep(3 * (n + 1))
    return None

def etiquetas(js, dim):
    cat = js["dimension"][dim]["category"]
    return dict(cat.get("label", {}))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prod, soc = {}, {}
    for p in PRODUCTOS:
        for m in MESES_PRUEBA:
            js = pedir({"reporter": "ES", "flow": 1, "freq": "M", "product": p, "time": m,
                        "indicators": "VALUE_IN_EUROS", "format": "JSON", "lang": "EN"})
            if js and js.get("value"):
                prod.update(etiquetas(js, "product")); soc.update(etiquetas(js, "partner"))
                print(p, m, "ok"); break
            time.sleep(0.3)
        else:
            print(p, "sin etiqueta encontrada")
    # socios: se piden todos los socios de un producto de chips en varios meses y declarantes
    for rep in ("ES", "EU27_2020"):
        for m in MESES_PRUEBA:
            js = pedir({"reporter": rep, "flow": 1, "freq": "M", "product": "854231", "time": m,
                        "indicators": "VALUE_IN_EUROS", "format": "JSON", "lang": "EN"})
            if js:
                soc.update(etiquetas(js, "partner")); print("socios", rep, m, len(soc))
            time.sleep(0.3)
    with open(OUT / "comext_etiquetas_productos.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["codigo", "descripcion"])
        for k in sorted(prod): w.writerow([k, prod[k]])
    with open(OUT / "comext_etiquetas_socios.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["codigo", "nombre"])
        for k in sorted(soc): w.writerow([k, soc[k]])
    print("Productos:", len(prod), "| Socios:", len(soc))

if __name__ == "__main__":
    main()
