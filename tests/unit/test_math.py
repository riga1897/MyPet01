from mypet_project.utils.math import add, subtract

def test_add() -> None:
    assert add(10, 5) == 15

def test_subtract() -> None:
    assert subtract(10, 5) == 5
