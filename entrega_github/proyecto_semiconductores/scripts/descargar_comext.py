"""Descarga mensual de importaciones de España (Eurostat Comext, DS-045409)
para los codigos HS6 de las partidas 8541 y 8542, por pais socio.
Uso:  python3 descargar_comext.py              -> Espana (ES)
      python3 descargar_comext.py EU27_2020    -> Union Europea (27 paises, composicion actual)
Salida: ../datos/raw/comext_<declarante>_import_mensual.csv  y  comext_<declarante>_log.csv
"""
import csv, itertools, sys, time
from pathlib import Path
import requests

BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
OUT = Path(__file__).resolve().parent.parent / "datos" / "raw"
PRODUCTOS = [
    # 8541 (diodos, transistores, fotovoltaicas): solo codigos con datos (comprobado en la descarga de ES)
    "854110","854121","854129","854130","854140","854141","854142","854143","854149",
    "854150","854151","854159","854160","854190",
    # 8542 (circuitos integrados)
    "854231","854232","854233","854239","854290",
]
REPORTER = sys.argv[1] if len(sys.argv) > 1 else "ES"
ANIOS = range(2015, 2027)

def parse_jsonstat(js):
    """JSON-stat 2.0 -> lista de dicts. El indice plano recorre la ultima dimension mas rapido."""
    ids, sizes = js["id"], js["size"]
    cats = []
    for d in ids:
        idx = js["dimension"][d]["category"]["index"]
        if isinstance(idx, list):
            idx = {c: i for i, c in enumerate(idx)}
        cats.append(sorted(idx, key=idx.get))
    vals = js.get("value", {})
    if isinstance(vals, list):
        vals = {str(i): v for i, v in enumerate(vals) if v is not None}
    filas = {}
    for k, v in vals.items():
        k = int(k)
        pos = []
        for s in reversed(sizes):
            pos.append(k % s); k //= s
        pos.reverse()
        rec = {d: cats[i][p] for i, (d, p) in enumerate(zip(ids, pos))}
        clave = tuple(rec[d] for d in ids if d != "indicators")
        fila = filas.setdefault(clave, {d: rec[d] for d in ids if d != "indicators"})
        fila[rec["indicators"]] = v
    return list(filas.values())

def pedir(producto, anio, intentos=4):
    params = {"reporter": REPORTER, "flow": 1, "freq": "M", "product": producto,
              "sinceTimePeriod": f"{anio}-01", "untilTimePeriod": f"{anio}-12",
              "format": "JSON", "lang": "EN"}
    for n in range(intentos):
        try:
            r = requests.get(BASE, params=params, timeout=120)
            if r.status_code == 200:
                return r.status_code, r.json()
            if r.status_code in (400, 404):      # codigo inexistente o sin datos
                return r.status_code, None
        except requests.RequestException as e:
            print("  red:", e)
        time.sleep(3 * (n + 1))
    return None, None

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    columnas = ["periodo","reporter","partner","product","flow","VALUE_IN_EUROS","QUANTITY_IN_100KG","SUPPLEMENTARY_QUANTITY"]
    with open(OUT / f"comext_{REPORTER.lower()}_import_mensual.csv", "w", newline="") as f, \
         open(OUT / f"comext_{REPORTER.lower()}_log.csv", "w", newline="") as g:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore"); w.writeheader()
        lg = csv.writer(g); lg.writerow(["producto","anio","http","filas"])
        for p, a in itertools.product(PRODUCTOS, ANIOS):
            http, js = pedir(p, a)
            filas = parse_jsonstat(js) if js and js.get("value") else []
            for r in filas:
                r["periodo"] = r.pop("time"); w.writerow(r)
            lg.writerow([p, a, http, len(filas)]); g.flush(); f.flush()
            print(p, a, http, len(filas)); time.sleep(0.5)

if __name__ == "__main__":
    main()
