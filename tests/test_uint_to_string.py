from brownie.test import given, strategy


def uint_to_string(value: int) -> str:
    """Convert an unsigned 256 bit integer to its ASCII string representation"""
    if value == 0:
        return "0"

    buffer = ""
    max_len = len(str(2 ** 256 - 1))
    digits = 0
    for i in range(1, max_len + 1):
        if value // 10 ** i == 0:
            digits = i
            break

    # go backwards from end to start
    for i in range(max_len - 1, -1, -1):
        # get rid of everything below, then everything above
        buffer += chr(((value // 10 ** i) % 10) + 48)

    return buffer[-digits:]


@given(value=strategy("uint256"))
def test_python_version(value):
    assert uint_to_string(value) == str(value)


@given(value=strategy("uint256"))
def test_veboost_version(value, veboost):
    assert veboost.uint_to_string(value) == str(value)
