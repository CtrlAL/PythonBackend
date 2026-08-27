# fastapi_version/common/base62.py
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)
def encode(n):
    if n == 0: return ALPHABET[0]
    s = ""
    while n > 0:
        s += ALPHABET[n % BASE]; n //= BASE
    return s[::-1]
def decode(s):
    n = 0
    for c in s: n = n * BASE + ALPHABET.index(c)
    return n
