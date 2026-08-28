ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABET_SIZE = len(ALPHABET)


def encode(number: int) -> str:
    if number == 0:
        return ALPHABET[0]

    encoded = ""
    while number > 0:
        encoded += ALPHABET[number % ALPHABET_SIZE]
        number //= ALPHABET_SIZE

    return encoded[::-1]


def decode(s: str) -> int:
    decoded = 0
    for char in s:
        decoded = decoded * ALPHABET_SIZE + ALPHABET.index(char)

    return decoded
