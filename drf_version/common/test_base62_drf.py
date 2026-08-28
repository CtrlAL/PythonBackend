from base62 import encode, decode


def test_roundtrip():
    for n in [0, 1, 42, 123456789, 2**40, 2**62]:
        assert decode(encode(n)) == n


def test_known():
    assert encode(10) == "a"
    assert encode(61) == "Z"
