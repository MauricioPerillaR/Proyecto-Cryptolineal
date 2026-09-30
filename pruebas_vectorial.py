"""
CryptoLineal · Semana 8 — Pruebas automáticas (T16 … T26 + menú)

Casos de prueba del backlog de la Semana 8, más la regresión completa del
prototipo v1. No contiene lógica de negocio: solo comprueba la de
vectorial_modelo, vectorial_figuras, vectorial_tabla y el menú.

Uso:
  python pruebas_vectorial.py            v1 + Semana 8
  python pruebas_vectorial.py --solo-s8  solo Semana 8
"""

import contextlib
import io
import math
import os
import random
import sys
import tempfile

import cryptolineal as cl
from cryptolineal import MODULO, ErrorCryptoLineal
from vectorial_modelo import (
    TOLERANCIA,
    ErrorCapas,
    VectorR2,
    VectorZ26,
    analizar_transformacion,
    angulo,
    aplicar,
    ataque_texto_escogido,
    cifrar_como_combinacion,
    combinacion_lineal,
    comparar_angulo_reduccion,
    cosenos_directores,
    es_isotropo,
    imagen,
    imagenes_base,
    iota,
    lectura_area,
    proyeccion_modular,
    proyeccion_real,
    submodulo_generado,
    todos_los_vectores,
    vectores_isotropos,
)
from vectorial_figuras import cargar_pyplot, figuras_casos
from vectorial_tabla import FILAS_TABLA, ids_de_evidencia, tabla_comparativa


K1 = ((3, 3), (2, 5))
K2 = ((2, 4), (3, 6))
K3 = ((1, 2), (3, 4))
K4 = ((1, 1), (1, 14))
K5 = ((2, 0), (0, 2))
OMITIDA = "omitida"


def _lanza(f, tipo=ErrorCryptoLineal):
    try:
        f()
    except tipo:
        return True
    return False


def _cerca(a, b, tol=0.05):
    return abs(a - b) <= tol


def _capturar(f):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            f()
    except ErrorCryptoLineal:
        pass
    return buf.getvalue()


def _lector(entradas):
    it = iter(entradas)

    def leer(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None
    return leer


def _colision_en_letras(K):
    ker = analizar_transformacion(K)["colision"]
    return [p.letras for p in ker], {aplicar(K, p).letras for p in ker}


def _t25_4():
    try:
        cargar_pyplot()
    except ErrorCryptoLineal:
        return OMITIDA
    with tempfile.TemporaryDirectory() as d:
        res = figuras_casos(d)
        figs = [f for f in res["figuras"] if "paralelogramo" in f["ruta"]]
        mismos_ejes = len({(f["xlim"], f["ylim"]) for f in figs}) == 1
        existen = all(os.path.getsize(f["ruta"]) > 0 for f in res["figuras"])
        return len(figs) == 4 and mismos_ejes and existen and len(res["figuras"]) == 9


def _menu():
    """Importación diferida: el menú importa este módulo para su opción de pruebas."""
    import cryptolineal_vectorial
    return cryptolineal_vectorial


def casos_semana8():
    """Registro ordenado id → comprobación. Lo usan las pruebas y la tabla de HU-26."""
    c = {}

    # ── HU-16 ─────────────────────────────────────────────────────
    c["T16-1"] = lambda: VectorZ26.de("AL") == VectorZ26(0, 11)
    c["T16-2"] = lambda: VectorZ26(20, 9) + VectorZ26(10, 20) == VectorZ26(4, 3)
    c["T16-3"] = lambda: 3 * VectorZ26(10, 9) == VectorZ26(4, 1)
    c["T16-4"] = lambda: iota((0, 11)) == VectorR2(0.0, 11.0) and iota((0, 11)).capa == "ℝ²"
    c["T16-5"] = lambda: (_lanza(lambda: iota((0, 11)) + VectorZ26(1, 2), ErrorCapas)
                          and _lanza(lambda: VectorZ26(1, 2) + iota((0, 11)), ErrorCapas)
                          and _lanza(lambda: angulo(VectorZ26(1, 2), iota((3, 4))), ErrorCapas))

    # ── HU-17 ─────────────────────────────────────────────────────
    def img(K):
        r = imagenes_base(K)
        return r["Ke1"].par, r["Ke2"].par, r["letras"]
    c["T17-1"] = lambda: img(K1) == ((3, 2), (3, 5), ("DC", "DF"))
    c["T17-2"] = lambda: img(K2) == ((2, 3), (4, 6), ("CD", "EG"))
    c["T17-3"] = lambda: img(cl.IDENTIDAD) == ((1, 0), (0, 1), ("BA", "AB"))
    c["T17-4"] = lambda: (cl.cifrar("BAAB", K1).criptograma == "DCDF"
                          and ataque_texto_escogido(K1)["clave_recuperada"] == K1)

    # ── HU-18 ─────────────────────────────────────────────────────
    def comb(p):
        r = combinacion_lineal(K1, p)
        return r["p1u"], r["p2v"], r["suma"], r["c"].par
    c["T18-1"] = lambda: comb((0, 11)) == ((0, 0), (33, 55), (33, 55), (7, 3))
    c["T18-2"] = lambda: comb((6, 4)) == ((18, 12), (12, 20), (30, 32), (4, 6))
    c["T18-3"] = lambda: comb((1, 0)) == ((3, 2), (0, 0), (3, 2), (3, 2))
    c["T18-4"] = lambda: cifrar_como_combinacion("ALGEBRA", K1) == "HDEGCJRL"

    # ── HU-19 ─────────────────────────────────────────────────────
    def area(K):
        r = lectura_area(K)
        return r["cruz"], r["area"], r["det_mod"]
    c["T19-1"] = lambda: area(K1) == ((0, 0, 9), 9, 9) and not lectura_area(K1)["ciega"]
    c["T19-2"] = lambda: area(K2) == ((0, 0, 0), 0, 0) and "v = 2·u" in lectura_area(K2)["lectura"]
    c["T19-3"] = lambda: area(K3) == ((0, 0, -2), 2, 24) and lectura_area(K3)["ciega"]
    c["T19-4"] = lambda: area(K4) == ((0, 0, 13), 13, 13) and lectura_area(K4)["ciega"]

    def t19_5():
        u, v = VectorR2(3, 2), VectorR2(3, 5)
        th = angulo(u, v)["theta"]
        return (_cerca(u.norma(), 3.606, 1e-3) and _cerca(v.norma(), 5.831, 1e-3)
                and _cerca(th, 25.35, 0.01) and _cerca(lectura_area(K1)["verificacion_seno"], 9.0, 1e-9))
    c["T19-5"] = t19_5

    # ── HU-20 ─────────────────────────────────────────────────────
    c["T20-1"] = lambda: (angulo(VectorR2(3, 2), VectorR2(3, 5))["punto"] == 19
                          and _cerca(angulo(VectorR2(3, 2), VectorR2(3, 5))["theta"], 25.35, 0.01))

    def t20_2():
        r = cosenos_directores(VectorR2(3, 2))
        return (_cerca(r["cos_alfa"], 0.832, 1e-3) and _cerca(r["cos_beta"], 0.555, 1e-3)
                and _cerca(r["alfa"], 33.7, 0.05) and _cerca(r["beta"], 56.3, 0.05)
                and _cerca(r["alfa"] + r["beta"], 90, 1e-9))
    c["T20-2"] = t20_2
    c["T20-3"] = lambda: _cerca(angulo(iota((0, 11)), VectorR2(33, 55))["theta"], 31.0, 0.05)

    def t20_4():
        r = comparar_angulo_reduccion(K1, (0, 11))
        return _cerca(r["despues"], 66.8, 0.05) and r["difieren"] and r["aviso"] != ""
    c["T20-4"] = t20_4

    def t20_5():
        rng = random.Random(20)
        for _ in range(500):
            v = VectorR2(rng.uniform(-50, 50), rng.uniform(-50, 50))
            if abs(cosenos_directores(v)["suma_cuadrados"] - 1) > TOLERANCIA:
                return False
        return _lanza(lambda: cosenos_directores(VectorR2(0, 0)))
    c["T20-5"] = t20_5

    # ── HU-21 ─────────────────────────────────────────────────────
    c["T21-1"] = lambda: (_cerca(proyeccion_real(VectorR2(3, 5), VectorR2(3, 2))["escalar"], 19 / 13, 1e-12)
                          and proyeccion_real(VectorR2(3, 5), VectorR2(3, 2))["proy"]
                          .aproximadamente(VectorR2(4.385, 2.923)))
    c["T21-2"] = lambda: (proyeccion_real(VectorR2(3, 5), VectorR2(3, 2))["residuo"]
                          .aproximadamente(VectorR2(-1.385, 2.077))
                          and abs(proyeccion_real(VectorR2(3, 5), VectorR2(3, 2))["residuo_punto_v"]) < 1e-9)

    def pm(v):
        r = proyeccion_modular((3, 5), v)
        return r["definida"], r["vv"], r["mcd"]
    c["T21-3"] = lambda: pm((3, 2)) == (False, 13, 13)
    c["T21-4"] = lambda: pm((3, 5)) == (False, 8, 2)

    def t21_5():
        if pm((1, 0)) != (True, 1, 1):
            return False
        return all(proyeccion_modular((x, y), (1, 0))["proy"] == VectorZ26(x, 0)
                   for x in range(MODULO) for y in range(0, MODULO, 5))
    c["T21-5"] = t21_5

    # ── HU-22 ─────────────────────────────────────────────────────
    c["T22-1"] = lambda: VectorZ26(1, 5).punto(VectorZ26(1, 5)) == 0 and 1 + 25 == 26
    c["T22-2"] = lambda: es_isotropo((5, 1))
    c["T22-3"] = lambda: es_isotropo((13, 13)) and 13 * 13 * 2 == 338 == 13 * 26
    c["T22-4"] = lambda: not es_isotropo((3, 2)) and VectorZ26(3, 2).punto(VectorZ26(3, 2)) == 13
    c["T22-5"] = lambda: (_cerca(iota((1, 5)).norma(), math.sqrt(26), 1e-12)
                          and iota((1, 5)).punto(iota((1, 5))) == 26.0)

    def t22_6():
        r = vectores_isotropos()
        # ℤ₂₆ ≅ ℤ₂ × ℤ₁₃: 2 soluciones de x²+y²≡0 mod 2 y 25 mod 13 (−1 = 5² es cuadrado) → 50
        return (len(r["no_nulos"]) > 0 and len(r["todos"]) == 50
                and all(v.punto(v) == 0 for v in r["todos"]))
    c["T22-6"] = t22_6

    # ── HU-23 ─────────────────────────────────────────────────────
    def tam(K):
        r = analizar_transformacion(K)
        return r["tam_nucleo"], r["tam_imagen"]
    c["T23-1"] = lambda: tam(K1) == (1, 676) and analizar_transformacion(K1)["colision"] == []
    c["T23-2"] = lambda: tam(K2) == (26, 26) and _colision_en_letras(K2) == (["AA", "AN"], {"AA"})
    c["T23-3"] = lambda: tam(K3) == (2, 338) and _colision_en_letras(K3) == (["AA", "AN"], {"AA"})
    c["T23-4"] = lambda: tam(K4) == (13, 52) and _colision_en_letras(K4) == (["AA", "CY"], {"AA"})
    c["T23-5"] = lambda: (tam(K5) == (4, 169)
                          and _colision_en_letras(K5) == (["AA", "AN", "NA", "NN"], {"AA"})
                          and math.gcd(cl.determinante(K5)[1], 26) == 2
                          and not analizar_transformacion(K5)["coincide_con_mcd"])

    def t23_extra():
        rng = random.Random(23)
        for _ in range(150):
            K = cl.construir_clave([rng.randrange(26) for _ in range(4)])
            r = analizar_transformacion(K)
            if r["crt"] != r["tam_nucleo"]:
                return False
        return True
    c["T23-extra (regla CRT para |núcleo|)"] = t23_extra

    # ── HU-24 ─────────────────────────────────────────────────────
    card = lambda v: submodulo_generado(v)["cardinal"]
    c["T24-1"] = lambda: card((1, 0)) == 26
    c["T24-2"] = lambda: card((2, 3)) == 26
    c["T24-3"] = lambda: card((2, 0)) == 13
    c["T24-4"] = lambda: card((13, 0)) == 2 and submodulo_generado((13, 0))["elementos"] == {VectorZ26(0, 0), VectorZ26(13, 0)}
    c["T24-5"] = lambda: card((0, 0)) == 1

    def t24_6():
        for v in todos_los_vectores():
            r = submodulo_generado(v)
            if r["cardinal"] != r["regla"] or not r["divide_26"] or r["cardinal"] not in (1, 2, 13, 26):
                return False
        return True
    c["T24-6"] = t24_6

    # ── HU-25 ─────────────────────────────────────────────────────
    c["T25-1"] = lambda: len(imagen(K1)) == 676
    c["T25-2"] = lambda: (len(imagen(K2)) == 26 and lectura_area(K2)["area"] == 0
                          and imagen(K2) == submodulo_generado((2, 3))["elementos"])
    c["T25-3"] = lambda: len(imagen(K3)) == 338 and lectura_area(K3)["area"] == 2
    c["T25-4"] = _t25_4

    # ── HU-26 ─────────────────────────────────────────────────────
    def t26_1():
        return all(fila["verificado"] for fila in tabla_comparativa(resultados_parciales(c)))
    c["T26-1"] = t26_1
    c["T26-2"] = lambda: all(ev in c for fila in FILAS_TABLA for ev in fila[3])

    # ── Menú ─────────────────────────────────────────────────────
    c["TM-1 opción inexistente"] = lambda: "Opción no válida" in _capturar(
        lambda: _menu().ejecutar_menu(_lector(["99", "0"])))
    c["TM-2 caso 5 → núcleo de 4"] = lambda: "|núcleo| = 4" in _capturar(
        lambda: _menu().ejecutar_menu(_lector(["12", "5", "8", "", "0"])))
    c["TM-3 entrada inválida no cierra"] = lambda: "Hasta pronto" in _capturar(
        lambda: _menu().ejecutar_menu(_lector(["1", "1.5 x", "0"])))
    return c


def resultados_parciales(registro, ids=None):
    """Ejecuta comprobaciones del registro y devuelve {id: True | False | 'omitida'}."""
    salida = {}
    for id_ in (ids if ids is not None else registro):
        if id_.startswith("T26"):
            continue
        try:
            r = registro[id_]()
            salida[id_] = r if r == OMITIDA else bool(r)
        except Exception:
            salida[id_] = False
    return salida


def ejecutar_pruebas(incluir_v1=True):
    ok_v1 = True
    if incluir_v1:
        print("══ Regresión del prototipo v1 (HU-01 … HU-15) ══")
        ok_v1 = cl.ejecutar_pruebas()
        print()
    print("══ Semana 8 (HU-16 … HU-26) ══")
    registro = casos_semana8()
    resultados = []
    for id_, f in registro.items():
        try:
            r = f()
            estado, detalle = (OMITIDA, "matplotlib no instalado") if r == OMITIDA else (bool(r), "")
        except Exception as e:
            estado, detalle = False, f"excepción {type(e).__name__}: {e}"
        resultados.append((id_, estado, detalle))

    fallos = [r for r in resultados if r[1] is False]
    omitidas = [r for r in resultados if r[1] == OMITIDA]
    ejecutadas = len(resultados) - len(omitidas)
    print(f"Pruebas superadas: {ejecutadas - len(fallos)} / {ejecutadas}"
          + (f"   ({len(omitidas)} omitida(s))" if omitidas else ""))
    for id_, _, detalle in fallos:
        print(f"  ✗ {id_} {detalle}")
    for id_, _, detalle in omitidas:
        print(f"  – {id_} omitida: {detalle}")
    if not fallos:
        print("  ✓ Todas las pruebas ejecutadas pasan.")
    return ok_v1 and not fallos



def tabla_verificada():
    """HU-26: ejecuta las pruebas de evidencia y construye la tabla con su verificación."""
    return tabla_comparativa(resultados_parciales(casos_semana8(), ids_de_evidencia()))


if __name__ == "__main__":
    cl._configurar_consola()
    sys.exit(0 if ejecutar_pruebas(incluir_v1="--solo-s8" not in sys.argv[1:]) else 1)
