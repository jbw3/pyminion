from pyminion.core import Expansion


def test_expansion_name():
    expansion = Expansion("Test", [])
    assert expansion.name == "Test"
