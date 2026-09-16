# Análisis

Nombre y código:

## Parte 1: cuatro herramientas, cuatro números

| Herramienta | Tiempo de `suma_primos(10000)` |
|---|---:|
| `time` |  |
| `timeit` (promedio de 20) |  |
| `cProfile` |  |
| `pyinstrument` |  |

¿Por qué no dan lo mismo? ¿Cuál se acerca más al tiempo real y cuál lo
deforma más, y por qué?

## Parte 2: lo que mostró el perfil

Función que concentra el tiempo, cuántas veces se llama y cuánto suma
(copiar la línea de `cProfile`):

Qué se cambió en `suma_primos_rapida` y por qué eso ataca lo que el perfil
mostró:

| Versión | Tiempo con `n = 200000` |
|---|---:|
| `suma_primos` |  |
| `suma_primos_rapida` |  |

Factor:

## Parte 3: el producto punto tres veces

| Forma | Tiempo |
|---|---:|
| Indexando el arreglo de NumPy |  |
| Ciclo sobre listas |  |
| NumPy vectorizado |  |

¿Por qué indexar el arreglo de NumPy desde Python es la forma más lenta de
las tres? ¿Qué hace NumPy por debajo que el ciclo de Python no puede hacer?

## Parte 4: AVX a mano

| Versión | Tiempo | Resultado |
|---|---:|---:|
| Escalar |  |  |
| AVX |  |  |

Factor obtenido, y por qué no llega a ocho aunque cada instrucción opere
ocho floats:
