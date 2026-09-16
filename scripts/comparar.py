"""Compara la suma de primos original con la versión rápida, con timeit."""
import timeit

from src.suma_primos import suma_primos, suma_primos_rapida

N = 200000
VECES = 3


def medir(funcion):
    return timeit.timeit(lambda: funcion(N), number=VECES) / VECES * 1000


if __name__ == "__main__":
    assert suma_primos(N) == suma_primos_rapida(N), "las dos sumas no coinciden"
    lenta = medir(suma_primos)
    rapida = medir(suma_primos_rapida)
    print(f"lenta  {lenta:10.1f} ms")
    print(f"rapida {rapida:10.1f} ms")
    print(f"factor {lenta / rapida:10.1f}")
