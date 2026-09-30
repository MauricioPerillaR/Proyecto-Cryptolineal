"""
CryptoLineal · Semana 8 — Visualización (HU-25)

Figuras para el informe: retícula 26×26 con la imagen de K resaltada y
paralelogramo de las columnas de K sobre ℝ². Aísla la dependencia de matplotlib:
si no está instalado, el resto del proyecto funciona igual.
"""

import os

from cryptolineal import MODULO, ErrorCryptoLineal, como_clave, fmt_matriz
from vectorial_modelo import CASOS_SEMANA8, TOTAL_PUNTOS, imagen, todos_los_vectores


def cargar_pyplot():
    """Devuelve pyplot (backend Agg) o lanza ErrorCryptoLineal con la instrucción de instalación."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ErrorCryptoLineal(
            "Las figuras de HU-25 necesitan matplotlib. Instálalo con: pip install matplotlib"
        ) from None
    return plt


def _limites_paralelogramo(claves):
    xs, ys = [0], [0]
    for K in claves:
        (a, b), (c, d) = como_clave(K)
        xs += [a, b, a + b]
        ys += [c, d, c + d]
    return (min(xs) - 1, max(xs) + 1), (min(ys) - 1, max(ys) + 1)


def _dibujar_reticula(ax, K):
    K = como_clave(K)
    img = imagen(K)
    todos = todos_los_vectores()
    ax.scatter([p.x for p in todos], [p.y for p in todos], s=4, color="#c9c4ba", label="ℤ₂₆²")
    ax.scatter([p.x for p in img], [p.y for p in img], s=9, color="#3a4b9e", label="imagen de K")
    ax.set_xlim(-1, 26)
    ax.set_ylim(-1, 26)
    ax.set_aspect("equal")
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.set_yticks([0, 5, 10, 15, 20, 25])
    ax.set_title(f"K = {fmt_matriz(K)}\nimagen: {len(img)} de {TOTAL_PUNTOS} puntos", fontsize=9)
    return len(img)


def _dibujar_paralelogramo(ax, K, xlim, ylim):
    K = como_clave(K)
    (a, b), (c, d) = K
    area = abs(a * d - b * c)
    ax.fill([0, a, a + b, b], [0, c, c + d, d], color="#e8ebf7", edgecolor="#3a4b9e", linewidth=1)
    ax.annotate("", xy=(a, c), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="#9a2e2e", lw=1.8))
    ax.annotate("", xy=(b, d), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color="#1f6b4a", lw=1.8))
    ax.text(a, c, f"  u=({a},{c})", color="#9a2e2e", fontsize=8)
    ax.text(b, d, f"  v=({b},{d})", color="#1f6b4a", fontsize=8)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.grid(True, linewidth=0.3)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.5)
    etiqueta = "degenerado" if area == 0 else "no degenerado"
    ax.set_title(f"Área |det K| = {area} ({etiqueta})\ndet mod 26 = {(a * d - b * c) % MODULO}", fontsize=9)
    return area


def figura_reticula(K, ruta):
    """HU-25: retícula 26×26 con la imagen de K resaltada. Devuelve el pie de figura."""
    plt = cargar_pyplot()
    fig, ax = plt.subplots(figsize=(4.2, 4.6))
    n = _dibujar_reticula(ax, K)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return {"ruta": ruta, "imagen": n,
            "pie": f"Imagen de la transformación K = {fmt_matriz(como_clave(K))} sobre ℤ₂₆²: "
                   f"{n} de {TOTAL_PUNTOS} puntos."}


def figura_paralelogramo(K, ruta, xlim=None, ylim=None):
    """HU-25: flechas u, v desde el origen y paralelogramo sombreado con su área."""
    plt = cargar_pyplot()
    if xlim is None or ylim is None:
        xlim, ylim = _limites_paralelogramo([K])
    fig, ax = plt.subplots(figsize=(4.2, 4.6))
    area = _dibujar_paralelogramo(ax, K, xlim, ylim)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    return {"ruta": ruta, "area": area, "xlim": xlim, "ylim": ylim,
            "pie": f"Paralelogramo generado por las columnas de K = {fmt_matriz(como_clave(K))} "
                   f"sobre ℝ²; área |det K| = {area}."}


def figuras_casos(directorio="figuras_semana8", claves=None):
    """
    HU-25 / T25-4: exporta retícula y paralelogramo de cada caso con la misma escala
    y los mismos ejes, más un panel comparativo único para el informe.
    """
    plt = cargar_pyplot()
    if claves is None:
        claves = [CASOS_SEMANA8[k][1] for k in ("1", "2", "3", "4")]
    os.makedirs(directorio, exist_ok=True)
    xlim, ylim = _limites_paralelogramo(claves)
    salidas = []
    for i, K in enumerate(claves, 1):
        r = figura_reticula(K, os.path.join(directorio, f"hu25_reticula_caso{i}.png"))
        p = figura_paralelogramo(K, os.path.join(directorio, f"hu25_paralelogramo_caso{i}.png"), xlim, ylim)
        salidas += [r, p]

    fig, ejes = plt.subplots(2, len(claves), figsize=(4 * len(claves), 8.4))
    for j, K in enumerate(claves):
        _dibujar_reticula(ejes[0][j], K)
        _dibujar_paralelogramo(ejes[1][j], K, xlim, ylim)
    fig.suptitle("Fila 1: imagen sobre ℤ₂₆² · Fila 2: paralelogramo de las columnas sobre ℝ²", fontsize=11)
    fig.tight_layout()
    ruta_panel = os.path.join(directorio, "hu25_comparativo.png")
    fig.savefig(ruta_panel, dpi=200)
    plt.close(fig)
    salidas.append({"ruta": ruta_panel,
                    "pie": "Comparación de los casos de estudio: la imagen modular (arriba) y el área real "
                           "(abajo) no cuentan la misma historia en los casos 3 y 4."})
    return {"figuras": salidas, "xlim": xlim, "ylim": ylim}

