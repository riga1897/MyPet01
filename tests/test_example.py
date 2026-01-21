from django.test import TestCase

class ExampleTest(TestCase):
    def test_math(self) -> None:
        self.assertEqual(1 + 1, 2)
