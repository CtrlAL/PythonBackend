# fastapi_version/common/base62.py
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABET_SIZE = len(ALPHABET)


def encode(n):
    if n == 0:
        return ALPHABET[0]

    encoded = ""
    number = n

    while number > 0:
        encoded += ALPHABET[number % ALPHABET_SIZE]
        number //= ALPHABET_SIZE

    return encoded[::-1]


def decode(encoded):
    number = 0

    for char in encoded:
        number = number * ALPHABET_SIZE + ALPHABET.index(char)

    return number
