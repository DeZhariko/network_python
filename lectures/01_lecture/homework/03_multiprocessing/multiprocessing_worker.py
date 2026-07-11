def is_prime_worker(n: int) -> bool:
    if n < 2:
        return False

    if n == 2:
        return True

    if n % 2 == 0:
        return False

    divisor = 3

    while divisor * divisor <= n:
        if n % divisor == 0:
            return False

        divisor += 2

    return True


def heavy_compute_worker(x: int) -> int:
    total = 0

    for number in range(2, x + 1):
        if is_prime_worker(number):
            total += number

    return total