import unittest

import numpy as np

from src.vectores import (producto_punto_bucle, producto_punto_indexado,
                          producto_punto_numpy)


class TestVectores(unittest.TestCase):
    def setUp(self):
        self.xs = [1, 2, 3, 4]
        self.ys = [5, 6, 7, 8]
        self.a = np.array(self.xs, dtype=np.int64)
        self.b = np.array(self.ys, dtype=np.int64)

    def test_indexado(self):
        self.assertEqual(producto_punto_indexado(self.a, self.b), 70)

    def test_bucle(self):
        self.assertEqual(producto_punto_bucle(self.xs, self.ys), 70)
        self.assertEqual(producto_punto_bucle([], []), 0)

    def test_numpy(self):
        self.assertEqual(producto_punto_numpy(self.a, self.b), 70)
        self.assertIsInstance(producto_punto_numpy(self.a, self.b), int)

    def test_las_tres_coinciden(self):
        rng = np.random.default_rng(2026)
        a = rng.integers(0, 100, 5000, dtype=np.int64)
        b = rng.integers(0, 100, 5000, dtype=np.int64)
        esperado = producto_punto_indexado(a, b)
        self.assertEqual(producto_punto_bucle(a.tolist(), b.tolist()), esperado)
        self.assertEqual(producto_punto_numpy(a, b), esperado)


if __name__ == "__main__":
    unittest.main()
