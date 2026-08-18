def es_primo(num):
    """Devuelve True si num es primo. Implementación deliberadamente ingenua."""
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True


def suma_primos(n):
    """Suma todos los primos menores que n."""
    return sum(i for i in range(2, n) if es_primo(i))
