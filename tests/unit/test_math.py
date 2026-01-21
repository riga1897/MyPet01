from mypet_project.utils.math import add, subtract

def test_add():
    assert add(10, 5) == 15

def test_subtract():
    assert subtract(10, 5) == 5
