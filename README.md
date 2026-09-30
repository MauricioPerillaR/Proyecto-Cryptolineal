# CryptoLineal · Semana 8 — Estructura del código

Todos los archivos van en la misma carpeta que `cryptolineal.py` (prototipo v1, sin cambios).

| Archivo | Capa | Contenido | Depende de |
|---|---|---|---|
| `vectorial_modelo.py` | Lógica de negocio | `VectorZ26`, `VectorR2`, ι, HU-16 a HU-24, casos de estudio | `cryptolineal` |
| `vectorial_figuras.py` | Lógica de visualización | HU-25: retícula, paralelogramo, panel comparativo | `vectorial_modelo`, matplotlib (opcional) |
| `vectorial_tabla.py` | Datos de la tabla | HU-26: filas, evidencias, construcción y Markdown | — |
| `cryptolineal_vectorial.py` | Demostración | Menú interactivo y opciones de línea de comandos | los tres anteriores |
| `pruebas_vectorial.py` | Pruebas | T16–T26, pruebas del menú y regresión del v1 | todos |

Dirección de las dependencias: `modelo ← figuras`, `modelo ← menú`, `todo ← pruebas`.
La lógica no importa ni el menú ni las pruebas. El menú y las pruebas se importan
entre sí de forma diferida (dentro de funciones), así que no hay importación circular.

## Uso

```
python cryptolineal_vectorial.py              # menú de demostración
python cryptolineal_vectorial.py --figuras    # exporta las figuras de HU-25
python cryptolineal_vectorial.py --tabla      # tabla de HU-26 verificada, en Markdown
python pruebas_vectorial.py                   # pruebas v1 (78) + Semana 8 (55)
python pruebas_vectorial.py --solo-s8         # solo Semana 8
```

matplotlib solo se necesita para las figuras (`pip install matplotlib`). Sin él,
todo lo demás funciona y la prueba T25-4 se reporta como omitida.
