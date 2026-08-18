# Profiling en Python

Infraestructuras Paralelas y Distribuidas
Escuela de Ingeniería de Sistemas y Computación, Universidad del Valle
Carlos Andrés Delgado Saavedra

Medir antes de optimizar. Este ejercicio toma una función lenta a propósito y
la mira con cuatro herramientas distintas, para ver qué dice cada una y qué
cuesta usarla.

## El código de partida

En `src/suma_primos.py` está la suma de los primos menores que `n`, con una
prueba de primalidad que recorre hasta la raíz:

```python
def suma_primos(n):
    return sum(i for i in range(2, n) if es_primo(i))
```

## Qué hay que hacer

Dentro de `scripts/`, cuatro programas que midan `suma_primos(10000)` e
impriman el tiempo en milisegundos, cada uno con su herramienta:

| Archivo | Herramienta |
|---|---|
| `time_profile.py` | módulo `time` |
| `ctime_profile.py` | `timeit`, promediando veinte ejecuciones |
| `cprofile_profile.py` | `cProfile` |
| `pyinstrument_profile.py` | `pyinstrument` |

Cada uno imprime solo el tiempo. El de pyinstrument, además, guarda el informe
con `output_html('pyinstrument_results.html')`.

## Ambiente y dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pruebas

```bash
python -m pytest tests/
```

## El .gitignore

Genere el archivo en [gitignore.io](https://www.toptal.com/developers/gitignore)
incluyendo Linux, Python y el editor que use. No incluirlo descuenta el 20 %
de la actividad: un repositorio con el entorno virtual y los archivos de caché
adentro es difícil de revisar.

## Qué mirar en los resultados

Las cuatro herramientas miden lo mismo y no dan lo mismo. `time` entrega una
sola muestra, `timeit` promedia, `cProfile` cuenta cada llamada y por eso pesa
sobre la ejecución, y pyinstrument muestrea con una sobrecarga mucho menor.
La diferencia entre los cuatro números es parte de lo que hay que explicar.
