"""
CryptoLineal · Semana 8 — Tabla comparativa ℝ² frente a ℤ₂₆² (HU-26)

Contiene los datos de la tabla y su presentación. La verificación la aporta
quien llama: tabla_comparativa() recibe {id de prueba: resultado} y marca cada
fila como verificada solo si TODAS sus pruebas de evidencia pasaron.
La ejecución de esas pruebas vive en pruebas_vectorial.tabla_verificada().
"""


FILAS_TABLA = [
    ("Suma y múltiplo escalar", "Sí", "—", ["T16-2", "T16-3"]),
    ("Combinación lineal", "Sí", "—", ["T18-1", "T18-2", "T18-3", "T18-4"]),
    ("Imagen de la base canónica", "Sí", "—", ["T17-1", "T17-4"]),
    ("Determinante y área", "Parcial", "El área no nula no garantiza invertibilidad", ["T19-3", "T19-4"]),
    ("Producto escalar", "Solo formal", "Existen vectores isótropos no nulos", ["T22-1", "T22-3"]),
    ("Norma", "No", "ℤ₂₆ no está ordenado; no hay raíz cuadrada", ["T22-5"]),
    ("Ángulo y cosenos directores", "No", "Requiere dividir entre normas", ["T20-3", "T20-4"]),
    ("Proyección ortogonal", "Casi nunca", "v·v rara vez es unidad", ["T21-3", "T21-4"]),
    ("Subespacio generado", "Sí, como submódulo", "Cardinales que un cuerpo no admite", ["T24-3", "T24-4"]),
    ("Inyectividad", "Condicionada", "mcd(det K, 26) = 1", ["T23-2", "T23-3", "T23-4", "T23-5"]),
]


def ids_de_evidencia():
    """Todos los identificadores de prueba que la tabla cita como evidencia."""
    return sorted({ev for fila in FILAS_TABLA for ev in fila[3]})


def tabla_comparativa(resultados):
    """
    HU-26: cada fila se marca verificada solo si TODOS sus casos de prueba
    valen True en `resultados`. Ninguna fila afirma sin evidencia.
    """
    tabla = []
    for operacion, sobrevive, obstruccion, evidencia in FILAS_TABLA:
        verificado = all(resultados.get(ev) is True for ev in evidencia)
        tabla.append({"operacion": operacion, "sobrevive": sobrevive, "obstruccion": obstruccion,
                      "evidencia": evidencia, "verificado": verificado})
    return tabla


def tabla_markdown(tabla):
    lineas = ["| Operación | ¿En ℤ₂₆? | Obstrucción | Evidencia | Verificado |",
              "|---|---|---|---|---|"]
    for f in tabla:
        lineas.append(f"| {f['operacion']} | {f['sobrevive']} | {f['obstruccion']} | "
                      f"{', '.join(f['evidencia'])} | {'✓' if f['verificado'] else '✗ SIN EVIDENCIA'} |")
    return "\n".join(lineas)
