import io
import sys
from time import sleep
import unittest
from fzfaws.utils import Spinner


class TestSpinner(unittest.TestCase):
    def setUp(self):
        self.spinner = Spinner()
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_default(self):
        spinner = Spinner()
        self.assertEqual(spinner.message, "loading ...")
        self.assertEqual(spinner.pattern, "|/-\\")
        self.assertEqual(spinner.speed, 0.1)
        self.assertEqual(spinner.no_progress, False)

    def test_nondefault(self):
        spinner = Spinner(
            pattern="1234", message="hello..", speed=0.01, no_progress=True
        )
        self.assertEqual(spinner.message, "hello..")
        self.assertEqual(spinner.pattern, "1234")
        self.assertEqual(spinner.speed, 0.01)
        self.assertEqual(spinner.no_progress, True)

    def test_no_progress(self):
        with Spinner.spin(no_progress=True):
            print("hello")
        self.assertEqual(self.capturedOutput.getvalue(), "hello\n")

    def test_spin(self):
        self.spinner.start()
        self.assertTrue(Spinner.instances)
        sleep(0.4)
        self.spinner.stop()
        self.assertRegex(self.capturedOutput.getvalue(), r".*[|/-\\]\sloading.*")
        Spinner.clear_spinner()
        self.assertEqual(Spinner.instances, [])

    def test_context(self):
        with Spinner.spin(message="hello"):
            response = 1 + 1
        self.assertEqual(response, 2)
        self.assertRegex(self.capturedOutput.getvalue(), r".*[|/-\\]\shello.*")

        try:
            with Spinner.spin():
                raise Exception
        except:
            self.assertEqual(Spinner.instances, [])
