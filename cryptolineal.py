#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoLineal — Prototipo v1
Cifrado de Hill 2×2 sobre ℤ₂₆ con traza algebraica paso a paso.

Uso:
    python cryptolineal.py             -> menú interactivo (HU-15)
    python cryptolineal.py --pruebas   -> pruebas automáticas (T01 … T15)

Solo usa la biblioteca estándar de Python 3.8 o superior.

Convenciones (ver backlog v1):
    · Alfabeto A…Z; φ(A)=0 … φ(Z)=25; Ñ→N; se quitan tildes y diéresis.
    · Cifrado:    c ≡ K·p   (mod 26)
    · Descifrado: p ≡ K⁻¹·c (mod 26), con K⁻¹ ≡ (det K)⁻¹ · adj(K)
    · Clave válida  <=>  mcd(det K, 26) = 1
    · Relleno: X (φ = 23). Decisión D-01.
    · D-03: el cifrado con clave no invertible está bloqueado por defecto;
            el menú permite forzarlo para mostrar que el mensaje no se recupera.
    · D-04: la matriz se representa como tupla de tuplas ((a, b), (c, d)).
"""

import contextlib
import io
import math
import random
import re
import sys
import unicodedata
from dataclasses import dataclass

# ════════════════════════════════════════════════════════════════════
#  Constantes y errores controlados (INV-3)
# ════════════════════════════════════════════════════════════════════

MODULO = 26
ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
RELLENO = "X"
IDENTIDAD = ((1, 0), (0, 1))


class ErrorCryptoLineal(Exception):
    """Error controlado: siempre lleva un mensaje diagnóstico legible."""


class ErrorClaveNoInvertible(ErrorCryptoLineal):
    """La clave no cumple mcd(det K, 26) = 1."""


class ErrorInterno(ErrorCryptoLineal):
    """Inconsistencia interna detectada por una comprobación propia."""


# ════════════════════════════════════════════════════════════════════
#  Traza (HU-09)
# ════════════════════════════════════════════════════════════════════

class Traza:
    """Imprime los pasos del procedimiento solo si está activada."""

    def __init__(self, activa=False):
        self.activa = activa

    def __call__(self, texto=""):
        if self.activa:
            print(texto)

    def paso(self, titulo):
        if self.activa:
            print(f"\n── {titulo} ──")


def fmt_matriz(M):
    return f"[{M[0][0]} {M[0][1]}; {M[1][0]} {M[1][1]}]"


# ════════════════════════════════════════════════════════════════════
#  Épica 1 · Codificación (HU-01, HU-02, HU-03)
# ════════════════════════════════════════════════════════════════════

def normalizar(texto, accion="codificar"):
    """HU-01: deja solo A–Z en mayúscula. Descarta lo demás sin avisar."""
    if not isinstance(texto, str):
        raise ErrorCryptoLineal("El mensaje debe ser un texto.")
    descompuesto = unicodedata.normalize("NFD", texto)   # Ñ -> N + tilde, ü -> u + diéresis
    sin_marcas = "".join(c for c in descompuesto if not unicodedata.combining(c))
    resultado = "".join(c for c in sin_marcas.upper() if c in ALFABETO)
    if not resultado:
        raise ErrorCryptoLineal(
            "El mensaje no contiene letras del alfabeto de trabajo (A–Z); "
            f"no hay nada que {accion}."
        )
    return resultado


def phi(letra):
    """HU-02: φ, letra -> entero en {0,…,25}."""
    u = letra.upper() if isinstance(letra, str) else ""
    if len(u) != 1 or u not in ALFABETO:
        raise ErrorCryptoLineal(f"φ solo está definida para las letras A–Z; se recibió {letra!r}.")
    return ALFABETO.index(u)


def phi_inv(n):
    """HU-02: φ⁻¹, entero -> letra. Reduce módulo 26 (INV-2)."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ErrorCryptoLineal(f"φ⁻¹ solo acepta enteros; se recibió {n!r}.")
    return ALFABETO[n % MODULO]


def particionar(texto):
    """
    HU-03: agrupa en digramas. Devuelve (digramas, relleno, texto_rellenado).
    Si la longitud es impar añade una única letra de relleno.
    """
    if not texto:
        raise ErrorCryptoLineal("No hay texto que particionar.")
    relleno = len(texto) % 2
    rellenado = texto + RELLENO * relleno
    digramas = [(phi(rellenado[i]), phi(rellenado[i + 1])) for i in range(0, len(rellenado), 2)]
    return digramas, relleno, rellenado


# ════════════════════════════════════════════════════════════════════
#  Épica 2 · Clave (HU-04, HU-05, HU-06)
# ════════════════════════════════════════════════════════════════════

_ENTERO = re.compile(r"[+-]?\d+")
_FORMATO = "Formato requerido: exactamente cuatro enteros a b c d (matriz K = [a b; c d])."


def construir_clave(entradas):
    """HU-04: cuatro enteros -> ((a, b), (c, d)) con cada entrada en ℤ₂₆."""
    if isinstance(entradas, str):
        elementos = entradas.replace(",", " ").replace(";", " ").split()
    else:
        try:
            elementos = list(entradas)
        except TypeError:
            raise ErrorCryptoLineal(f"Entrada no válida para la clave. {_FORMATO}") from None

    if len(elementos) != 4:
        raise ErrorCryptoLineal(f"Se recibieron {len(elementos)} valores. {_FORMATO}")

    valores = []
    for e in elementos:
        if isinstance(e, bool):
            raise ErrorCryptoLineal(f"«{e}» no es un entero. {_FORMATO}")
        if isinstance(e, int):
            valores.append(e)
        elif isinstance(e, str) and _ENTERO.fullmatch(e.strip()):
            valores.append(int(e))
        else:
            raise ErrorCryptoLineal(
                f"«{e}» no es un entero. ℤ₂₆ solo admite enteros (ni fracciones ni letras). {_FORMATO}"
            )
    a, b, c, d = (v % MODULO for v in valores)
    return ((a, b), (c, d))


def como_clave(K):
    """Acepta una clave ya construida o cualquier formato que construir_clave entienda."""
    try:
        if not isinstance(K, str) and len(K) == 2 and all(len(f) == 2 for f in K):
            return construir_clave([K[0][0], K[0][1], K[1][0], K[1][1]])
    except TypeError:
        pass
    return construir_clave(K)


def determinante(K, traza=None):
    """HU-05: devuelve (det entero, det mod 26) mostrando la sustitución."""
    t = traza or Traza(False)
    (a, b), (c, d) = como_clave(K)
    entero = a * d - b * c
    mod = entero % MODULO
    t(f"det K = a·d − b·c = {a}·{d} − {b}·{c} = {a * d} − {b * c} = {entero}")
    t(f"det K mod 26 = {entero} mod 26 = {mod}")
    return entero, mod


def validar_clave(K, traza=None):
    """
    HU-06: valida mcd(det K, 26) = 1 y diagnostica el modo de fallo.
    Devuelve un diccionario con: valida, tipo, det_entero, det_mod, mcd, motivo.
    tipo ∈ {"valida", "singular", "factor_2", "factor_13"}
    """
    t = traza or Traza(False)
    K = como_clave(K)
    t(f"Matriz clave K = {fmt_matriz(K)}")
    det_entero, det_mod = determinante(K, t)
    g = math.gcd(det_mod, MODULO)
    t(f"mcd(det K, 26) = mcd({det_mod}, 26) = {g}")

    nota_reales = (
        f" Sobre ℝ esta matriz sería invertible (det = {det_entero} ≠ 0), "
        "pero ℤ₂₆ es un anillo con divisores de cero (26 = 2·13)."
    )
    if g == 1:
        tipo = "valida"
        motivo = f"Clave válida: mcd({det_mod}, 26) = 1, así que det K = {det_mod} tiene inverso en ℤ₂₆."
    elif det_mod == 0:
        tipo = "singular"
        motivo = (
            f"Matriz singular: det K ≡ 0 (mod 26), mcd = {g}. La transformación no es inyectiva: "
            "distintos digramas producen el mismo criptograma y el mensaje no se puede recuperar."
        )
    elif det_mod % 2 == 0:
        tipo = "factor_2"
        motivo = (
            f"det K = {det_mod} es par: comparte el factor común 2 con 26 (mcd = {g}) "
            "y no tiene inverso en ℤ₂₆." + nota_reales
        )
    else:
        tipo = "factor_13"
        motivo = (
            f"det K = {det_mod} es múltiplo de 13: comparte el factor común 13 con 26 (mcd = {g}) "
            "y no tiene inverso en ℤ₂₆." + nota_reales
        )
    t(("→ " if g == 1 else "→ CLAVE RECHAZADA. ") + motivo)
    return {
        "valida": g == 1,
        "tipo": tipo,
        "det_entero": det_entero,
        "det_mod": det_mod,
        "mcd": g,
        "motivo": motivo,
    }


# ════════════════════════════════════════════════════════════════════
#  Álgebra modular de matrices (HU-07, HU-10, HU-11, HU-12)
# ════════════════════════════════════════════════════════════════════

def aplicar_matriz(M, v, traza=None, nombre="c"):
    """
    HU-07: producto matricial modular de un digrama.
    Devuelve ((sin reducir), (reducido)).
    """
    t = traza or Traza(False)
    (a, b), (c, d) = M
    x, y = v
    s1 = a * x + b * y
    s2 = c * x + d * y
    r = (s1 % MODULO, s2 % MODULO)
    t(f"  {nombre}₁ = {a}·{x} + {b}·{y} = {s1} ≡ {r[0]} (mod 26)")
    t(f"  {nombre}₂ = {c}·{x} + {d}·{y} = {s2} ≡ {r[1]} (mod 26)")
    t(f"  {nombre} = ({r[0]}, {r[1]}) → '{phi_inv(r[0])}{phi_inv(r[1])}'")
    return (s1, s2), r


cifrar_digrama = aplicar_matriz   # alias con el nombre de la HU-07


def euclides_extendido(a, b):
    """Devuelve (g, s, x, pasos) con a·s + b·x = g = mcd(a, b)."""
    r0, r1 = a, b
    s0, s1 = 1, 0
    t0, t1 = 0, 1
    pasos = []
    while r1 != 0:
        q, r = divmod(r0, r1)
        pasos.append((r0, r1, q, r))
        r0, r1 = r1, r
        s0, s1 = s1, s0 - q * s1
        t0, t1 = t1, t0 - q * t1
    return r0, s0, t0, pasos


def inverso_modular(valor, traza=None):
    """HU-10: inverso de `valor` módulo 26 por Euclides extendido, en {1,…,25}."""
    t = traza or Traza(False)
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ErrorCryptoLineal(f"El inverso modular solo se define para enteros; se recibió {valor!r}.")
    a = valor % MODULO
    g, _, x, pasos = euclides_extendido(MODULO, a)
    t(f"Euclides extendido sobre 26 y {a}:")
    for r0, r1, q, r in pasos:
        t(f"  {r0} = {q}·{r1} + {r}")
    if g != 1:
        raise ErrorCryptoLineal(
            f"{a} no tiene inverso módulo 26: mcd({a}, 26) = {g} ≠ 1 (factor común {g})."
        )
    inv = x % MODULO
    t(f"  Inverso: {a}·{inv} = {a * inv} ≡ {(a * inv) % MODULO} (mod 26)  →  ({a})⁻¹ = {inv}")
    return inv


def adjunta(K):
    """HU-11: adj(K) = [d −b; −c a] con entradas reducidas módulo 26."""
    (a, b), (c, d) = como_clave(K)
    return ((d % MODULO, (-b) % MODULO), ((-c) % MODULO, a % MODULO))


def multiplicar_matrices(A, B):
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(2)) % MODULO for j in range(2))
        for i in range(2)
    )


def construir_inversa(K, traza=None):
    """HU-12: construye K⁻¹ y comprueba K·K⁻¹ ≡ I₂. Aborta si la clave no es válida."""
    t = traza or Traza(False)
    K = como_clave(K)
    diag = validar_clave(K, t)
    if not diag["valida"]:
        raise ErrorClaveNoInvertible(diag["motivo"])

    t.paso("Inverso de det K y matriz adjunta")
    det_inv = inverso_modular(diag["det_mod"], t)
    adj = adjunta(K)
    t(f"adj(K) = [d −b; −c a] = {fmt_matriz(adj)}   (con signos reducidos: −x ≡ 26 − x)")

    Kinv = tuple(tuple((det_inv * x) % MODULO for x in fila) for fila in adj)
    t(f"K⁻¹ = (det K)⁻¹ · adj(K) = {det_inv} · {fmt_matriz(adj)} = {fmt_matriz(Kinv)}")

    prod = multiplicar_matrices(K, Kinv)
    t(f"Comprobación: K·K⁻¹ = {fmt_matriz(K)} · {fmt_matriz(Kinv)} = {fmt_matriz(prod)}")
    if prod != IDENTIDAD:
        raise ErrorInterno(
            f"Inconsistencia interna: K·K⁻¹ = {fmt_matriz(prod)} ≠ I₂. Se aborta el descifrado."
        )
    t("K·K⁻¹ ≡ I₂ ✓")
    return Kinv


# ════════════════════════════════════════════════════════════════════
#  Épicas 3 y 4 · Cifrado y descifrado (HU-08, HU-09, HU-13)
# ════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoCifrado:
    criptograma: str
    normalizado: str
    rellenado: str
    relleno: int
    clave_valida: bool


@dataclass
class ResultadoDescifrado:
    texto: str
    aviso: str


def cifrar(mensaje, K, traza=None, permitir_no_invertible=False):
    """HU-08 + HU-09: cifra el mensaje completo con la clave K."""
    t = traza or Traza(False)
    K = como_clave(K)

    t.paso("Texto normalizado")
    normalizado = normalizar(mensaje)
    t(f"Entrada     : {mensaje!r}")
    t(f"Normalizado : {normalizado}")

    t.paso("Valores φ y digramas")
    digramas, relleno, rellenado = particionar(normalizado)
    t("φ           : " + " ".join(f"{ch}={phi(ch)}" for ch in rellenado))
    t("Digramas    : " + "  ".join(f"({p}, {q})" for p, q in digramas))
    t(f"Relleno     : {relleno} letra(s)" + (f" ('{RELLENO}', φ = {phi(RELLENO)})" if relleno else ""))

    t.paso("Clave y determinante")
    diag = validar_clave(K, t)
    if not diag["valida"]:
        if not permitir_no_invertible:
            raise ErrorClaveNoInvertible(diag["motivo"])
        t("⚠ Se continúa por decisión del usuario (D-03): cifrar es posible, descifrar no.")

    t.paso("Productos matriciales c = K·p (mod 26)")
    bloques = []
    for i, p in enumerate(digramas, 1):
        t(f"Digrama {i}/{len(digramas)}: p = ({p[0]}, {p[1]}) → '{phi_inv(p[0])}{phi_inv(p[1])}'")
        _, c = aplicar_matriz(K, p, t, "c")
        bloques.append(c)

    criptograma = "".join(phi_inv(n) for c in bloques for n in c)
    t.paso("Criptograma")
    t(criptograma)
    return ResultadoCifrado(criptograma, normalizado, rellenado, relleno, diag["valida"])


def descifrar(criptograma, K, traza=None):
    """HU-13 + HU-09: descifra un criptograma con la clave K."""
    t = traza or Traza(False)
    K = como_clave(K)

    t.paso("Criptograma normalizado")
    cripto = normalizar(criptograma, accion="descifrar")
    t(f"Entrada     : {criptograma!r}")
    t(f"Normalizado : {cripto}")
    if len(cripto) % 2 != 0:
        raise ErrorCryptoLineal(
            f"El criptograma tiene longitud impar ({len(cripto)}). Un criptograma legítimo "
            "siempre tiene longitud par, porque cada digrama produce dos letras."
        )

    t.paso("Valores φ y digramas")
    digramas, _, _ = particionar(cripto)
    t("φ           : " + " ".join(f"{ch}={phi(ch)}" for ch in cripto))
    t("Digramas    : " + "  ".join(f"({p}, {q})" for p, q in digramas))

    t.paso("Clave, determinante e inversa")
    Kinv = construir_inversa(K, t)

    t.paso("Productos matriciales p = K⁻¹·c (mod 26)")
    bloques = []
    for i, c in enumerate(digramas, 1):
        t(f"Digrama {i}/{len(digramas)}: c = ({c[0]}, {c[1]}) → '{phi_inv(c[0])}{phi_inv(c[1])}'")
        _, p = aplicar_matriz(Kinv, c, t, "p")
        bloques.append(p)

    texto = "".join(phi_inv(n) for p in bloques for n in p)
    t.paso("Texto recuperado")
    t(texto)

    aviso = ""
    if texto.endswith(RELLENO):
        aviso = (
            f"La última letra ('{RELLENO}') podría ser relleno añadido al cifrar. "
            "No se elimina en silencio: si el mensaje original tenía longitud impar, sobra esa letra."
        )
    return ResultadoDescifrado(texto, aviso)


# ════════════════════════════════════════════════════════════════════
#  Épica 5 · Interacción (HU-15)
# ════════════════════════════════════════════════════════════════════

CASOS_DE_ESTUDIO = {
    "1": ("Caso 1 — clave válida (det 9, mcd 1)", ((3, 3), (2, 5))),
    "2": ("Caso 2 — matriz singular (det 0, mcd 26)", ((2, 4), (3, 6))),
    "3": ("Caso 3 — det par (det 24, mcd 2)", ((1, 2), (3, 4))),
    "4": ("Caso 4 — det múltiplo de 13 (det 13, mcd 13)", ((1, 1), (1, 14))),
}


def pedir_clave(estado, leer):
    K0 = estado["clave"]
    if K0 is not None:
        s = leer(f"Clave a b c d (Enter = usar {fmt_matriz(K0)}): ").strip()
        if not s:
            return K0
    else:
        s = leer("Clave: cuatro enteros a b c d, para K = [a b; c d]: ")
    return construir_clave(s)


def op_cifrar(estado, leer):
    mensaje = leer("Mensaje a cifrar: ")
    normalizar(mensaje)                       # falla pronto si no hay letras
    K = pedir_clave(estado, leer)

    permitir = False
    diag = validar_clave(K)
    if not diag["valida"]:
        print(f"\n✗ Clave no invertible. {diag['motivo']}")
        resp = leer("¿Cifrar de todos modos para comprobar que no se podrá descifrar? (s/n): ")
        if resp.strip().lower() not in ("s", "si", "sí"):
            print("Cifrado cancelado.")
            return
        permitir = True

    res = cifrar(mensaje, K, estado["traza"], permitir)
    print(f"\nClave             : {fmt_matriz(como_clave(K))}")
    print(f"Texto normalizado : {res.normalizado}")
    print(f"Relleno añadido   : {res.relleno} letra(s)" + (f" ('{RELLENO}')" if res.relleno else ""))
    print(f"Criptograma       : {res.criptograma}")
    if not res.clave_valida:
        print("\n⚠ Con esta clave el descifrado es imposible: la transformación no es inyectiva.")


def op_descifrar(estado, leer):
    cripto = leer("Criptograma: ")
    K = pedir_clave(estado, leer)
    res = descifrar(cripto, K, estado["traza"])
    print(f"\nClave           : {fmt_matriz(como_clave(K))}")
    print(f"Texto recuperado: {res.texto}")
    if res.aviso:
        print(f"⚠ {res.aviso}")


def op_validar(estado, leer):
    K = pedir_clave(estado, leer)
    print()
    diag = validar_clave(K, Traza(True))
    if diag["valida"]:
        print()
        construir_inversa(K, Traza(True))


def op_caso(estado, leer):
    print("\nCasos de estudio:")
    for k, (nombre, M) in CASOS_DE_ESTUDIO.items():
        print(f"  {k}. {nombre}   K = {fmt_matriz(M)}")
    eleccion = leer("Elige un caso (1-4): ").strip()
    if eleccion not in CASOS_DE_ESTUDIO:
        raise ErrorCryptoLineal("Caso inexistente. Elige un número del 1 al 4.")
    nombre, M = CASOS_DE_ESTUDIO[eleccion]
    estado["clave"] = M
    print(f"\nClave precargada: {nombre}\n")
    validar_clave(M, Traza(True))
    print("\nEsta clave se usará por defecto al cifrar, descifrar o validar (Enter en la petición de clave).")


def op_traza(estado, leer):
    estado["traza"].activa = not estado["traza"].activa
    print("Traza " + ("ACTIVADA." if estado["traza"].activa else "DESACTIVADA."))


def op_pruebas(estado, leer):
    ejecutar_pruebas()


def ejecutar_menu(leer=input):
    estado = {"traza": Traza(False), "clave": None}
    acciones = {
        "1": op_cifrar,
        "2": op_descifrar,
        "3": op_validar,
        "4": op_caso,
        "5": op_traza,
        "6": op_pruebas,
    }
    while True:
        clave = fmt_matriz(estado["clave"]) if estado["clave"] else "ninguna"
        print("\n══════════ CryptoLineal v1 · Hill 2×2 sobre ℤ₂₆ ══════════")
        print(f"Traza: {'ACTIVADA' if estado['traza'].activa else 'desactivada'}   |   Clave precargada: {clave}")
        print("  1. Cifrar un mensaje")
        print("  2. Descifrar un criptograma")
        print("  3. Validar una clave")
        print("  4. Cargar un caso de estudio")
        print("  5. Activar / desactivar la traza")
        print("  6. Ejecutar las pruebas automáticas")
        print("  0. Salir")
        try:
            opcion = leer("Opción: ").strip()
            if opcion == "0":
                print("Hasta pronto.")
                return
            if opcion in acciones:
                acciones[opcion](estado, leer)
            else:
                print("Opción no válida. Elige un número del menú.")
        except ErrorCryptoLineal as e:
            print(f"\n✗ {e}")
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo…")
            return
        except Exception as e:  # último recurso: INV-3, el programa no termina
            print(f"\n✗ Error inesperado ({type(e).__name__}): {e}")


# ════════════════════════════════════════════════════════════════════
#  Pruebas automáticas (casos T01 … T15 del backlog + HU-14)
# ════════════════════════════════════════════════════════════════════

def ejecutar_pruebas():
    K1 = ((3, 3), (2, 5))
    K2 = ((2, 4), (3, 6))
    K3 = ((1, 2), (3, 4))
    K4 = ((1, 1), (1, 14))
    resultados = []

    def v(id_, f):
        try:
            ok, detalle = bool(f()), ""
        except Exception as e:  # una excepción inesperada cuenta como fallo
            ok, detalle = False, f"excepción {type(e).__name__}: {e}"
        resultados.append((id_, ok, detalle))

    def lanza(f, tipo=ErrorCryptoLineal):
        try:
            f()
        except tipo:
            return True
        return False

    def capturar(f):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                f()
        except ErrorCryptoLineal:
            pass
        return buf.getvalue()

    def lector(entradas):
        it = iter(entradas)

        def leer(prompt=""):
            try:
                return next(it)
            except StopIteration:
                raise EOFError from None
        return leer

    # ── HU-01 ─────────────────────────────────────────────────────
    v("T01-1", lambda: normalizar("Álgebra lineal") == "ALGEBRALINEAL")
    v("T01-2", lambda: normalizar("Mañana, a las 5!") == "MANANAALAS")
    v("T01-3", lambda: normalizar("ÑOÑO") == "NONO")
    v("T01-4", lambda: normalizar("pingüino") == "PINGUINO")
    v("T01-5", lambda: normalizar(normalizar("HOLA")) == "HOLA")
    v("T01-6", lambda: lanza(lambda: normalizar(" ")))
    v("T01-7", lambda: lanza(lambda: normalizar("2024!!")))

    # ── HU-02 ─────────────────────────────────────────────────────
    v("T02-1", lambda: phi("A") == 0)
    v("T02-2", lambda: phi("Z") == 25)
    v("T02-3", lambda: phi("X") == 23)
    v("T02-4", lambda: phi_inv(13) == "N")
    v("T02-5", lambda: phi_inv(26) == "A")
    v("T02-6", lambda: phi_inv(-1) == "Z")
    v("T02-7", lambda: all(phi_inv(phi(l)) == l for l in ALFABETO)
      and sorted(phi(l) for l in ALFABETO) == list(range(26)))

    # ── HU-03 ─────────────────────────────────────────────────────
    v("T03-1", lambda: particionar("ALGEBRA")[:2] == ([(0, 11), (6, 4), (1, 17), (0, 23)], 1))
    v("T03-2", lambda: particionar("HOLA")[:2] == ([(7, 14), (11, 0)], 0))
    v("T03-3", lambda: particionar("A")[:2] == ([(0, 23)], 1))
    v("T03-4", lambda: particionar("AX")[:2] == ([(0, 23)], 0))
    v("T03-5", lambda: all(len(particionar(m)[2]) == 2 * len(particionar(m)[0])
                           for m in ("A", "AB", "ABC", "ALGEBRA", "HOLA", "Q" * 51)))

    # ── HU-04 ─────────────────────────────────────────────────────
    v("T04-1", lambda: construir_clave("3 3 2 5") == ((3, 3), (2, 5)))
    v("T04-2", lambda: construir_clave("29 -3 2 5") == ((3, 23), (2, 5)))
    v("T04-3", lambda: lanza(lambda: construir_clave("1 2 3")))
    v("T04-4", lambda: lanza(lambda: construir_clave("1 2 3 a")))
    v("T04-5", lambda: lanza(lambda: construir_clave("1.5 2 3 4")))

    # ── HU-05 ─────────────────────────────────────────────────────
    v("T05-1", lambda: determinante(K1) == (9, 9))
    v("T05-2", lambda: determinante(K2) == (0, 0))
    v("T05-3", lambda: determinante(K3) == (-2, 24))
    v("T05-4", lambda: determinante(K4) == (13, 13))
    v("T05-5", lambda: determinante(((1, 0), (0, 1))) == (1, 1))

    # ── HU-06 ─────────────────────────────────────────────────────
    def diag(K):
        d = validar_clave(K)
        return d["valida"], d["mcd"], d["tipo"]
    v("T06-1", lambda: diag(K1) == (True, 1, "valida"))
    v("T06-2", lambda: diag(K2) == (False, 26, "singular"))
    v("T06-3", lambda: diag(K3) == (False, 2, "factor_2"))
    v("T06-4", lambda: diag(K4) == (False, 13, "factor_13"))
    v("T06-5", lambda: diag(((1, 0), (0, 1))) == (True, 1, "valida"))

    # ── HU-07 ─────────────────────────────────────────────────────
    v("T07-1", lambda: aplicar_matriz(K1, (0, 11)) == ((33, 55), (7, 3)))
    v("T07-2", lambda: aplicar_matriz(K1, (6, 4)) == ((30, 32), (4, 6)))
    v("T07-3", lambda: aplicar_matriz(K1, (1, 17)) == ((54, 87), (2, 9)))
    v("T07-4", lambda: aplicar_matriz(K1, (0, 23)) == ((69, 115), (17, 11)))
    v("T07-5", lambda: aplicar_matriz(K1, (0, 0)) == ((0, 0), (0, 0)))

    # ── HU-08 ─────────────────────────────────────────────────────
    v("T08-1", lambda: cifrar("ALGEBRA", K1).criptograma == "HDEGCJRL")
    v("T08-2", lambda: cifrar("HOLA", K1).criptograma == "LGHW")
    v("T08-3", lambda: cifrar("Álgebra", K1).criptograma == "HDEGCJRL")
    v("T08-4", lambda: cifrar("HOLA", ((1, 0), (0, 1))).criptograma == "HOLA")
    v("T08-5", lambda: cifrar("AAAA", K1).criptograma == "AAAA")

    # ── HU-09 ─────────────────────────────────────────────────────
    v("T09-1", lambda: capturar(lambda: cifrar("ALGEBRA", K1, Traza(True))).count("  c = (") == 4)

    def t09_2():
        salida = capturar(lambda: cifrar("ALGEBRA", K3, Traza(True)))
        return "mcd" in salida and "Digrama " not in salida and lanza(lambda: cifrar("ALGEBRA", K3))
    v("T09-2", t09_2)

    def t09_3():
        salida = capturar(lambda: cifrar("ALGEBRA", K1))
        return salida == "" and cifrar("ALGEBRA", K1).criptograma == "HDEGCJRL"
    v("T09-3", t09_3)

    # ── HU-10 ─────────────────────────────────────────────────────
    v("T10-1", lambda: inverso_modular(9) == 3)
    v("T10-2", lambda: inverso_modular(1) == 1)
    v("T10-3", lambda: inverso_modular(25) == 25)
    v("T10-4", lambda: inverso_modular(5) == 21)
    v("T10-5", lambda: inverso_modular(17) == 23)
    v("T10-6", lambda: lanza(lambda: inverso_modular(2)))
    v("T10-7", lambda: lanza(lambda: inverso_modular(13)))
    v("T10-8", lambda: lanza(lambda: inverso_modular(0)))
    tabla = {1: 1, 3: 9, 5: 21, 7: 15, 9: 3, 11: 19, 15: 7, 17: 23, 19: 11, 21: 5, 23: 17, 25: 25}
    v("T10-9", lambda: all(inverso_modular(u) == inv and (u * inv) % 26 == 1 for u, inv in tabla.items())
      and all(math.gcd(u, 26) == 1 for u in tabla))

    # ── HU-11 ─────────────────────────────────────────────────────
    v("T11-1", lambda: adjunta(K1) == ((5, 23), (24, 3)))
    v("T11-2", lambda: adjunta(K3) == ((4, 24), (23, 1)))
    v("T11-3", lambda: adjunta(IDENTIDAD) == IDENTIDAD)

    def t11_4():
        rng = random.Random(11)
        for _ in range(2000):
            K = construir_clave([rng.randrange(26) for _ in range(4)])
            det = determinante(K)[1]
            if multiplicar_matrices(K, adjunta(K)) != ((det, 0), (0, det)):
                return False
        return True
    v("T11-4", t11_4)

    # ── HU-12 ─────────────────────────────────────────────────────
    v("T12-1", lambda: construir_inversa(K1) == ((15, 17), (20, 9))
      and multiplicar_matrices(K1, construir_inversa(K1)) == IDENTIDAD)
    v("T12-2", lambda: construir_inversa(IDENTIDAD) == IDENTIDAD)
    v("T12-3", lambda: lanza(lambda: construir_inversa(K3), ErrorClaveNoInvertible))

    def t12_4():
        rng = random.Random(12)
        n = 0
        while n < 200:
            K = construir_clave([rng.randrange(26) for _ in range(4)])
            if validar_clave(K)["valida"]:
                n += 1
                if construir_inversa(construir_inversa(K)) != K:
                    return False
        return True
    v("T12-4", t12_4)

    # ── HU-13 ─────────────────────────────────────────────────────
    def t13_1():
        r = descifrar("HDEGCJRL", K1)
        return r.texto == "ALGEBRAX" and r.aviso != ""
    v("T13-1", t13_1)
    v("T13-2", lambda: descifrar("LGHW", K1).texto == "HOLA" and descifrar("LGHW", K1).aviso == "")
    v("T13-3", lambda: lanza(lambda: descifrar("HDEGCJR", K1)))
    v("T13-4", lambda: lanza(lambda: descifrar("HDEGCJRL", K3), ErrorClaveNoInvertible))
    v("T13-5", lambda: descifrar("HDEGCJRL", ((5, 3), (2, 3))).texto != "ALGEBRAX")

    # ── HU-14 ─────────────────────────────────────────────────────
    mensajes = ["ALGEBRA", "HOLA", "A", "AX", "Mañana temprano"]

    def t14_1():
        for m in mensajes:
            esperado = normalizar(m) + (RELLENO if len(normalizar(m)) % 2 else "")
            if descifrar(cifrar(m, K1).criptograma, K1).texto != esperado:
                return False
            for K in (K2, K3, K4):
                if not lanza(lambda: cifrar(m, K), ErrorClaveNoInvertible):
                    return False
        return True
    v("T14-1", t14_1)

    def t14_2():
        rng = random.Random(2026)
        validas = rechazadas = 0
        for _ in range(3000):
            K = construir_clave([rng.randrange(26) for _ in range(4)])
            if not validar_clave(K)["valida"]:
                rechazadas += 1
                continue
            validas += 1
            n = rng.randint(1, 40)
            m = "".join(rng.choice(ALFABETO) for _ in range(n))
            esperado = m + (RELLENO if n % 2 else "")
            c = cifrar(m, K).criptograma
            if descifrar(c, K).texto != esperado:
                return False
            # INV-1: toda salida numérica está en {0,…,25}
            if not all(0 <= x < 26 for x in aplicar_matriz(K, (rng.randrange(26), rng.randrange(26)))[1]):
                return False
        return 0.60 < rechazadas / (validas + rechazadas) < 0.70   # ≈ 65,6 % esperado
    v("T14-2", t14_2)
    v("T14-3", lambda: descifrar(cifrar("Q", K1).criptograma, K1).texto == "QX")

    def t14_4():
        rng = random.Random(4)
        m = "".join(rng.choice(ALFABETO) for _ in range(251))
        c = cifrar(m, K1).criptograma
        return len(c) == 252 and descifrar(c, K1).texto == m + RELLENO
    v("T14-4", t14_4)

    def dato_invertibles():
        n = sum(
            1
            for a in range(26) for b in range(26) for c in range(26) for d in range(26)
            if math.gcd((a * d - b * c) % 26, 26) == 1
        )
        return n == 157248
    v("T14-dato (157 248 de 456 976 matrices son invertibles)", dato_invertibles)

    # ── HU-15 ─────────────────────────────────────────────────────
    v("T15-1", lambda: "Opción no válida" in capturar(lambda: ejecutar_menu(lector(["9", "0"]))))
    v("T15-2", lambda: "[1 2; 3 4]" in (s := capturar(lambda: ejecutar_menu(lector(["4", "3", "0"]))))
      and "factor común 2" in s)
    v("T15-3", lambda: "Hasta pronto" in capturar(lambda: ejecutar_menu(lector(["0"]))))
    v("T15-4 (entrada inválida no cierra el programa)",
      lambda: "Hasta pronto" in capturar(lambda: ejecutar_menu(lector(["1", "2024!!", "0"]))))

    # ── Informe ───────────────────────────────────────────────────
    fallos = [r for r in resultados if not r[1]]
    print(f"\nPruebas superadas: {len(resultados) - len(fallos)} / {len(resultados)}")
    for id_, _, detalle in fallos:
        print(f"  ✗ {id_} {detalle}")
    if not fallos:
        print("  ✓ Todas las pruebas pasan.")
    return not fallos


# ════════════════════════════════════════════════════════════════════
#  Punto de entrada
# ════════════════════════════════════════════════════════════════════

def _configurar_consola():
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    _configurar_consola()
    if "--pruebas" in sys.argv[1:]:
        sys.exit(0 if ejecutar_pruebas() else 1)
    ejecutar_menu()