import pytest

from math_mcp.server import add, divide, multiply, subtract


class TestAdd:
    def test_positive_numbers(self):
        assert add(3, 4) == 7

    def test_negative_numbers(self):
        assert add(-3, -4) == -7

    def test_floats(self):
        assert add(1.5, 2.5) == 4.0

    def test_zero(self):
        assert add(0, 5) == 5


class TestSubtract:
    def test_basic(self):
        assert subtract(10, 4) == 6

    def test_negative_result(self):
        assert subtract(3, 10) == -7

    def test_floats(self):
        assert subtract(5.5, 2.5) == 3.0


class TestMultiply:
    def test_positive(self):
        assert multiply(4, 7) == 28

    def test_by_zero(self):
        assert multiply(99, 0) == 0

    def test_floats(self):
        assert multiply(2.5, 4) == 10.0

    def test_negative(self):
        assert multiply(-3, 5) == -15


class TestDivide:
    def test_exact(self):
        assert divide(20, 4) == 5.0

    def test_float_result(self):
        assert divide(10, 3) == pytest.approx(3.333, rel=1e-3)

    def test_negative(self):
        assert divide(-12, 4) == -3.0

    def test_divide_by_zero(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(5, 0)
