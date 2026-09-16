"""Mide las tres formas del producto punto sobre un millón de elementos."""
import timeit

import numpy as np

from src.vectores import (producto_punto_bucle, producto_punto_indexado,
                          producto_punto_numpy)

N = 1000000
VECES = 5

if __name__ == "__main__":
    rng = np.random.default_rng(2026)
    a = rng.integers(0, 100, N, dtype=np.int64)
    b = rng.integers(0, 100, N, dtype=np.int64)
    xs, ys = a.tolist(), b.tolist()

    esperado = producto_punto_numpy(a, b)
    assert producto_punto_bucle(xs, ys) == esperado, "el bucle no da lo mismo que numpy"

    indexado = timeit.timeit(lambda: producto_punto_indexado(a, b), number=1) * 1000
    bucle = timeit.timeit(lambda: producto_punto_bucle(xs, ys), number=VECES) / VECES * 1000
    numpy = timeit.timeit(lambda: producto_punto_numpy(a, b), number=VECES) / VECES * 1000
    print(f"indexado {indexado:10.2f} ms")
    print(f"bucle    {bucle:10.2f} ms")
    print(f"numpy    {numpy:10.2f} ms")
    print(f"factor   {bucle / numpy:10.1f}")
