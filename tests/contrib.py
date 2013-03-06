from saltunittest import TestSuite, TestLoader
import os

tests = TestSuite()

current_dir = os.path.realpath(os.path.dirname(__file__))
l = len(current_dir)

names = []
for dirname, dirs, files in os.walk(current_dir):
    parts = dirname[l:].split(os.sep)
    module = '.'.join(parts[1:])

    for f in files:
        if f[-8:] == '_test.py':
            names.append('{0}.{1}'.format(module, f[:-3]))

loader = TestLoader()
tests.addTest(loader.loadTestsFromNames(names))
