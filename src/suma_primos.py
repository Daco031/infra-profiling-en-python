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


def suma_primos_rapida(n):
    """TODO: la misma suma, escrita a partir de lo que mostró el perfil.

    Tiene que devolver exactamente lo mismo que suma_primos(n) para todo n.
    """
    raise NotImplementedError
