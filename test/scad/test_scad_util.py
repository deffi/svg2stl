import unittest

from svg2fff.model import Point
from svg2fff.scad import render


class TestScadUtil(unittest.TestCase):
    def test_render(self):
        self.assertEqual(render(42), "42")
        self.assertEqual(render(42.0), "42.0")

        self.assertEqual(render([1, 2, 33]), "[1, 2, 33]")
        self.assertEqual(render((1, 2, 33)), "[1, 2, 33]")

        p1 = Point(11, 12)
        p2 = Point(21, 22)
        self.assertEqual(render(p1), "[11, 12]")
        self.assertEqual(render(p2), "[21, 22]")
        self.assertEqual(render([p1, p2]), "[[11, 12], [21, 22]]")

        with self.assertRaises(ValueError):
            render("foo")


if __name__ == '__main__':
    unittest.main()
