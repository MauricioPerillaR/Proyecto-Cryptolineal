"""
CryptoLineal · Semana 8 — Demostración interactiva (punto de entrada)

Menú para la sustentación. Solo lee datos, llama a la lógica de
vectorial_modelo / vectorial_figuras / vectorial_tabla y muestra resultados.

Uso:
  python cryptolineal_vectorial.py              menú interactivo
  python cryptolineal_vectorial.py --pruebas    delega en pruebas_vectorial.py
  python cryptolineal_vectorial.py --figuras    exporta las figuras de HU-25
  python cryptolineal_vectorial.py --tabla      tabla de HU-26 verificada, en Markdown
"""

import sys

import cryptolineal as cl
from cryptolineal import ErrorCryptoLineal, Traza, fmt_matriz
from vectorial_modelo import (
    CASOS_SEMANA8,
    ErrorCapas,
    VectorZ26,
    analizar_transformacion,
    angulo,
    ataque_texto_escogido,
    cifrar_como_combinacion,
    comparar_angulo_reduccion,
    cosenos_directores,
    imagenes_base,
    iota,
    lectura_area,
    proyeccion_modular,
    proyeccion_real,
    representar_digrama,
    submodulo_generado,
    vectores_isotropos,
)
from vectorial_figuras import figuras_casos
from vectorial_tabla import tabla_markdown


def _pruebas():
    """Importación diferida: las pruebas importan este módulo para probar el menú."""
    import pruebas_vectorial
    return pruebas_vectorial


def imprimir_tabla(tabla):
    anchos = (28, 19, 45)
    print(f"{'Operación':<{anchos[0]}} {'¿En ℤ₂₆?':<{anchos[1]}} {'Obstrucción':<{anchos[2]}} Evidencia")
    print("─" * 120)
    for f in tabla:
        marca = "✓" if f["verificado"] else "✗ SIN EVIDENCIA"
        print(f"{f['operacion']:<{anchos[0]}} {f['sobrevive']:<{anchos[1]}} {f['obstruccion']:<{anchos[2]}} "
              f"{', '.join(f['evidencia'])}  {marca}")


def leer_vector(s):
    """Acepta un digrama ('AL') o dos enteros ('0 11', '0,11')."""
    s = s.strip()
    if len(s) == 2 and s.isalpha():
        return VectorZ26.desde_letras(s.upper())
    partes = s.replace(",", " ").replace(";", " ").replace("(", " ").replace(")", " ").split()
    if len(partes) != 2 or not all(cl._ENTERO.fullmatch(p) for p in partes):
        raise ErrorCryptoLineal(
            f"«{s}» no es un vector. Escribe dos letras (p. ej. AL) o dos enteros (p. ej. 0 11)."
        )
    return VectorZ26(int(partes[0]), int(partes[1]))


def _clave(estado, leer):
    return cl.pedir_clave(estado, leer)


def op_representar(estado, leer):
    v = leer_vector(leer("Digrama o vector (p. ej. AL o 0 11): "))
    representar_digrama(v, Traza(True))
    k = leer("Escalar k para calcular k·v (Enter = omitir): ").strip()
    if k:
        if not cl._ENTERO.fullmatch(k):
            raise ErrorCapas(f"«{k}» no es un escalar de ℤ₂₆: solo se admiten enteros.")
        print(f"  {k}·{v} = {int(k) * v}  (mod 26)")
    w = leer("Otro vector para sumar (Enter = omitir): ").strip()
    if w:
        w = leer_vector(w)
        print(f"  {v} + {w} = {v + w}  (mod 26)")


def op_columnas(estado, leer):
    K = _clave(estado, leer)
    print()
    imagenes_base(K, Traza(True))
    print()
    ataque_texto_escogido(K, Traza(True))


def op_combinacion(estado, leer):
    mensaje = leer("Mensaje a cifrar: ")
    cl.normalizar(mensaje)
    K = _clave(estado, leer)
    c = cifrar_como_combinacion(mensaje, K, estado["traza"])
    print(f"\nCriptograma: {c}")


def op_area(estado, leer):
    K = _clave(estado, leer)
    print()
    lectura_area(K, Traza(True))


def op_angulo(estado, leer):
    u = leer_vector(leer("Vector u (se elevará a ℝ²): "))
    v = leer_vector(leer("Vector v (se elevará a ℝ²): "))
    ur, vr = iota(u), iota(v)
    print(f"\nι(u) = {ur}, ι(v) = {vr}  (capa real)")
    angulo(ur, vr, Traza(True))
    print("Cosenos directores de u:")
    cosenos_directores(ur, Traza(True))
    print("Cosenos directores de v:")
    cosenos_directores(vr, Traza(True))
    if estado["clave"] is not None:
        p = leer("Digrama p para comparar el ángulo antes/después de reducir con la clave precargada (Enter = omitir): ").strip()
        if p:
            print()
            comparar_angulo_reduccion(estado["clave"], leer_vector(p), Traza(True))


def op_proyeccion(estado, leer):
    u = leer_vector(leer("Vector u (el que se proyecta): "))
    v = leer_vector(leer("Vector v (sobre el que se proyecta): "))
    print(f"\nEn ℝ²: proyección de ι(u) = {iota(u)} sobre ι(v) = {iota(v)}")
    proyeccion_real(iota(u), iota(v), Traza(True))
    print(f"\nEn ℤ₂₆²: misma fórmula con u = {u}, v = {v}")
    proyeccion_modular(u, v, Traza(True))


def op_isotropos(estado, leer):
    r = vectores_isotropos(Traza(True))
    print("  No nulos: " + " ".join(str(v) for v in r["no_nulos"]))


def op_nucleo(estado, leer):
    K = _clave(estado, leer)
    print()
    analizar_transformacion(K, Traza(True))


def op_submodulo(estado, leer):
    v = leer_vector(leer("Vector generador v: "))
    print()
    submodulo_generado(v, Traza(True))


def op_figuras(estado, leer):
    d = leer("Carpeta de salida (Enter = figuras_semana8): ").strip() or "figuras_semana8"
    res = figuras_casos(d)
    for f in res["figuras"]:
        print(f"  {f['ruta']}\n     Pie: {f['pie']}")


def op_tabla(estado, leer):
    print("Ejecutando las pruebas de evidencia…\n")
    imprimir_tabla(_pruebas().tabla_verificada())


def op_caso(estado, leer):
    print("\nCasos de estudio:")
    for k, (nombre, M) in CASOS_SEMANA8.items():
        print(f"  {k}. {nombre}   K = {fmt_matriz(M)}")
    eleccion = leer("Elige un caso (1-5): ").strip()
    if eleccion not in CASOS_SEMANA8:
        raise ErrorCryptoLineal("Caso inexistente. Elige un número del 1 al 5.")
    nombre, M = CASOS_SEMANA8[eleccion]
    estado["clave"] = M
    print(f"\nClave precargada: {nombre}")
    print("Se usará por defecto al pedir la clave (Enter).")


def op_traza(estado, leer):
    estado["traza"].activa = not estado["traza"].activa
    print("Traza del cifrado como combinación lineal " + ("ACTIVADA." if estado["traza"].activa else "DESACTIVADA."))


def op_pruebas(estado, leer):
    _pruebas().ejecutar_pruebas()


def op_menu_v1(estado, leer):
    cl.ejecutar_menu(leer)


OPCIONES = [
    ("1", "Representar un digrama como vector (HU-16)", op_representar),
    ("2", "Columnas de K e imágenes de la base; ataque BAAB (HU-17)", op_columnas),
    ("3", "Cifrar como combinación lineal (HU-18)", op_combinacion),
    ("4", "Determinante como área: producto vectorial (HU-19)", op_area),
    ("5", "Ángulo y cosenos directores (HU-20)", op_angulo),
    ("6", "Proyección en ℝ² y su obstrucción en ℤ₂₆² (HU-21)", op_proyeccion),
    ("7", "Vectores isótropos (HU-22)", op_isotropos),
    ("8", "Núcleo, imagen y colisiones (HU-23)", op_nucleo),
    ("9", "Submódulo generado por un vector (HU-24)", op_submodulo),
    ("10", "Exportar figuras (HU-25)", op_figuras),
    ("11", "Tabla comparativa ℝ² vs ℤ₂₆² (HU-26)", op_tabla),
    ("12", "Cargar un caso de estudio", op_caso),
    ("13", "Activar / desactivar la traza", op_traza),
    ("14", "Ejecutar las pruebas automáticas", op_pruebas),
    ("15", "Ir al menú del prototipo v1", op_menu_v1),
]


def ejecutar_menu(leer=input):
    estado = {"traza": Traza(True), "clave": None}
    acciones = {k: f for k, _, f in OPCIONES}
    while True:
        clave = fmt_matriz(estado["clave"]) if estado["clave"] else "ninguna"
        print("\n══════ CryptoLineal · Semana 8 · Lectura vectorial y geométrica ══════")
        print(f"Traza: {'ACTIVADA' if estado['traza'].activa else 'desactivada'}   |   Clave precargada: {clave}")
        for k, texto, _ in OPCIONES:
            print(f"  {k:>2}. {texto}")
        print("   0. Salir")
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
        except Exception as e:  # INV-3: el programa no termina
            print(f"\n✗ Error inesperado ({type(e).__name__}): {e}")




if __name__ == "__main__":
    cl._configurar_consola()
    args = sys.argv[1:]
    try:
        if "--pruebas" in args:
            sys.exit(0 if _pruebas().ejecutar_pruebas() else 1)
        if "--figuras" in args:
            for f in figuras_casos()["figuras"]:
                print(f"{f['ruta']}\n  Pie: {f['pie']}")
            sys.exit(0)
        if "--tabla" in args:
            print(tabla_markdown(_pruebas().tabla_verificada()))
            sys.exit(0)
    except ErrorCryptoLineal as e:
        print(f"✗ {e}")
        sys.exit(1)
    ejecutar_menu()
