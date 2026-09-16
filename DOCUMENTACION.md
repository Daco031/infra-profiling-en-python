# Documentación de apoyo: profiling en Python e instrucciones AVX

Aquí está lo que hace falta saber para escribir cada parte del ejercicio: las
funciones, clases y comandos con su firma, un ejemplo completo que resuelve un
problema parecido al que pide el README, los detalles que suelen fallar y los
enlaces a la documentación oficial. Las secciones siguen las del README, en el
mismo orden y con el mismo nombre. Los ejemplos se copian y corren tal cual; la
salida que acompaña a cada uno es la que dio una máquina con un Ryzen 5 3600,
Python 3.14 y GCC 16, y en otra máquina los tiempos cambian aunque las
proporciones se parezcan. Los enlaces van al final de cada sección.

## Ambiente y dependencias

### Lo que se usa

- `python3 -m venv .venv` crea un entorno virtual en la carpeta `.venv`: un
  intérprete con su propio `pip`, aislado de los paquetes del sistema.
  `source .venv/bin/activate` pone `.venv/bin` al frente del `PATH`, y desde
  ahí `python` y `pip` son los del entorno; `deactivate` lo deshace.
- `pip install -r requirements.txt` instala los paquetes listados en el
  archivo, uno por línea. `pip list` muestra lo que quedó instalado.
- `python -m paquete.modulo` ejecuta un módulo como programa con el directorio
  actual al frente de `sys.path`; por eso, desde la raíz del repositorio,
  `from src.suma_primos import suma_primos` funciona. `python scripts/archivo.py`
  pone `scripts/` al frente y `src` deja de encontrarse. Los `__init__.py` de
  `src/`, `scripts/` y `tests/` son los que convierten cada carpeta en paquete.
- `.gitignore` lleva un patrón por línea: `.venv/` excluye ese directorio con
  todo lo que contiene, `__pycache__/` excluye las carpetas de caché en
  cualquier nivel del árbol y `*.pyc` los archivos por extensión.
  `git check-ignore -v ruta` dice qué línea del archivo tapa una ruta, y
  `git status --ignored` lista lo excluido con el prefijo `!!`.
- `git rm -r --cached .venv` saca del índice lo que ya se había agregado por
  error, sin borrarlo del disco; desde ese momento el `.gitignore` sí lo tapa.

### Ejemplo

Un repositorio de prueba con un paquete, un entorno virtual y un `.gitignore`
de tres líneas, para ver qué tapa cada una.

```bash
mkdir ejemplo-gitignore && cd ejemplo-gitignore && git init -q
mkdir paquete && echo 'print("hola")' > paquete/hola.py
python3 -m venv .venv
.venv/bin/python -c "import paquete.hola"      # corre y deja paquete/__pycache__/
git status --short
printf '.venv/\n__pycache__/\n*.pyc\n' > .gitignore
git status --short --ignored
git check-ignore -v .venv/bin/python paquete/__pycache__/hola.cpython-314.pyc
```

Salida:

```
hola
?? paquete/
?? .gitignore
?? paquete/
!! .venv/
!! paquete/__pycache__/
.gitignore:1:.venv/	.venv/bin/python
.gitignore:2:__pycache__/	paquete/__pycache__/hola.cpython-314.pyc
```

El primer `git status` no muestra `.venv/` porque desde Python 3.13 el propio
`venv` deja adentro un `.gitignore` con `*`. Con el Python 3.11 del servidor
de Actions esa línea sale como `?? .venv/`, y el flujo revisa el `.gitignore`
de la raíz, no el que hay dentro del entorno: la línea `.venv/` tiene que
estar en el suyo. El generador que nombra el README produce un archivo mucho
más largo con las mismas tres entradas adentro; sirve igual, siempre que al
final aparezcan `venv` y `__pycache__`.

### Lo que suele fallar

- `ModuleNotFoundError: No module named 'src'` al correr
  `python scripts/time_profile.py`. El intérprete puso `scripts/` al frente
  de `sys.path` y `src` no está ahí. Se corre desde la raíz con
  `python -m scripts.time_profile`.
- El `.gitignore` está, pero `.venv/` sigue apareciendo en `git status` como
  modificado. Ya estaba en el índice antes de escribir el archivo; se saca con
  `git rm -r --cached .venv` y se hace commit.
- El flujo marca `.gitignore no excluye el entorno virtual` aunque el archivo
  exista. La verificación busca la palabra `venv` en el archivo; un entorno
  creado con otro nombre, como `env/`, está excluido pero la palabra no está.
  Se agrega la línea `.venv/` de todos modos.
- `pip: command not found` o los paquetes se instalan en el Python del
  sistema. El entorno no está activado en esa terminal; cada terminal nueva
  necesita su `source .venv/bin/activate`, y `which python` dice cuál está
  en uso.
- Un `pyinstrument_results.html` y las carpetas `__pycache__` aparecen en el
  commit. El informe se regenera en cada corrida; una línea `*.html` o el
  nombre del archivo en el `.gitignore` lo deja fuera.

### Enlaces

- [venv: creación de entornos virtuales](https://docs.python.org/3/library/venv.html):
  cómo se crea, se activa y se desactiva un entorno, y qué hay dentro de la carpeta.
- [Línea de comandos de Python, opción -m](https://docs.python.org/3/using/cmdline.html):
  qué hace `python -m` con `sys.path` y por qué encuentra los paquetes de la raíz.
- [Tutorial de Python, módulos y paquetes](https://docs.python.org/3/tutorial/modules.html):
  el papel de `__init__.py` y las importaciones dentro de un paquete.
- [Formato del archivo de requisitos de pip](https://pip.pypa.io/en/stable/reference/requirements-file-format/):
  qué admite cada línea de `requirements.txt`.
- [gitignore en la documentación de Git](https://git-scm.com/docs/gitignore):
  la sintaxis de los patrones, la barra final, la negación con `!` y el orden de precedencia.
- [Plantillas de gitignore de GitHub](https://github.com/github/gitignore):
  la colección de la que salen las plantillas de Python y de los editores.

## Parte 1: cuatro herramientas, cuatro números

### Lo que se usa

- `time.perf_counter() -> float` devuelve segundos de un reloj monótono de
  alta resolución. Solo la diferencia entre dos lecturas tiene sentido; se
  multiplica por 1.000 para milisegundos. `time.perf_counter_ns()` da lo mismo
  en nanosegundos enteros; `time.process_time()` cuenta solo tiempo de CPU del
  proceso; `time.time()` es la hora del sistema y puede saltar.
- `timeit.timeit(stmt='pass', setup='pass', timer=time.perf_counter, number=1000000, globals=None) -> float`
  ejecuta `stmt` `number` veces y devuelve el total en segundos. `stmt` puede
  ser una cadena o un objeto invocable; con una cadena, `globals=globals()`
  le da acceso a las variables del programa. El promedio es dividir por
  `number`.
- `timeit.repeat(stmt, setup, timer, repeat=5, number=1000000, globals=None) -> list[float]`
  hace `repeat` series de `number` ejecuciones y devuelve la lista de
  totales. El mínimo es la serie con menos interferencia.
- `timeit.Timer(stmt, setup, timer, globals)` es la clase detrás de las dos
  anteriores, con los métodos `.timeit(number)`, `.repeat(repeat, number)` y
  `.autorange()`, que busca cuántas ejecuciones caben en 0,2 s y devuelve la
  pareja `(number, segundos)`.
- `python -m timeit -s 'preparación' 'sentencia'` es la misma medición desde
  la terminal; `-n` fija `number` y `-r` fija `repeat`.
- `cProfile.Profile()` crea un perfilador que cuenta cada llamada a función.
  `.enable()` y `.disable()` delimitan lo que se mide; `.runcall(funcion, *args)`
  mide solo esa llamada; desde Python 3.8 también sirve como contexto con
  `with cProfile.Profile() as perfil:`. `cProfile.run('sentencia', filename=None, sort=-1)`
  hace todo en una línea e imprime la tabla.
- `pstats.Stats(perfil_o_archivo)` recibe un `Profile` o el archivo que dejó
  `.dump_stats()`. Su atributo `.total_tt` es el tiempo total que registró,
  en segundos. `.sort_stats('tottime')` y `.print_stats(n)` ordenan e imprimen
  la tabla, que se lee en la parte 2.
- `pyinstrument.Profiler(interval=0.001)` guarda la pila de llamadas cada
  `interval` segundos. `.start()` y `.stop() -> Session` delimitan la
  medición; la sesión trae `.duration` en segundos. `.output_text(unicode=False, color=False, show_all=False) -> str`
  devuelve el árbol en texto, `.output_html() -> str` devuelve la página
  completa como cadena y `.write_html(ruta)` la escribe directo en un archivo.
  `.print()` imprime el árbol en pantalla.
- `pyinstrument archivo.py` corre un programa bajo el perfilador y muestra el
  árbol al terminar. `-r html -o informe.html` deja el informe en un archivo,
  `-m modulo` corre un módulo como `python -m`, `--show-all` deja de ocultar
  las funciones de la biblioteca estándar.

### Ejemplo

Una función lenta a propósito: cuenta los números perfectos menores que `n`
sumando los divisores de cada uno de a uno. En `lento.py`:

```python
"""Una función lenta a propósito: cuenta los números perfectos menores que n
(los que son iguales a la suma de sus divisores propios, como 6 = 1 + 2 + 3)
probando cada divisor uno por uno."""


def suma_divisores(k):
    total = 0
    for d in range(1, k):
        if k % d == 0:
            total += d
    return total


def cuenta_perfectos(n):
    return sum(1 for k in range(2, n) if suma_divisores(k) == k)


if __name__ == "__main__":
    print(cuenta_perfectos(1000))
```

En `cuatro.py`, la misma medición con las cuatro herramientas sobre dos
cargas: `cuenta_perfectos(1000)` hace mil llamadas con mucho trabajo cada
una, y `muchas_llamadas(200000)` hace doscientas mil llamadas que casi no
trabajan.

```python
"""Dos cargas medidas con las cuatro herramientas: cuenta_perfectos(1000)
hace mil llamadas con mucho trabajo cada una; muchas_llamadas(200000) hace
doscientas mil llamadas que casi no trabajan."""
import cProfile
import pstats
import time
import timeit

from pyinstrument import Profiler

from lento import cuenta_perfectos


def cuadrado(i):
    return i * i


def muchas_llamadas(n):
    return sum(cuadrado(i) for i in range(n))


def cuatro(nombre, trabajo, veces=20):
    print(nombre)
    # 1. time: una sola muestra del reloj de alta resolución.
    inicio = time.perf_counter()
    trabajo()
    print(f"  time         {(time.perf_counter() - inicio) * 1000:8.3f} ms")

    # 2. timeit: corre number veces y devuelve el total; se divide para el promedio.
    total = timeit.timeit(trabajo, number=veces)
    print(f"  timeit       {total / veces * 1000:8.3f} ms  (promedio de {veces})")

    # 3. cProfile: cuenta cada llamada; total_tt es el tiempo total que registró.
    perfil = cProfile.Profile()
    perfil.enable()
    trabajo()
    perfil.disable()
    print(f"  cProfile     {pstats.Stats(perfil).total_tt * 1000:8.3f} ms")

    # 4. pyinstrument: guarda la pila cada milisegundo; stop() devuelve la sesión.
    perfilador = Profiler()
    perfilador.start()
    trabajo()
    sesion = perfilador.stop()
    print(f"  pyinstrument {sesion.duration * 1000:8.3f} ms")
    with open(f"informe_{nombre}.html", "w") as archivo:
        archivo.write(perfilador.output_html())


cuatro("perfectos", lambda: cuenta_perfectos(1000))
cuatro("llamadas", lambda: muchas_llamadas(200000))
```

```bash
python cuatro.py
```

```
perfectos
  time           15.025 ms
  timeit         15.302 ms  (promedio de 20)
  cProfile       16.872 ms
  pyinstrument   15.887 ms
llamadas
  time           20.332 ms
  timeit         21.311 ms  (promedio de 20)
  cProfile       93.880 ms
  pyinstrument   96.089 ms
```

Con mil llamadas largas los cuatro números quedan a menos de dos
milisegundos entre sí; con doscientas mil llamadas cortas, los dos
perfiladores cuadruplican el tiempo. El costo de ambos está en cada llamada y
cada retorno: `cProfile` registra el evento, y pyinstrument, aunque solo
guarda la pila una vez por milisegundo, consulta el reloj en cada uno para
saber si ya pasó el intervalo. Cuanto más corta la función y más veces se
llame, más se separan los perfiladores de `time` y `timeit`.

Las mismas tres herramientas de perfilado tienen versión de terminal, sin
tocar el programa:

```bash
python -m cProfile -s tottime lento.py
pyinstrument lento.py
pyinstrument -r html -o informe.html lento.py
python -m timeit -s 'from lento import cuenta_perfectos' 'cuenta_perfectos(300)'
```

```
3
         1008 function calls in 0.016 seconds

   Ordered by: internal time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      998    0.016    0.000    0.016    0.000 lento.py:6(suma_divisores)
        4    0.000    0.000    0.016    0.004 lento.py:15(<genexpr>)
```

```
3

  _     ._   __/__   _ _  _  _ _/_   Recorded: 14:31:42  Samples:  17
 /_//_/// /_\ / //_// / //_'/ //     Duration: 0.017     CPU time: 0.017
/   _/                      v5.1.3

Program: lento.py

0.016 <module>  lento.py:1
└─ 0.016 cuenta_perfectos  lento.py:14
   └─ 0.016 <genexpr>  lento.py:15
      ├─ 0.015 suma_divisores  lento.py:6
      └─ 0.001 [self]  lento.py
```

```
200 loops, best of 5: 1.09 msec per loop
```

Y las tres formas de `timeit` desde un programa, en `formas_timeit.py`:

```python
"""Las formas de timeit sobre la misma llamada."""
import timeit

from lento import cuenta_perfectos

# timeit.timeit: total de number ejecuciones; el promedio es dividir.
total = timeit.timeit(lambda: cuenta_perfectos(300), number=50)
print(f"timeit  promedio {total / 50 * 1000:.3f} ms")

# timeit.repeat: repeat series de number ejecuciones; se reporta el mínimo,
# que es la corrida con menos interferencia.
series = timeit.repeat(lambda: cuenta_perfectos(300), repeat=5, number=50)
print(f"repeat  mínimo   {min(series) / 50 * 1000:.3f} ms  "
      f"máximo {max(series) / 50 * 1000:.3f} ms")

# Timer con la sentencia como texto y globals: igual que la CLI.
reloj = timeit.Timer("cuenta_perfectos(300)", globals=globals())
veces, segundos = reloj.autorange()   # cuántas caben en 0,2 s
print(f"Timer   autorange corrió {veces} veces en {segundos:.3f} s")
```

```bash
python formas_timeit.py
```

```
timeit  promedio 1.105 ms
repeat  mínimo   1.082 ms  máximo 1.120 ms
Timer   autorange corrió 200 veces en 0.218 s
```

### Lo que suele fallar

- El número de `timeit` sale veinte veces más grande que el de `time`.
  `timeit.timeit` devuelve el total de las `number` ejecuciones, en segundos:
  con `number=20` y sin dividir, `cuenta_perfectos(1000)` reporta 302 ms
  en vez de 15. Se divide por `number` y se multiplica por 1.000.
- El flujo marca `debe imprimir solo el tiempo en milisegundos, como '12.345 ms'`.
  Toma la última línea que escribió el programa y la compara con
  `^[0-9]+([.,][0-9]+)? ms$`: una etiqueta antes del número, dos cifras en la
  misma línea o un `perfil.print_stats()` que dejó la tabla en pantalla la
  rompen. Los scripts imprimen una sola línea y nada más.
- `pyinstrument_results.html` no aparece o queda vacío. `output_html()`
  devuelve una cadena y no toca el disco; hay que abrir el archivo y
  escribirla, o usar `write_html("pyinstrument_results.html")`. El nombre y
  la carpeta cuentan: el flujo lo busca en la raíz del repositorio, que es
  desde donde corre `python -m`.
- `cProfile` mide más de lo que se pidió. Sin `disable()` antes del `print`,
  o con `cProfile.run()` sobre una cadena que también importa cosas, el
  tiempo incluye trabajo ajeno. `runcall(funcion, argumento)` delimita solo
  esa llamada.
- Medido con `time.time()`, el intervalo sale en 0,0 en Windows o cambia de
  una corrida a otra sin razón. Es la hora del sistema, con la resolución que
  el sistema le dé, y el servicio de hora puede moverla hacia atrás. Para
  medir intervalos va `perf_counter`.

### Enlaces

- [time: perf_counter y los demás relojes](https://docs.python.org/3/library/time.html):
  qué mide cada reloj y cuál conviene para intervalos.
- [timeit: medir tiempos de fragmentos pequeños](https://docs.python.org/3/library/timeit.html):
  `timeit`, `repeat`, la clase `Timer`, `autorange` y la interfaz de terminal.
- [Los perfiladores de Python: cProfile y pstats](https://docs.python.org/3/library/profile.html):
  la clase `Profile`, `run`, la tabla de `pstats` y las claves de ordenamiento.
- [Guía de usuario de pyinstrument](https://pyinstrument.readthedocs.io/en/latest/guide.html):
  la clase `Profiler`, `output_text`, `output_html` y las opciones de la terminal.
- [Referencia de la API de pyinstrument](https://pyinstrument.readthedocs.io/en/latest/reference.html):
  las firmas completas de `Profiler` y `Session`.
- [Cómo funciona pyinstrument](https://pyinstrument.readthedocs.io/en/latest/how-it-works.html):
  por qué guarda la pila por intervalos y qué le cuesta al programa medido.

## Parte 2: leer el perfil y decidir

### Lo que se usa

- La tabla de `cProfile` tiene una fila por función y seis columnas:
  - `ncalls`: cuántas veces se llamó. Con recursión aparecen dos números,
    `total/primitivas`; las primitivas son las llamadas que no vienen de la
    misma función.
  - `tottime`: segundos gastados dentro de la función, sin contar lo que
    tardaron las funciones que ella llamó. Es la columna que dice dónde se
    gasta el tiempo.
  - `percall`: la primera, `tottime / ncalls`.
  - `cumtime`: segundos desde que entra hasta que sale, incluidas las
    funciones que llamó. La función de más arriba del programa siempre tiene
    el `cumtime` mayor.
  - `percall`: la segunda, `cumtime / llamadas primitivas`.
  - `filename:lineno(function)`: dónde está definida.
- `pstats.Stats.sort_stats(*claves)` ordena la tabla: `'tottime'` (o
  `'time'`) para encontrar la función que concentra el trabajo,
  `'cumulative'` (o `'cumtime'`) para ver quién la manda a llamar,
  `'calls'` para ordenar por `ncalls`. Las mismas claves están en el
  enumerado `pstats.SortKey`.
- `pstats.Stats.print_stats(*restricciones)` imprime la tabla ya ordenada.
  Un entero deja solo las primeras `n` filas, un decimal entre 0 y 1 deja
  esa fracción, una cadena filtra por expresión regular sobre el nombre.
  `strip_dirs()` recorta las rutas de los archivos; `print_callers()` y
  `print_callees()` muestran quién llama a quién.
- `cProfile.Profile.runcall(funcion, *args)` perfila una sola llamada;
  `dump_stats('perfil.prof')` deja el perfil en un archivo que después abre
  `pstats.Stats('perfil.prof')` o `python -m pstats perfil.prof`.
- `python -m pytest tests/test_suma_primos.py -v` corre las pruebas de esa
  parte y muestra una línea por prueba; el `pytest.ini` del repositorio corta
  cualquier prueba que pase de dos minutos.
- `timeit.timeit(lambda: funcion(N), number=VECES) / VECES` es lo que hace
  `scripts/comparar.py` con cada versión; el factor es el cociente de los dos
  promedios.

### Ejemplo

El perfil de `cuenta_perfectos(1000)`, del `lento.py` de la parte anterior,
ordenado de las dos maneras. En `perfil.py`:

```python
"""El perfil de cuenta_perfectos(1000), ordenado de dos maneras."""
import cProfile
import pstats

from lento import cuenta_perfectos

perfil = cProfile.Profile()
perfil.runcall(cuenta_perfectos, 1000)   # perfila solo esa llamada

estadisticas = pstats.Stats(perfil).strip_dirs()   # rutas cortas
estadisticas.sort_stats("tottime").print_stats(3)      # dónde se gasta el tiempo
estadisticas.sort_stats("cumulative").print_stats(3)   # quién lo manda a gastar
```

```bash
python perfil.py
```

```
         1005 function calls in 0.016 seconds

   Ordered by: internal time
   List reduced from 5 to 3 due to restriction <3>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      998    0.016    0.000    0.016    0.000 lento.py:6(suma_divisores)
        4    0.000    0.000    0.016    0.004 lento.py:15(<genexpr>)
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}


         1005 function calls in 0.016 seconds

   Ordered by: cumulative time
   List reduced from 5 to 3 due to restriction <3>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.016    0.016 lento.py:14(cuenta_perfectos)
        1    0.000    0.000    0.016    0.016 {built-in method builtins.sum}
        4    0.000    0.000    0.016    0.004 lento.py:15(<genexpr>)
```

La lectura: `suma_divisores` se llamó 998 veces y esas llamadas suman 0,016 s
de `tottime`: todo el tiempo del programa. Ordenado por `cumulative`,
`cuenta_perfectos` sube al primer puesto con el mismo 0,016 s, pero su
`tottime` es 0,000: no trabaja, manda a trabajar. Lo que hay que atacar es la
fila de arriba de la primera tabla, y hay dos caminos: que cada llamada
cueste menos o que haya menos llamadas. Aquí el problema es que cada `k`
busca sus divisores por separado, probando `k - 1` candidatos, cuando un
divisor `d` se puede repartir de una vez entre todos sus múltiplos. En
`rapida.py`:

```python
"""La versión que ataca lo que mostró el perfil: en vez de buscar los
divisores de cada k por separado, una sola pasada reparte cada d entre sus
múltiplos. Después se compara con la original usando timeit."""
import timeit

from lento import cuenta_perfectos


def cuenta_perfectos_rapida(n):
    suma = [0] * max(n, 1)
    for d in range(1, n // 2 + 1):
        for multiplo in range(2 * d, n, d):
            suma[multiplo] += d
    return sum(1 for k in range(2, n) if suma[k] == k)


if __name__ == "__main__":
    N, VECES = 5000, 3
    for n in (0, 1, 2, 7, 500, N):
        assert cuenta_perfectos_rapida(n) == cuenta_perfectos(n), n
    lenta = timeit.timeit(lambda: cuenta_perfectos(N), number=VECES) / VECES * 1000
    rapida = timeit.timeit(lambda: cuenta_perfectos_rapida(N), number=VECES) / VECES * 1000
    print(f"lenta  {lenta:9.2f} ms")
    print(f"rapida {rapida:9.2f} ms")
    print(f"factor {lenta / rapida:9.1f}")
```

```bash
python rapida.py
```

```
lenta     492.30 ms
rapida      2.16 ms
factor     228.3
```

El ciclo interno de la versión rápida da `n / d` vueltas para cada `d`, y la
suma de todas es del orden de `n · ln n`; la original hacía del orden de
`n²`. Con `n = 5.000` eso es la diferencia entre 492,3 ms y 2,2 ms.

### Lo que suele fallar

- El factor se queda en 2 o 3 y el flujo dice `la version rapida solo es 2.4
  veces mas rapida: el perfil apunta a otra cosa`. El cambio recortó lo que
  hace cada llamada (saltarse los pares, cortar antes) pero la columna
  `ncalls` sigue igual. Cuando el perfil muestra miles de llamadas a la misma
  función, el factor de diez sale de que esas llamadas dejen de existir, no
  de que cada una sea un poco más corta.
- Las pruebas fallan en `n = 0`, `1` o `2` y pasan en el resto. La versión
  nueva arma una tabla de tamaño `n` y con `n` pequeño queda vacía, o
  devuelve 1 donde la original devuelve 0. Los casos de borde se prueban
  antes que los grandes; el `assert` del ejemplo recorre seis valores.
- Se optimizó la función equivocada. Ordenada por `cumulative`, la primera
  fila es la función externa, que solo llama a las demás. La que trabaja es
  la primera fila ordenada por `tottime`.
- Todas las columnas del perfil dicen `0.000`. La llamada perfilada es
  demasiado corta para la resolución de la tabla; se perfila un `n` que tarde
  al menos unas decenas de milisegundos.
- `python -m scripts.comparar` tarda más de un minuto. Con `n = 200000` la
  versión original se corre tres veces y tarda lo que tarda; la nueva es la
  que tiene que ser corta. Si la nueva también tarda, la tabla auxiliar se
  está construyendo dentro de un ciclo en vez de una sola vez.

### Enlaces

- [Manual del perfilador: las columnas de la tabla](https://docs.python.org/3/library/profile.html):
  qué significa cada columna, las claves de `sort_stats` y los métodos de `Stats`.
- [timeit: medir la versión nueva contra la vieja](https://docs.python.org/3/library/timeit.html):
  la firma de `timeit.timeit` con un invocable y el argumento `number`.
- [pytest: cómo invocarlo](https://docs.pytest.org/en/stable/how-to/usage.html):
  correr un archivo, una clase o una prueba, y qué hace `-v`.
- [unittest: las aserciones de las pruebas del repositorio](https://docs.python.org/3/library/unittest.html):
  `assertEqual`, `assertIsInstance` y cómo se escribe una prueba nueva.
- [functools: lru_cache](https://docs.python.org/3/library/functools.html):
  cuando el perfil muestra la misma función llamada muchas veces con los
  mismos argumentos, guardar el resultado es otra forma de bajar `ncalls`.

## Parte 3: el producto punto tres veces

### Lo que se usa

- `np.array(objeto, dtype=None) -> ndarray` construye un arreglo a partir de
  una lista; `dtype=np.int64` fija enteros de 64 bits con signo, que aguantan
  hasta 9,2 × 10¹⁸. Un arreglo tiene `.dtype`, `.shape` y `.tolist()`, que
  devuelve una lista de `int` de Python.
- `np.random.default_rng(semilla)` crea un generador; `rng.integers(bajo, alto, tamaño, dtype=np.int64)`
  devuelve un arreglo de enteros en `[bajo, alto)`. Con la misma semilla
  salen los mismos números.
- `np.dot(a, b)` con dos vectores de la misma longitud es el producto punto:
  multiplica posición a posición y suma, en un solo ciclo en C. `a @ b` es
  el mismo cálculo escrito como operador (`np.matmul`); con vectores de una
  dimensión ambos devuelven un escalar.
- `np.sum(a) -> escalar` suma todas las posiciones. Las operaciones
  aritméticas entre arreglos, `a * b`, `a - b`, `a ** 2`, se aplican posición
  a posición y devuelven un arreglo nuevo del mismo tamaño.
- Lo que devuelven `np.dot`, `np.sum` y `a[i]` es un escalar de NumPy,
  `np.int64`, que no es `int` de Python: `isinstance(np.int64(3), int)` da
  `False`. `int(valor)` lo convierte.
- Indexar un `ndarray` desde un ciclo de Python es lento porque cada `a[i]`
  construye un objeto `np.int64` nuevo a partir de los bytes del arreglo, y
  la aritmética entre esos escalares vuelve a pasar por NumPy. Una lista ya
  tiene sus `int` construidos y `xs[i]` solo devuelve el puntero. Las
  operaciones vectorizadas recorren el arreglo una vez en C, sin crear un
  objeto por elemento.

### Ejemplo

La suma de los cuadrados de las diferencias de dos vectores de un millón de
enteros, en las tres formas. En `distancia.py`:

```python
"""La suma de los cuadrados de las diferencias de dos vectores, tres veces:
indexando arreglos de NumPy desde Python, con listas y zip, y con NumPy."""
import timeit

import numpy as np


def distancia_indexada(a, b):
    total = 0
    for i in range(len(a)):
        d = int(a[i]) - int(b[i])   # cada a[i] crea un escalar de NumPy
        total += d * d
    return total


def distancia_bucle(xs, ys):
    total = 0
    for x, y in zip(xs, ys):        # x, y ya son int de Python
        total += (x - y) * (x - y)
    return total


def distancia_numpy(a, b):
    d = a - b                        # un solo ciclo en C sobre los dos arreglos
    return int(np.sum(d * d))        # int() convierte el np.int64 en int


if __name__ == "__main__":
    N, VECES = 1000000, 5
    rng = np.random.default_rng(7)
    a = rng.integers(0, 50, N, dtype=np.int64)
    b = rng.integers(0, 50, N, dtype=np.int64)
    xs, ys = a.tolist(), b.tolist()

    esperado = distancia_numpy(a, b)
    assert distancia_bucle(xs, ys) == esperado
    assert distancia_indexada(a, b) == esperado
    print(f"resultado {esperado}  tipo {type(distancia_numpy(a, b)).__name__}")

    indexada = timeit.timeit(lambda: distancia_indexada(a, b), number=1) * 1000
    bucle = timeit.timeit(lambda: distancia_bucle(xs, ys), number=VECES) / VECES * 1000
    vector = timeit.timeit(lambda: distancia_numpy(a, b), number=VECES) / VECES * 1000
    print(f"indexada {indexada:9.2f} ms")
    print(f"bucle    {bucle:9.2f} ms")
    print(f"numpy    {vector:9.2f} ms")
    print(f"factor   {bucle / vector:9.1f}")
```

```bash
python distancia.py
```

```
resultado 415936954  tipo int
indexada    292.13 ms
bucle        72.51 ms
numpy         3.41 ms
factor        21.3
```

La versión de NumPy hace tres pasadas en C (la resta, el cuadrado y la suma)
y crea dos arreglos temporales; aun así gana por un factor que según la
corrida queda entre dieciséis y veintiuno. Un producto punto con `np.dot` es una
sola pasada sin temporales y gana por bastante más. Para ver de
dónde sale la diferencia entre indexar y recorrer una lista, `escalares.py`
mide una sola lectura de cada tipo y varias reducciones:

```python
"""Qué devuelve cada indexación y cuánto cuesta, con timeit."""
import timeit

import numpy as np

a = np.arange(1000000, dtype=np.int64)
xs = a.tolist()

print("a[3] es", type(a[3]).__name__, "   xs[3] es", type(xs[3]).__name__)
print("a * 2 es", type(a * 2).__name__, "de", (a * 2).dtype, "   np.sum(a) es", type(np.sum(a)).__name__)

n = 1000000
por_indice = timeit.timeit("a[500000]", globals=globals(), number=n) / n * 1e9
por_lista = timeit.timeit("xs[500000]", globals=globals(), number=n) / n * 1e9
print(f"leer a[i]  {por_indice:6.1f} ns    leer xs[i]  {por_lista:6.1f} ns")

# Tres reducciones del mismo arreglo: ciclo en Python, np.sum, producto punto.
print(f"sum(xs)     {timeit.timeit('sum(xs)', globals=globals(), number=5) / 5 * 1000:8.3f} ms")
print(f"np.sum(a)   {timeit.timeit('np.sum(a)', globals=globals(), number=5) / 5 * 1000:8.3f} ms")
print(f"np.sum(a*a) {timeit.timeit('np.sum(a * a)', globals=globals(), number=5) / 5 * 1000:8.3f} ms")
print(f"a @ a       {timeit.timeit('a @ a', globals=globals(), number=5) / 5 * 1000:8.3f} ms")
print("np.dot([1, 2, 3], [4, 5, 6]) =", np.dot([1, 2, 3], [4, 5, 6]))
```

```bash
python escalares.py
```

```
a[3] es int64    xs[3] es int
a * 2 es ndarray de int64    np.sum(a) es int64
leer a[i]    86.3 ns    leer xs[i]    13.9 ns
sum(xs)        4.378 ms
np.sum(a)      0.213 ms
np.sum(a*a)    0.563 ms
a @ a          0.595 ms
np.dot([1, 2, 3], [4, 5, 6]) = 32
```

Leer `a[i]` cuesta seis veces más que leer `xs[i]`, y eso antes de operar:
es el precio de construir el `np.int64`. Con enteros, `a @ a` y
`np.sum(a * a)` cuestan lo mismo; la ruta rápida de álgebra lineal que hace a
`np.dot` todavía mejor es para `float`.

### Lo que suele fallar

- `AssertionError: np.int64(70) is not an instance of <class 'int'>`. La
  función devolvió el escalar de NumPy tal cual; la prueba pide `int`. Se
  envuelve el resultado en `int(...)`.
- El flujo dice `numpy solo es 0.9 veces mas rapido que el ciclo: revise que
  no quede un ciclo de Python adentro`. `sum(a * b)` con el `sum` de Python
  recorre el arreglo elemento por elemento creando un escalar cada vez: sobre
  un millón de `int64`, `sum(a * a)` tardó 81,7 ms donde `np.sum(a * a)`
  tardó 0,6. Lo mismo pasa con una comprensión
  sobre el arreglo o con `range(len(a))`. Sin ciclo de Python quiere decir
  sin `for`, sin `sum` de Python y sin comprensión: solo `np.dot`, `@` o `np.sum`.
- El resultado de NumPy es distinto al de las listas y hasta negativo. Los
  arreglos son `int32`: un millón de productos de dos cifras suma hasta 10¹⁰
  y el `int32` da la vuelta en 2,1 × 10⁹ sin avisar; con `np.int32` y
  valores de 99 el producto punto de un millón de elementos da 1.211.065.408
  en vez de 9.801.000.000. Con `np.int64` cabe.
- `producto_punto_bucle` da un número más pequeño que los otros dos. `zip`
  se detiene en la lista más corta y no avisa; si una de las listas se
  recortó o se construyó con un `range` distinto, faltan términos. Las dos
  listas tienen que medir lo mismo, y `np.dot` sí avisa con
  `ValueError: shapes (3,) and (4,) not aligned`.
- La versión sobre listas convierte las listas a arreglos adentro
  (`np.array(xs)`) o la versión de NumPy convierte a listas. La conversión
  cuesta más que el cálculo y confunde las tres medidas: cada función trabaja
  sobre el tipo que recibe.

### Enlaces

- [Qué es NumPy y por qué es rápido](https://numpy.org/doc/stable/user/whatisnumpy.html):
  vectorización, arreglos homogéneos y el ciclo en C que reemplaza al de Python.
- [numpy.dot](https://numpy.org/doc/stable/reference/generated/numpy.dot.html):
  el producto punto de dos vectores y qué devuelve según las dimensiones.
- [numpy.matmul y el operador @](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html):
  la semántica del operador `@` para vectores y matrices.
- [numpy.sum](https://numpy.org/doc/stable/reference/generated/numpy.sum.html):
  la reducción sobre un arreglo, con `axis` y `dtype`.
- [Tipos de datos de NumPy](https://numpy.org/doc/stable/user/basics.types.html):
  `int32`, `int64`, los escalares de NumPy frente a los tipos de Python y el desbordamiento.
- [Generador de números aleatorios](https://numpy.org/doc/stable/reference/random/generator.html):
  `default_rng` e `integers`, que es lo que usan `vectorizar.py` y las pruebas.

## Parte 4: AVX a mano

### Lo que se usa

- `#include <immintrin.h>` trae los tipos y los intrínsecos de todas las
  extensiones vectoriales de x86. `__m256` es un registro de 256 bits con
  ocho `float`; `__m128` es la mitad, cuatro `float`. Cada intrínseco es una
  función que el compilador traduce a una instrucción. El catálogo completo,
  con la instrucción, la operación posición a posición y la latencia de cada
  uno, es la *Intel Intrinsics Guide*; se busca por ese nombre en el sitio
  de Intel.
- `_mm256_setzero_ps() -> __m256` deja las ocho posiciones en cero; es el
  valor inicial de un acumulador.
- `_mm256_loadu_ps(const float *p) -> __m256` carga ocho `float` seguidos
  desde `p`, con cualquier alineación. `_mm256_load_ps` hace lo mismo pero
  exige que `p` sea múltiplo de 32 bytes. `_mm256_storeu_ps(float *p, __m256 v)`
  es la escritura equivalente.
- `_mm256_mul_ps(a, b)`, `_mm256_add_ps(a, b)` y `_mm256_sub_ps(a, b)`
  operan posición a posición y devuelven un `__m256` nuevo.
- `_mm256_fmadd_ps(a, b, c) -> __m256` calcula `a * b + c` en cada posición
  con una sola instrucción y un solo redondeo. Necesita la extensión FMA:
  se compila con `-mfma` (o `-mavx2 -mfma`, o `-march=native`) y el
  compilador define la macro `__FMA__` cuando está habilitada.
- La reducción horizontal deja las ocho posiciones en un `float`:
  `_mm256_extractf128_ps(v, 1) -> __m128` saca la mitad alta (posiciones 4 a
  7) y `_mm256_castps256_ps128(v) -> __m128` la mitad baja sin costo;
  `_mm_add_ps` las suma en cuatro parciales; `_mm_hadd_ps(s, s)` suma
  parejas vecinas, y dos veces seguidas deja el total en la posición 0;
  `_mm_cvtss_f32(s) -> float` extrae esa posición.
- La cola: el ciclo vectorial avanza de a ocho mientras `i + 8 <= n`; los
  `n % 8` elementos que sobran se suman con un ciclo escalar que arranca en
  el `i` donde quedó el otro.
- `g++ -std=c++17 -O2 -mavx -fno-tree-vectorize` es lo que usa el `Makefile`:
  `-mavx` habilita los intrínsecos de 256 bits (sin ella no compilan) y
  `-fno-tree-vectorize` impide que el compilador vectorice por su cuenta el
  ciclo escalar. `-fopt-info-vec-optimized` imprime qué ciclos vectorizó.
- `std::chrono::high_resolution_clock::now()` y
  `duration_cast<microseconds>(t1 - t0).count()` son la medición del
  programa; `grep -o -w 'avx2\|avx\|fma' /proc/cpuinfo | sort -u` dice qué
  extensiones tiene el procesador.

### Ejemplo

La suma de los cuadrados de las diferencias de dos vectores de `float`, con
un ciclo escalar y con AVX. `n` no es múltiplo de ocho a propósito, para que
la cola cuente. En `distancia_avx.cpp`:

```cpp
// La suma de los cuadrados de las diferencias de dos vectores de floats,
// con un ciclo escalar y con intrínsecos AVX de a ocho floats por vuelta.
// n no es múltiplo de ocho a propósito: la cola se suma aparte.
#include <chrono>
#include <cstdio>
#include <immintrin.h>
#include <vector>

using namespace std;
using namespace std::chrono;

const size_t N = 1000005;
const int REPETICIONES = 100;

float escalar(const float *a, const float *b, size_t n) {
  float suma = 0.0f;
  for (size_t i = 0; i < n; i++) {
    float d = a[i] - b[i];
    suma += d * d;
  }
  return suma;
}

// Deja en un float la suma de las ocho posiciones de un registro __m256.
float reducir(__m256 v) {
  __m128 alto = _mm256_extractf128_ps(v, 1);   // posiciones 4..7
  __m128 bajo = _mm256_castps256_ps128(v);     // posiciones 0..3, sin costo
  __m128 s = _mm_add_ps(alto, bajo);           // cuatro sumas parciales
  s = _mm_hadd_ps(s, s);                       // dos
  s = _mm_hadd_ps(s, s);                       // una, en la posición 0
  return _mm_cvtss_f32(s);
}

float con_avx(const float *a, const float *b, size_t n) {
  __m256 acumulador = _mm256_setzero_ps();
  size_t i = 0;
  for (; i + 8 <= n; i += 8) {
    __m256 d = _mm256_sub_ps(_mm256_loadu_ps(a + i), _mm256_loadu_ps(b + i));
#ifdef __FMA__
    acumulador = _mm256_fmadd_ps(d, d, acumulador);   // d*d + acumulador
#else
    acumulador = _mm256_add_ps(acumulador, _mm256_mul_ps(d, d));
#endif
  }
  float suma = reducir(acumulador);
  for (; i < n; i++) {                         // la cola: n % 8 elementos
    float d = a[i] - b[i];
    suma += d * d;
  }
  return suma;
}

int main() {
  vector<float> a(N), b(N);
  for (size_t i = 0; i < N; i++) {
    a[i] = (float)(i % 3);
    b[i] = (float)(i % 2);
  }
  float r1 = 0, r2 = 0;
  auto t0 = high_resolution_clock::now();
  for (int k = 0; k < REPETICIONES; k++) r1 = escalar(a.data(), b.data(), N);
  auto t1 = high_resolution_clock::now();
  for (int k = 0; k < REPETICIONES; k++) r2 = con_avx(a.data(), b.data(), N);
  auto t2 = high_resolution_clock::now();
  printf("escalar %.1f ms resultado %.0f\n",
         duration_cast<microseconds>(t1 - t0).count() / 1000.0, r1);
  printf("avx     %.1f ms resultado %.0f\n",
         duration_cast<microseconds>(t2 - t1).count() / 1000.0, r2);
  return 0;
}
```

```bash
g++ -std=c++17 -O2 -mavx -fno-tree-vectorize -o distancia_avx distancia_avx.cpp
./distancia_avx
g++ -std=c++17 -O2 -mavx2 -mfma -fno-tree-vectorize -o distancia_fma distancia_avx.cpp
./distancia_fma
```

```
escalar 78.6 ms resultado 1166673
avx     9.9 ms resultado 1166673
escalar 78.2 ms resultado 1166673
avx     16.3 ms resultado 1166673
```

Los dos resultados coinciden, con la cola de cinco elementos incluida, y el
factor es 7,9. En las dos versiones cada vuelta del ciclo espera a que la
anterior termine de escribir el acumulador: la suma escalar tarda tres ciclos
por elemento y la suma AVX tres ciclos por ocho elementos, y de ahí sale un
techo de ocho. Lo que lo baja es todo lo que no es esa suma: las dos cargas
por vuelta, la reducción y la cola, que son costo fijo, y la memoria cuando
los vectores no caben en caché, que aquí son ocho megabytes. La versión con
FMA lo muestra desde otro lado: sale más lenta, 16,3 ms contra 9,9, porque en
este procesador un FMA tarda cinco ciclos y una suma tres, y en la forma
`mul + add` la multiplicación queda fuera de la cadena de espera. Romper la
cadena es lo que da más: con vectores de 30.005 elementos, que caben en la
caché L2, y 3.000 repeticiones, un solo acumulador tarda 8,8 ms y cuatro
acumuladores independientes 5,9 ms.

Sin `-fno-tree-vectorize`, el compilador hace lo que aquí se escribió a mano
y mejor, con ocho acumuladores; los dos avisos de la línea 46 son la cola de
`con_avx`, vectorizada aparte con registros de 128 bits:

```bash
g++ -std=c++17 -O2 -mavx -fopt-info-vec-optimized -o o2 distancia_avx.cpp && ./o2
```

```
distancia_avx.cpp:17:24: optimized: loop vectorized using 32 byte vectors and unroll factor 8
distancia_avx.cpp:46:12: optimized: loop vectorized using 16 byte vectors and unroll factor 4
distancia_avx.cpp:46:12: optimized: loop vectorized using 16 byte vectors and unroll factor 4
distancia_avx.cpp:61:21: optimized: loop vectorized using 32 byte vectors and unroll factor 8
escalar 3.1 ms resultado 1166673
avx     9.9 ms resultado 1166673
```

### Lo que suele fallar

- `error: inlining failed in call to 'always_inline' '__m128 _mm_hadd_ps(__m128, __m128)': target specific option mismatch`.
  Se compiló sin `-mavx`: los intrínsecos existen en el encabezado pero el
  compilador no tiene permiso de emitir esas instrucciones. Con
  `_mm256_fmadd_ps` el mismo mensaje aparece si falta `-mfma`.
- `Segmentation fault` (código de salida 139) en la carga. Se usó
  `_mm256_load_ps` sobre una dirección que no es múltiplo de 32 bytes; la
  memoria de un `std::vector<float>` no lo garantiza. `_mm256_loadu_ps`
  acepta cualquier dirección.
- `las dos versiones no dan el mismo producto punto`, y la diferencia es
  pequeña: 1166667 contra 1166673 en el ejemplo. Faltó la cola: el ciclo de
  a ocho se detuvo en el último múltiplo de ocho y los `n % 8` elementos
  finales nunca se sumaron. Con `2^20` posiciones no se nota, con
  `1.000.005` sí.
- El resultado de AVX es más o menos la mitad del escalar. La reducción se
  hizo con `_mm256_hadd_ps` dos veces sobre el registro de 256 bits: esa
  instrucción suma parejas dentro de cada mitad de 128 bits y nunca cruza de
  una mitad a la otra, así que queda la suma de la mitad baja (10 en vez de
  36 sobre `1..8`). Primero `_mm256_extractf128_ps` y `_mm_add_ps`, después
  los `_mm_hadd_ps`.
- El acumulador arranca con basura y el resultado cambia en cada corrida.
  `__m256 acumulador;` no inicializa nada; va `_mm256_setzero_ps()`.
- `AVX no salio al menos tres veces mas rapido que el ciclo escalar` con el
  escalar en 3 ms. Se compiló con `-O3` o sin `-fno-tree-vectorize` y el
  compilador vectorizó el ciclo escalar por su cuenta; el `Makefile` del
  repositorio ya trae la bandera, y `make -C avx producto_punto` la usa.
- `Illegal instruction (core dumped)` al ejecutar. El procesador, o la
  máquina virtual, no expone AVX; `grep -o -w avx /proc/cpuinfo` lo confirma,
  y en ese caso la parte solo corre en el servidor de Actions.

### Enlaces

- [Opciones de GCC para x86](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html):
  `-mavx`, `-mavx2`, `-mfma`, `-march=native` y qué habilita cada una.
- [Opciones de optimización de GCC](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html):
  `-O2`, `-O3`, `-ftree-vectorize` y su negación.
- [Opciones de desarrollador de GCC](https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html):
  `-fopt-info-vec-optimized`, que dice qué ciclos vectorizó el compilador.
- [std::chrono::high_resolution_clock en cppreference](https://en.cppreference.com/w/cpp/chrono/high_resolution_clock):
  el reloj del programa y cómo se convierten las duraciones.
- [uops.info](https://uops.info/):
  la latencia y el rendimiento medidos de cada instrucción por
  microarquitectura, para explicar por qué el factor no llega a ocho.

## Cómo compilar y ejecutar en la máquina propia

En Debian o Ubuntu hace falta el intérprete con el módulo `venv`, el
compilador y `make`:

```bash
sudo apt install python3 python3-venv python3-pip build-essential git
grep -o -w 'avx2\|avx\|fma' /proc/cpuinfo | sort -u     # qué extensiones hay
```

Con eso, desde la raíz del repositorio, el flujo completo es el del README:
`python3 -m venv .venv`, `source .venv/bin/activate`,
`pip install -r requirements.txt`, los scripts con `python -m scripts.<nombre>`,
las pruebas con `python -m pytest tests/ -v` y la parte de AVX con
`make -C avx producto_punto`. Para compilar a mano, las banderas son las del
`Makefile`, `-std=c++17 -O2 -mavx -fno-tree-vectorize`; si el procesador tiene
FMA y se quiere probar `_mm256_fmadd_ps`, se agregan `-mavx2 -mfma`, o
`-march=native` para habilitar todo lo que el procesador tenga. Si en la
distribución `python` no existe y solo hay `python3`, dentro del entorno
virtual activado `python` sí existe; fuera de él, el paquete
`python-is-python3` lo agrega.

En Windows todo corre dentro de WSL2 con Ubuntu: `wsl --install` desde una
terminal de PowerShell con permisos de administrador instala el subsistema y
la distribución, y de ahí en adelante los comandos son los de arriba. El
repositorio conviene clonarlo dentro del sistema de archivos de Linux, en
`~/`, y no en `/mnt/c/...`: el acceso al disco de Windows desde WSL es lento,
y los tiempos de la parte 3 se distorsionan. WSL2 expone las extensiones del
procesador, así que el `grep` sobre `/proc/cpuinfo` dice si AVX está
disponible. Los editores de Windows suelen guardar los archivos con fin de
línea CRLF; Git avisa con `warning: LF will be replaced by CRLF` y
`git config core.autocrlf input` lo deja en LF.

En macOS el compilador es `clang++`, que viene con las herramientas de línea
de comandos de Xcode (`xcode-select --install`) junto con `make` y `git`;
`g++` en un Mac es un alias de `clang++`. Las partes 1 a 3 corren igual que
en Linux con el `python3` del sistema o el de Homebrew. La parte 4 depende
del procesador: en un Mac con Intel, `clang++` acepta `-mavx`,
`-fno-tree-vectorize` y las mismas banderas; en un Mac con Apple Silicon no
existe `immintrin.h` porque el procesador es ARM y no tiene AVX, y esa parte
se verifica solo con el flujo de Actions después del push.

- [Uso de Python en plataformas Unix](https://docs.python.org/3/using/unix.html):
  cómo se instala y dónde queda Python en cada distribución.
- [Uso de Python en macOS](https://docs.python.org/3/using/mac.html):
  el intérprete del sistema, el instalador oficial y los entornos virtuales.
- [Instalar WSL](https://learn.microsoft.com/en-us/windows/wsl/install):
  `wsl --install`, cómo elegir la distribución y cómo abrir la terminal de Linux.
- [Página de manual de make](https://man7.org/linux/man-pages/man1/make.1.html):
  las opciones de `make`, entre ellas `-C`, que es la que usa el README para
  compilar dentro de `avx/`.
