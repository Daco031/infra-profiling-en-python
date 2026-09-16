import unittest

from src.suma_primos import suma_primos, suma_primos_rapida


class TestSumaPrimos(unittest.TestCase):
    def test_suma_primos(self):
        self.assertEqual(suma_primos(10), 17)   # 2 + 3 + 5 + 7
        self.assertEqual(suma_primos(20), 77)   # 2 + 3 + 5 + 7 + 11 + 13 + 17 + 19

    def test_la_rapida_da_lo_mismo(self):
        self.assertEqual(suma_primos_rapida(10), 17)
        self.assertEqual(suma_primos_rapida(20), 77)
        for n in (0, 1, 2, 3, 100, 1000, 7919):
            self.assertEqual(suma_primos_rapida(n), suma_primos(n))


if __name__ == "__main__":
    unittest.main()
