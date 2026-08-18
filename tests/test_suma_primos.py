import unittest

from src.suma_primos import suma_primos


class TestSumaPrimos(unittest.TestCase):
    def test_suma_primos(self):
        self.assertEqual(suma_primos(10), 17)   # 2 + 3 + 5 + 7
        self.assertEqual(suma_primos(20), 77)   # 2 + 3 + 5 + 7 + 11 + 13 + 17 + 19


if __name__ == "__main__":
    unittest.main()
