from saltunittest import TestSuite, TestLoader
import os

tests = TestSuite()
loader = TestLoader()

# add some useful tests from the main suite
extra = ('integration.modules.sysmod', )
tests.addTest(loader.loadTestsFromNames(extra))

# this should resolve to the salt-contrib directory
current_dir = os.path.dirname(os.path.realpath(__file__))
l = len(current_dir)

names = []
for dirname, dirs, files in os.walk(current_dir):
    parts = dirname[l:].split(os.sep)
    if len(parts) < 2:
        continue

    module = '.'.join(parts[1:])
    for f in files:
        if f[-3:] == '.py':
            names.append('{0}.{1}'.format(module, f[:-3]))

print names
tests.addTest(loader.loadTestsFromNames(names))
