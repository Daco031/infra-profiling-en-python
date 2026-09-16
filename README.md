# Profiling en Python

Infraestructuras Paralelas y Distribuidas
Escuela de Ingeniería de Sistemas y Computación, Universidad del Valle
Carlos Andrés Delgado Saavedra

Medir antes de optimizar, y después de medir, decidir. El ejercicio toma una
función lenta a propósito, la mira con cuatro herramientas para ver qué dice
cada una y qué cuesta usarla, arregla lo que el perfil señala, y termina donde
el ciclo de Python ya no alcanza: en NumPy y en las instrucciones vectoriales
del procesador.

| Parte | Archivos | Qué se hace |
|---|---|---|
| 1 | `scripts/*_profile.py` | Medir la misma función con `time`, `timeit`, `cProfile` y `pyinstrument` |
| 2 | `src/suma_primos.py` | Leer el perfil y escribir la versión que ataca lo que mostró |
| 3 | `src/vectores.py` | El producto punto en tres formas: indexado, ciclo y NumPy |
| 4 | `avx/producto_punto.cpp` | El mismo producto punto con instrucciones AVX, a mano |

## Ambiente y dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Los scripts se ejecutan como módulos desde la raíz del repositorio, para que
encuentren `src`:

```bash
python -m scripts.time_profile
```

### El `.gitignore`

Genere el archivo en [gitignore.io](https://www.toptal.com/developers/gitignore)
con Linux, Python y el editor que use. Un repositorio con el entorno virtual y
los archivos de caché adentro es difícil de revisar, y el flujo de Actions
comprueba que el archivo exista y excluya el entorno y `__pycache__`.

## Parte 1: cuatro herramientas, cuatro números

En `src/suma_primos.py` está la suma de los primos menores que `n`, con una
prueba de primalidad que recorre hasta la raíz:

```python
def suma_primos(n):
    return sum(i for i in range(2, n) if es_primo(i))
```

Dentro de `scripts/`, cuatro programas que midan `suma_primos(10000)` e
impriman el tiempo en milisegundos, cada uno con su herramienta:

| Archivo | Herramienta |
|---|---|
| `time_profile.py` | módulo `time`, con `perf_counter` |
| `ctime_profile.py` | `timeit`, promediando veinte ejecuciones |
| `cprofile_profile.py` | `cProfile` |
| `pyinstrument_profile.py` | `pyinstrument` |

Cada uno imprime una sola línea con el tiempo, en la forma `12.345 ms`. El de
pyinstrument, además, guarda el informe con
`output_html()` en `pyinstrument_results.html`.

Las cuatro herramientas miden lo mismo y no dan lo mismo. `time` entrega una
sola muestra, `timeit` promedia, `cProfile` cuenta cada llamada y por eso pesa
sobre la ejecución, y pyinstrument muestrea. La diferencia entre los cuatro
números va explicada en `ANALISIS.md`.

## Parte 2: leer el perfil y decidir

`cProfile` sobre `suma_primos(10000)` dice qué función concentra el tiempo y
cuántas veces se llama. Con eso a la vista, escribir `suma_primos_rapida` en
`src/suma_primos.py`: devuelve exactamente lo mismo para todo `n`, y ataca lo
que el perfil mostró. La línea del perfil que justificó el cambio se copia en
`ANALISIS.md`.

```bash
python -m pytest tests/test_suma_primos.py -v
python -m scripts.comparar
```

`comparar.py` mide las dos versiones con `n = 200000` usando `timeit` e
imprime el factor. Tiene que llegar por lo menos a diez.

## Parte 3: el producto punto tres veces

`src/vectores.py` calcula el producto punto de dos vectores de un millón de
enteros. `producto_punto_indexado` ya está escrito y es la forma más lenta:
recorre dos arreglos de NumPy por índice desde un ciclo de Python, y cada
`a[i]` saca un escalar del arreglo y lo convierte en un objeto. Faltan las
otras dos:

- `producto_punto_bucle`, sobre listas de Python, con un ciclo y `zip`.
- `producto_punto_numpy`, sobre arreglos de NumPy, sin ningún ciclo de Python.

```bash
python -m pytest tests/test_vectores.py -v
python -m scripts.vectorizar
```

Las tres tienen que dar el mismo entero. La tabla con los tres tiempos y la
explicación de por qué NumPy gana por dos órdenes de magnitud van en
`ANALISIS.md`.

## Parte 4: AVX a mano

Lo que NumPy hace por debajo, escrito al nivel de las instrucciones del
procesador. `avx/producto_punto.cpp` trae `escalar`, un ciclo que multiplica y
suma un elemento a la vez. Falta `con_avx`: de a ocho floats por vuelta, con
`_mm256_loadu_ps` para cargar, `_mm256_mul_ps` para multiplicar,
`_mm256_add_ps` para acumular, y al final la reducción horizontal que deja las
ocho posiciones del acumulador en un solo número. Los elementos que sobran
cuando `n` no es múltiplo de ocho se suman aparte.

```bash
make -C avx producto_punto
```

El `Makefile` compila con `-mavx` para habilitar los intrínsecos, y con
`-fno-tree-vectorize` para que el compilador no vectorice por su cuenta el
ciclo escalar. Sin esa bandera, con `-O3`, el compilador suele hacer solo lo
que aquí se escribe a mano.

Los valores son enteros pequeños y el vector tiene `2^20` posiciones, así que
todas las sumas parciales son exactas en `float` y las dos versiones tienen
que imprimir el mismo resultado. En un procesador ARM, como los Mac con Apple
Silicon, esta parte solo corre en el servidor de Actions.

## Qué revisa el flujo de Actions

- Que el `.gitignore` exista y excluya el entorno virtual y `__pycache__`.
- Parte 1: que los cuatro scripts impriman un tiempo en milisegundos y que
  el de pyinstrument deje el informe HTML.
- Parte 2: que `suma_primos_rapida` pase las pruebas y sea al menos diez
  veces más rápida con `n = 200000`.
- Parte 3: que las tres formas del producto punto coincidan y que NumPy sea
  al menos veinte veces más rápido que el ciclo sobre listas.
- Parte 4: que las dos versiones den el mismo producto punto y que AVX sea
  al menos tres veces más rápida que el ciclo escalar.
- Que `ANALISIS.md` tenga las tablas y las explicaciones.

Los tiempos del registro son los de un servidor compartido; los que van en el
análisis son los de su máquina.

## Lo que hay que poder explicar

- Por qué los cuatro números de la parte 1 no coinciden, cuál se acerca más
  al tiempo real y cuál lo deforma más.
- Qué mostró el perfil, qué se cambió y por qué ese cambio ataca lo que el
  perfil mostró, con el factor obtenido.
- Por qué indexar un arreglo de NumPy desde un ciclo de Python es más lento
  que recorrer una lista, y qué hace NumPy por debajo que el ciclo no puede
  hacer.
- Cuánto ganó AVX frente al ciclo escalar y por qué no llega a ocho, aunque
  cada instrucción opere ocho floats.
