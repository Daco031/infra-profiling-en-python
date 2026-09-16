"""El producto punto de dos vectores, tres veces: indexando un arreglo de
NumPy desde Python, recorriendo listas de Python, y con NumPy vectorizado."""
import numpy as np


def producto_punto_indexado(a, b):
    """Recorre dos arreglos de NumPy por índice desde un ciclo de Python.
    Es la forma más lenta de las tres: cada a[i] saca un escalar del arreglo
    y lo convierte en un objeto de Python."""
    total = 0
    for i in range(len(a)):
        total += int(a[i]) * int(b[i])
    return total


def producto_punto_bucle(xs, ys):
    """TODO: el producto punto de dos listas de Python, con un ciclo y zip."""
    raise NotImplementedError


def producto_punto_numpy(a, b):
    """TODO: el producto punto de dos arreglos de NumPy, sin ciclos de Python.
    Devolver un int de Python."""
    raise NotImplementedError
