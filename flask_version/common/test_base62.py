from base62 import encode, decode


def test_encode_zero():
    assert encode(0) == "0"


def test_roundtrip():
    for n in [1, 42, 123456789, 2**31, 2**40]:
        assert decode(encode(n)) == n


def test_known_values():
    assert encode(10) == "a"
    assert encode(61) == "Z"
