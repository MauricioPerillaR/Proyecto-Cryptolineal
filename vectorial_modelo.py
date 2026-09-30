"""
CryptoLineal · Semana 8 — Lógica de negocio (HU-16 … HU-24)

Reformulación vectorial y geométrica del cifrado de Hill. Sin menú, sin pruebas
y sin dependencias externas: solo cálculo, con traza opcional (INV-4).

Estrategia de dos capas:
  · ℤ₂₆² es un módulo libre de rango 2 sobre ℤ₂₆ (no un espacio vectorial).
    Aquí vive la aritmética del cifrado.                       → VectorZ26
  · La geometría métrica (norma, ángulo, área, proyección) se hace en ℝ²,
    elevando con ι: ℤ₂₆² → ℝ² a los representantes en {0,…,25}. → VectorR2
  · Mezclar capas sin elevar lanza ErrorCapas (T16-5).
"""

import math
from dataclasses import dataclass

import cryptolineal as cl
from cryptolineal import (
    MODULO,
    ErrorCryptoLineal,
    ErrorInterno,
    Traza,
    aplicar_matriz,
    como_clave,
    fmt_matriz,
    phi,
    phi_inv,
)

TOTAL_PUNTOS = MODULO * MODULO      # |ℤ₂₆²| = 676
TOLERANCIA = 1e-9


# ════════════════════════════════════════════════════════════════════
#  Errores y utilidades de formato
# ════════════════════════════════════════════════════════════════════

class ErrorCapas(ErrorCryptoLineal):
    """Se intentó operar un vector de ℤ₂₆² con uno de ℝ² (o con algo sin capa)."""


def fmt_num(x, decimales=3):
    """Número real con coma decimal, como en el informe."""
    if abs(x - round(x)) < TOLERANCIA:
        return str(int(round(x)))
    return f"{x:.{decimales}f}".replace(".", ",")


def fmt_par(par, decimales=3):
    return f"({fmt_num(par[0], decimales)}, {fmt_num(par[1], decimales)})"


def _es_entero(n):
    return isinstance(n, int) and not isinstance(n, bool)


def _es_real(n):
    return isinstance(n, (int, float)) and not isinstance(n, bool)


# ════════════════════════════════════════════════════════════════════
#  Épica 6 · Representación vectorial (HU-16)
# ════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class VectorZ26:
    """Elemento del módulo ℤ₂₆². Las componentes se guardan reducidas (INV-1, INV-2)."""
    x: int
    y: int

    capa = "ℤ₂₆²"

    def __post_init__(self):
        for n in (self.x, self.y):
            if not _es_entero(n):
                raise ErrorCryptoLineal(
                    f"Las componentes de un vector de ℤ₂₆² deben ser enteras; se recibió {n!r}."
                )
        object.__setattr__(self, "x", self.x % MODULO)
        object.__setattr__(self, "y", self.y % MODULO)

    # ── construcción ──────────────────────────────────────────────
    @classmethod
    def desde_letras(cls, digrama):
        if not isinstance(digrama, str) or len(digrama) != 2:
            raise ErrorCryptoLineal(f"Un digrama son exactamente dos letras; se recibió {digrama!r}.")
        return cls(phi(digrama[0]), phi(digrama[1]))

    @classmethod
    def de(cls, obj):
        """Acepta VectorZ26, un par de enteros o un digrama de letras."""
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, VectorR2):
            raise ErrorCapas("Se esperaba un vector de ℤ₂₆² y se recibió uno de ℝ² (capa real).")
        if isinstance(obj, str):
            return cls.desde_letras(obj.strip().upper())
        try:
            a, b = obj
        except (TypeError, ValueError):
            raise ErrorCryptoLineal(f"No se puede interpretar {obj!r} como vector de ℤ₂₆².") from None
        return cls(a, b)

    # ── representaciones ─────────────────────────────────────────
    @property
    def par(self):
        return (self.x, self.y)

    @property
    def letras(self):
        return phi_inv(self.x) + phi_inv(self.y)

    def columna(self):
        return f"⎡{self.x:>2}⎤\n⎣{self.y:>2}⎦"

    def __iter__(self):
        return iter(self.par)

    def __str__(self):
        return f"({self.x}, {self.y})"

    # ── operaciones de módulo ────────────────────────────────────
    def _comprobar_capa(self, otro, op):
        if not isinstance(otro, VectorZ26):
            capa = "ℝ²" if isinstance(otro, VectorR2) else f"sin capa ({type(otro).__name__})"
            raise ErrorCapas(
                f"No se mezclan capas: {self} ∈ ℤ₂₆² {op} {otro!s} ∈ {capa}. "
                "Eleva con ι para trabajar en ℝ², o convierte el otro operando a ℤ₂₆²."
            )

    def __add__(self, otro):
        self._comprobar_capa(otro, "+")
        return VectorZ26(self.x + otro.x, self.y + otro.y)

    __radd__ = __add__

    def __sub__(self, otro):
        self._comprobar_capa(otro, "−")
        return VectorZ26(self.x - otro.x, self.y - otro.y)

    def __neg__(self):
        return VectorZ26(-self.x, -self.y)

    def __mul__(self, k):
        if not _es_entero(k):
            raise ErrorCapas(
                f"En ℤ₂₆² los escalares son enteros módulo 26; se recibió {k!r}. "
                "Para escalares reales, eleva el vector con ι."
            )
        return VectorZ26(k * self.x, k * self.y)

    __rmul__ = __mul__

    def punto(self, otro):
        """Producto escalar FORMAL: x₁x₂ + y₁y₂ (mod 26). No mide longitudes ni ángulos (HU-22)."""
        self._comprobar_capa(otro, "·")
        return (self.x * otro.x + self.y * otro.y) % MODULO

    def elevar(self):
        return VectorR2(float(self.x), float(self.y))


@dataclass(frozen=True)
class VectorR2:
    """Vector de la capa real ℝ²: aquí sí tienen sentido norma, ángulo, área y proyección."""
    x: float
    y: float

    capa = "ℝ²"

    def __post_init__(self):
        for n in (self.x, self.y):
            if not _es_real(n):
                raise ErrorCryptoLineal(f"Las componentes de un vector de ℝ² deben ser números; se recibió {n!r}.")
        object.__setattr__(self, "x", float(self.x))
        object.__setattr__(self, "y", float(self.y))

    @property
    def par(self):
        return (self.x, self.y)

    def __iter__(self):
        return iter(self.par)

    def __str__(self):
        return fmt_par(self.par)

    def _comprobar_capa(self, otro, op):
        if not isinstance(otro, VectorR2):
            capa = "ℤ₂₆²" if isinstance(otro, VectorZ26) else f"sin capa ({type(otro).__name__})"
            raise ErrorCapas(
                f"No se mezclan capas: {self} ∈ ℝ² {op} {otro!s} ∈ {capa}. "
                "Eleva el operando modular con ι antes de operar en ℝ²."
            )

    def __add__(self, otro):
        self._comprobar_capa(otro, "+")
        return VectorR2(self.x + otro.x, self.y + otro.y)

    __radd__ = __add__

    def __sub__(self, otro):
        self._comprobar_capa(otro, "−")
        return VectorR2(self.x - otro.x, self.y - otro.y)

    def __neg__(self):
        return VectorR2(-self.x, -self.y)

    def __mul__(self, k):
        if not _es_real(k):
            raise ErrorCapas(f"En ℝ² los escalares son números reales; se recibió {k!r}.")
        return VectorR2(k * self.x, k * self.y)

    __rmul__ = __mul__

    def punto(self, otro):
        self._comprobar_capa(otro, "·")
        return self.x * otro.x + self.y * otro.y

    def norma(self):
        return math.hypot(self.x, self.y)

    def aproximadamente(self, otro, tol=1e-3):
        return abs(self.x - otro.x) <= tol and abs(self.y - otro.y) <= tol


def iota(v):
    """ι: ℤ₂₆² → ℝ². Única puerta entre las dos capas."""
    return VectorZ26.de(v).elevar()


elevar = iota


def representar_digrama(digrama, traza=None):
    """HU-16: muestra un digrama como par ordenado, como columna y como letras."""
    t = traza or Traza(False)
    v = VectorZ26.de(digrama)
    t(f"Digrama '{v.letras}'")
    t(f"  como par ordenado : {v}  ∈ ℤ₂₆²")
    t("  como columna      :")
    for linea in v.columna().splitlines():
        t("    " + linea)
    t(f"  elevado ι(p)      : {v.elevar()}  ∈ ℝ²  (capa real)")
    return v


# ════════════════════════════════════════════════════════════════════
#  HU-17 · Las columnas de K como imágenes de la base canónica
# ════════════════════════════════════════════════════════════════════

E1 = VectorZ26(1, 0)
E2 = VectorZ26(0, 1)


def columnas(K):
    """Columnas u = (a, c) y v = (b, d) de K, como vectores de ℤ₂₆²."""
    (a, b), (c, d) = como_clave(K)
    return VectorZ26(a, c), VectorZ26(b, d)


def aplicar(K, p):
    """K·p (mod 26) como VectorZ26, reutilizando el producto de HU-07."""
    _, r = aplicar_matriz(como_clave(K), VectorZ26.de(p).par)
    return VectorZ26(*r)


def imagenes_base(K, traza=None):
    """HU-17: K·e₁ y K·e₂ coinciden con las columnas de K."""
    t = traza or Traza(False)
    K = como_clave(K)
    u, v = columnas(K)
    Ke1, Ke2 = aplicar(K, E1), aplicar(K, E2)
    t(f"K = {fmt_matriz(K)}")
    t(f"  K·e₁ = K·(1, 0) = {Ke1}  → '{Ke1.letras}'   primera columna u = {u}  "
      + ("✓" if Ke1 == u else "✗"))
    t(f"  K·e₂ = K·(0, 1) = {Ke2}  → '{Ke2.letras}'   segunda columna v = {v}  "
      + ("✓" if Ke2 == v else "✗"))
    if Ke1 != u or Ke2 != v:
        raise ErrorInterno("Inconsistencia interna: las imágenes de la base no coinciden con las columnas de K.")
    t("  La matriz registra a dónde va cada dirección básica: sus columnas SON K·e₁ y K·e₂.")
    return {"Ke1": Ke1, "Ke2": Ke2, "u": u, "v": v, "letras": (Ke1.letras, Ke2.letras)}


def ataque_texto_escogido(K, traza=None):
    """
    HU-17 / T17-4: cifrar "BAAB" = e₁ e₂ devuelve la clave escrita en letras.
    Se permite cifrar aunque la clave no sea invertible: el ataque no necesita invertir nada.
    """
    t = traza or Traza(False)
    K = como_clave(K)
    cripto = cl.cifrar("BAAB", K, permitir_no_invertible=True).criptograma
    u = VectorZ26.desde_letras(cripto[0:2])
    v = VectorZ26.desde_letras(cripto[2:4])
    recuperada = ((u.x, v.x), (u.y, v.y))
    t("Texto plano escogido: 'BAAB' = e₁ e₂ = (1, 0) (0, 1)")
    t(f"Criptograma         : {cripto}  → columnas {u} y {v}")
    t(f"Clave reconstruida  : {fmt_matriz(recuperada)}  "
      + ("= K ✓" if recuperada == K else "≠ K ✗"))
    t("Hallazgo: con dos digramas escogidos el atacante lee la clave sin invertir nada.")
    return {"criptograma": cripto, "clave_recuperada": recuperada, "coincide": recuperada == K}


# ════════════════════════════════════════════════════════════════════
#  HU-18 · El cifrado como combinación lineal
# ════════════════════════════════════════════════════════════════════

def combinacion_lineal(K, p, traza=None):
    """
    HU-18: c = p₁·u + p₂·v. Devuelve los múltiplos sin reducir, la suma y c,
    y comprueba que c coincide con K·p de HU-07.
    """
    t = traza or Traza(False)
    K = como_clave(K)
    p = VectorZ26.de(p)
    u, v = columnas(K)
    p1u = (p.x * u.x, p.x * u.y)                 # sobre los representantes, sin reducir
    p2v = (p.y * v.x, p.y * v.y)
    suma = (p1u[0] + p2v[0], p1u[1] + p2v[1])
    c = VectorZ26(*suma)
    t(f"  p₁·u = {p.x}·{u} = {fmt_par(p1u)}")
    t(f"  p₂·v = {p.y}·{v} = {fmt_par(p2v)}")
    t(f"  suma = {fmt_par(suma)} ≡ {c} (mod 26) → '{c.letras}'")
    sin_reducir, reducido = aplicar_matriz(K, p.par)
    if reducido != c.par or sin_reducir != suma:
        raise ErrorInterno(
            f"Inconsistencia interna: combinación lineal {c} ≠ K·p {reducido} (HU-07)."
        )
    t("  ✓ coincide con K·p calculado como producto matricial (HU-07)")
    return {"p1u": p1u, "p2v": p2v, "suma": suma, "c": c}


def cifrar_como_combinacion(mensaje, K, traza=None, permitir_no_invertible=False):
    """HU-18: cifra el mensaje completo como combinaciones lineales y contrasta con HU-08."""
    t = traza or Traza(False)
    K = como_clave(K)
    normalizado = cl.normalizar(mensaje)
    digramas, relleno, rellenado = cl.particionar(normalizado)
    diag = cl.validar_clave(K)
    if not diag["valida"] and not permitir_no_invertible:
        raise cl.ErrorClaveNoInvertible(diag["motivo"])

    u, v = columnas(K)
    t.paso("El cifrado como combinación lineal c = p₁·u + p₂·v")
    t(f"K = {fmt_matriz(K)}   u = {u}   v = {v}")
    bloques = []
    for i, p in enumerate(digramas, 1):
        t(f"Digrama {i}/{len(digramas)}: p = {fmt_par(p)} → '{phi_inv(p[0])}{phi_inv(p[1])}'")
        bloques.append(combinacion_lineal(K, p, t)["c"])
    criptograma = "".join(c.letras for c in bloques)

    referencia = cl.cifrar(mensaje, K, permitir_no_invertible=permitir_no_invertible).criptograma
    t.paso("Contraste con HU-08")
    t(f"Combinación lineal : {criptograma}")
    t(f"Producto matricial : {referencia}")
    if criptograma != referencia:
        raise ErrorInterno("Inconsistencia interna: las dos lecturas del cifrado no coinciden.")
    t("✓ Las dos lecturas del mismo cálculo coinciden.")
    return criptograma


# ════════════════════════════════════════════════════════════════════
#  Épica 7 · Lectura geométrica sobre ℝ² (HU-19, HU-20, HU-21)
# ════════════════════════════════════════════════════════════════════

def producto_vectorial(a, b):
    """Producto vectorial en ℝ³."""
    a1, a2, a3 = a
    b1, b2, b3 = b
    return (a2 * b3 - a3 * b2, a3 * b1 - a1 * b3, a1 * b2 - a2 * b1)


def _requiere_real(*vs):
    for w in vs:
        if isinstance(w, VectorZ26):
            raise ErrorCapas(
                f"{w} está en ℤ₂₆²: la geometría métrica solo se hace en ℝ². Eleva primero con ι."
            )
        if not isinstance(w, VectorR2):
            raise ErrorCapas(f"Se esperaba un vector de ℝ²; se recibió {w!r}.")


def angulo(u, v, traza=None):
    """HU-20: u·v, normas, cos θ y θ en grados. Solo en la capa real."""
    t = traza or Traza(False)
    _requiere_real(u, v)
    nu, nv = u.norma(), v.norma()
    if nu < TOLERANCIA or nv < TOLERANCIA:
        raise ErrorCryptoLineal("El ángulo no está definido si alguno de los vectores es nulo.")
    pu = u.punto(v)
    cos = max(-1.0, min(1.0, pu / (nu * nv)))
    theta = math.degrees(math.acos(cos))
    t(f"  u·v = {fmt_num(u.x)}·{fmt_num(v.x)} + {fmt_num(u.y)}·{fmt_num(v.y)} = {fmt_num(pu)}")
    t(f"  ‖u‖ = {fmt_num(nu)}   ‖v‖ = {fmt_num(nv)}")
    t(f"  cos θ = {fmt_num(pu)} / ({fmt_num(nu)}·{fmt_num(nv)}) = {fmt_num(cos, 4)}  →  θ ≈ {fmt_num(theta, 2)}°")
    return {"punto": pu, "norma_u": nu, "norma_v": nv, "cos": cos, "theta": theta}


def cosenos_directores(v, traza=None):
    """HU-20: cos α = x/‖v‖, cos β = y/‖v‖, y comprobación cos²α + cos²β = 1."""
    t = traza or Traza(False)
    _requiere_real(v)
    n = v.norma()
    if n < TOLERANCIA:
        raise ErrorCryptoLineal("El vector nulo no tiene dirección: no hay cosenos directores.")
    ca, cb = v.x / n, v.y / n
    alfa, beta = math.degrees(math.acos(ca)), math.degrees(math.acos(cb))
    suma = ca * ca + cb * cb
    t(f"  v = {v}, ‖v‖ = {fmt_num(n)}")
    t(f"  cos α = {fmt_num(ca)} (α ≈ {fmt_num(alfa, 1)}°)   cos β = {fmt_num(cb)} (β ≈ {fmt_num(beta, 1)}°)")
    t(f"  cos²α + cos²β = {fmt_num(suma, 9)}  " + ("✓" if abs(suma - 1) < TOLERANCIA else "✗"))
    return {"cos_alfa": ca, "cos_beta": cb, "alfa": alfa, "beta": beta, "suma_cuadrados": suma}


def comparar_angulo_reduccion(K, p, traza=None):
    """
    HU-20 (T20-3 frente a T20-4): ángulo entre p y K·p antes y después de reducir.
    La reducción módulo 26 destruye la información métrica.
    """
    t = traza or Traza(False)
    K = como_clave(K)
    p = VectorZ26.de(p)
    sin_reducir, reducido = aplicar_matriz(K, p.par)
    t(f"p = {p}, K·p sin reducir = {fmt_par(sin_reducir)}, reducido = {fmt_par(reducido)}")
    t("Ángulo entre ι(p) y K·p SIN reducir (lectura del operador sobre ℝ²):")
    antes = angulo(p.elevar(), VectorR2(*sin_reducir), t)["theta"]
    t("Ángulo entre ι(p) e ι(K·p mod 26) (tras reducir):")
    despues = angulo(p.elevar(), VectorR2(*reducido), t)["theta"]
    difieren = abs(antes - despues) > 1e-6
    aviso = ""
    if difieren:
        aviso = (
            f"⚠ El ángulo pasa de {fmt_num(antes, 1)}° a {fmt_num(despues, 1)}° solo por reducir módulo 26. "
            "La reducción destruye la información métrica: no se puede afirmar que la clave "
            "«rota los vectores» un ángulo fijo."
        )
        t(aviso)
    return {"antes": antes, "despues": despues, "difieren": difieren, "aviso": aviso}


def lectura_area(K, traza=None):
    """
    HU-19: el determinante como área del paralelogramo de las columnas,
    vía u × v con u = (a, c, 0) y v = (b, d, 0).
    """
    t = traza or Traza(False)
    K = como_clave(K)
    (a, b), (c, d) = K
    u3, v3 = (a, c, 0), (b, d, 0)
    cruz = producto_vectorial(u3, v3)
    det_entero, det_mod = cl.determinante(K)
    g = math.gcd(det_mod, MODULO)
    area = abs(cruz[2])
    if cruz[2] != det_entero:
        raise ErrorInterno("Inconsistencia interna: la tercera componente de u × v no es det K.")

    t(f"K = {fmt_matriz(K)} → columnas u = ({a}, {c}), v = ({b}, {d}) (representantes en ℝ²)")
    t(f"  Embebidas en ℝ³: u = {u3}, v = {v3}")
    t(f"  u × v = (c·0 − 0·d, 0·b − a·0, a·d − c·b) = {cruz}")
    t(f"  Tercera componente = ad − bc = {det_entero} = det K sin reducir ✓")
    t(f"  Área del paralelogramo = |{det_entero}| = {area}   (capa ℝ²)")
    t(f"  det K mod 26 = {det_mod}, mcd({det_mod}, 26) = {g}   (capa ℤ₂₆)")

    if area == 0:
        k = None
        if (a, c) != (0, 0):
            for m in range(1, MODULO):
                if (m * a, m * c) == (b, d):
                    k = m
                    break
        lectura = (
            "Columnas colineales: el paralelogramo degenera en un segmento"
            + (f" (v = {k}·u)" if k else "")
            + ". Singular en ℝ² y en ℤ₂₆: la imagen se aplasta."
        )
    elif g == 1:
        lectura = "Área no nula y determinante unidad módulo 26: invertible en ambas capas."
    else:
        lectura = (
            f"Área {area} ≠ 0: sobre ℝ² la matriz sería invertible. Pero det K ≡ {det_mod} (mod 26) "
            f"comparte el factor {g} con 26. La geometría real es CIEGA a este fallo: "
            "la condición modular es estrictamente más fuerte que la geométrica."
        )
    t("  → " + lectura)

    # T19-5: verificación cruzada ‖u‖·‖v‖·sen θ = |det K|
    ur, vr = VectorR2(a, c), VectorR2(b, d)
    cruzada = None
    if ur.norma() > 0 and vr.norma() > 0:
        theta = angulo(ur, vr)["theta"]
        cruzada = ur.norma() * vr.norma() * math.sin(math.radians(theta))
        t(f"  Verificación: ‖u‖·‖v‖·sen θ = {fmt_num(ur.norma())}·{fmt_num(vr.norma())}·sen {fmt_num(theta, 2)}° "
          f"≈ {fmt_num(cruzada, 2)} = |det K|")
    return {
        "u3": u3, "v3": v3, "cruz": cruz, "det_entero": det_entero, "area": area,
        "det_mod": det_mod, "mcd": g,
        "invertible_R": area != 0, "invertible_Z26": g == 1,
        "ciega": area != 0 and g != 1,
        "verificacion_seno": cruzada, "lectura": lectura,
    }


def proyeccion_real(u, v, traza=None):
    """HU-21: proy_v(u) = (u·v / v·v)·v en ℝ² y comprobación de ortogonalidad del residuo."""
    t = traza or Traza(False)
    _requiere_real(u, v)
    vv = v.punto(v)
    if vv < TOLERANCIA:
        raise ErrorCryptoLineal("No se puede proyectar sobre el vector nulo.")
    uv = u.punto(v)
    escalar = uv / vv
    proy = escalar * v
    residuo = u - proy
    ortog = residuo.punto(v)
    t(f"  u·v = {fmt_num(uv)}, v·v = {fmt_num(vv)}, escalar = {fmt_num(uv)}/{fmt_num(vv)} ≈ {fmt_num(escalar)}")
    t(f"  proy_v(u) ≈ {proy}")
    t(f"  u − proy ≈ {residuo};  (u − proy)·v = {fmt_num(ortog, 9)}  "
      + ("✓ ortogonal" if abs(ortog) < 1e-9 else "✗"))
    return {"escalar": escalar, "proy": proy, "residuo": residuo, "residuo_punto_v": ortog}


def proyeccion_modular(u, v, traza=None):
    """
    HU-21: intenta la misma fórmula en ℤ₂₆². Exige que v·v sea unidad módulo 26.
    Devuelve un diagnóstico: definida, vv, mcd, factor, proy, motivo.
    """
    t = traza or Traza(False)
    u, v = VectorZ26.de(u), VectorZ26.de(v)
    vv = v.punto(v)
    vv_entero = v.x * v.x + v.y * v.y
    g = math.gcd(vv, MODULO)
    t(f"  v·v = {v.x}² + {v.y}² = {vv_entero} ≡ {vv} (mod 26), mcd({vv}, 26) = {g}")
    if g != 1:
        factor = {2: "2", 13: "13", 26: "26 (v·v ≡ 0)"}[g]
        motivo = (
            f"Proyección NO definida en ℤ₂₆²: v·v ≡ {vv} no tiene inverso módulo 26 "
            f"(factor común {factor})."
        )
        t("  → " + motivo)
        return {"definida": False, "vv": vv, "mcd": g, "factor": g, "proy": None, "motivo": motivo}
    inv = cl.inverso_modular(vv)
    uv = u.punto(v)
    escalar = (uv * inv) % MODULO
    proy = escalar * v
    motivo = (
        f"Definida: (v·v)⁻¹ = {inv}, escalar = (u·v)·(v·v)⁻¹ = {uv}·{inv} ≡ {escalar}, "
        f"proy = {escalar}·{v} = {proy}. Ojo: es otra operación, no la versión discreta de la proyección real."
    )
    t("  → " + motivo)
    return {"definida": True, "vv": vv, "mcd": 1, "factor": None, "proy": proy, "motivo": motivo}


# ════════════════════════════════════════════════════════════════════
#  Épica 8 · La frontera entre ℝ² y ℤ₂₆² (HU-22, HU-23, HU-24)
# ════════════════════════════════════════════════════════════════════

def todos_los_vectores():
    return [VectorZ26(x, y) for x in range(MODULO) for y in range(MODULO)]


def es_isotropo(v):
    return VectorZ26.de(v).punto(VectorZ26.de(v)) == 0


def vectores_isotropos(traza=None):
    """HU-22: barrido completo de ℤ₂₆² buscando v·v ≡ 0 (mod 26)."""
    t = traza or Traza(False)
    lista = [v for v in todos_los_vectores() if es_isotropo(v)]
    no_nulos = [v for v in lista if v.par != (0, 0)]
    t(f"Barrido de los {TOTAL_PUNTOS} vectores de ℤ₂₆²: {len(lista)} cumplen v·v ≡ 0, "
      f"{len(no_nulos)} de ellos NO nulos.")
    for ej in (VectorZ26(1, 5), VectorZ26(13, 13)):
        t(f"  Ej.: {ej}·{ej} = {ej.x}² + {ej.y}² = {ej.x ** 2 + ej.y ** 2} ≡ 0 (mod 26)")
    t("  Sobre ℝ², v·v = 0 implica v = 0: de ahí salen la norma y todo lo demás.")
    t(f"  En ℤ₂₆ esa implicación es falsa: (1, 5) tiene norma real √26 ≈ {fmt_num(math.sqrt(26), 2)}, "
      "pero es «ortogonal a sí mismo» módulo 26.")
    return {"todos": lista, "no_nulos": no_nulos}


def nucleo(K):
    K = como_clave(K)
    return [p for p in todos_los_vectores() if aplicar(K, p).par == (0, 0)]


def imagen(K):
    K = como_clave(K)
    return {aplicar(K, p) for p in todos_los_vectores()}


def _rango_mod_primo(K, q):
    (a, b), (c, d) = K
    if (a * d - b * c) % q:
        return 2
    return 0 if all(x % q == 0 for x in (a, b, c, d)) else 1


def tamano_nucleo_crt(K):
    """
    Regla correcta (por el teorema chino del resto, ℤ₂₆ ≅ ℤ₂ × ℤ₁₃):
    |núcleo| = 2^(2 − rango₂ K) · 13^(2 − rango₁₃ K).
    Sustituye a la conjetura |núcleo| = mcd(det K, 26), refutada por T23-5.
    """
    K = como_clave(K)
    return 2 ** (2 - _rango_mod_primo(K, 2)) * 13 ** (2 - _rango_mod_primo(K, 13))


def analizar_transformacion(K, traza=None):
    """HU-23: núcleo, imagen, 676 = |núcleo|·|imagen| y colisiones exhibidas."""
    t = traza or Traza(False)
    K = como_clave(K)
    ker = nucleo(K)
    img = imagen(K)
    det_mod = cl.determinante(K)[1]
    g = math.gcd(det_mod, MODULO)
    t(f"K = {fmt_matriz(K)} como transformación ℤ₂₆² → ℤ₂₆²")
    t(f"  |núcleo| = {len(ker)}   |imagen| = {len(img)}   "
      f"producto = {len(ker) * len(img)} " + ("= 676 ✓" if len(ker) * len(img) == TOTAL_PUNTOS else "≠ 676 ✗"))
    if len(ker) * len(img) != TOTAL_PUNTOS:
        raise ErrorInterno("Inconsistencia interna: |núcleo|·|imagen| ≠ 676.")

    colision = []
    if len(ker) == 1:
        t("  Núcleo trivial: la transformación es biyectiva, no hay colisiones.")
    else:
        colision = ker if len(ker) <= 4 else ker[:2]
        letras = ", ".join(f"'{p.letras}'" for p in colision)
        destino = aplicar(K, colision[0]).letras
        t(f"  Colisión: {letras} cifran todos a '{destino}'")
        for p in colision:
            t(f"    K·{p} = {aplicar(K, p)}")
        t("  Mensajes distintos, mismo criptograma: la información se pierde de forma verificable.")

    crt = tamano_nucleo_crt(K)
    t(f"  mcd(det K, 26) = {g}  " + ("= |núcleo|" if g == len(ker) else f"≠ |núcleo| = {len(ker)}  ← contraejemplo a la conjetura"))
    t(f"  Regla por el teorema chino del resto: 2^(2−rango₂)·13^(2−rango₁₃) = {crt}  "
      + ("✓" if crt == len(ker) else "✗"))
    return {
        "nucleo": ker, "imagen": img, "tam_nucleo": len(ker), "tam_imagen": len(img),
        "colision": colision, "mcd": g, "coincide_con_mcd": g == len(ker), "crt": crt,
    }


def submodulo_generado(v, traza=None):
    """HU-24: ⟨v⟩ = {k·v : k = 0,…,25} ⊂ ℤ₂₆², su cardinal y la regla general."""
    t = traza or Traza(False)
    v = VectorZ26.de(v)
    conjunto = {k * v for k in range(MODULO)}
    n = len(conjunto)
    regla = MODULO // math.gcd(MODULO, math.gcd(v.x, v.y))
    t(f"⟨{v}⟩ = {{k·{v} : k = 0,…,25}} tiene {n} elementos distintos")
    t(f"  ¿Divide a 26? {'sí' if MODULO % n == 0 else 'NO'}   "
      f"Regla 26 / mcd(26, mcd({v.x}, {v.y})) = {regla} " + ("✓" if regla == n else "✗"))
    if n <= 13:
        t("  Elementos: " + " ".join(str(w) for w in sorted(conjunto, key=lambda w: w.par)))
    t(f"  En ℝ², la recta generada por ι(v) = {v.elevar()} es infinita"
      + ("" if v.par != (0, 0) else " (salvo v = 0, que genera solo el origen)") + ".")
    if n in (2, 13):
        t("  Un cuerpo de q elementos solo admite subespacios de dimensión 1 con q elementos: "
          f"el cardinal {n} es huella de que ℤ₂₆ no es un cuerpo.")
    return {"elementos": conjunto, "cardinal": n, "divide_26": MODULO % n == 0, "regla": regla}



# ════════════════════════════════════════════════════════════════════
#  Casos de estudio (Tabla 3 del documento + contraejemplo de HU-23)
# ════════════════════════════════════════════════════════════════════

CASOS_SEMANA8 = dict(cl.CASOS_DE_ESTUDIO)
CASOS_SEMANA8["5"] = ("Caso 5 — contraejemplo [2 0; 0 2] (det 4, mcd 2, |núcleo| 4)", ((2, 0), (0, 2)))

