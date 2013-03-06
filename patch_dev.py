#!/usr/bin/env python
'''
Make developing using salt-contrib easier.

Assuming you have already cloned salt-contrib...

git clone git@github.com:saltstack/salt.git
git clone git@github.com:<me>/salt-contrib.git

salt-contrib/patch_dev.py salt

Then you can test your modules in the usual way

salt/tests/runtests.py -n integration.modules.<mymodule>

You can remove all links by running with -u which should
leave the salt repo as it was.
'''
import os
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr)

current_dir = os.path.realpath(os.path.dirname(__file__))

unsafe_modules = ('ansible',)

def get_files(target):
    '''
    Returns a list of (source, dest) tuples
    '''
    for dirname, dirnames, filenames in os.walk(current_dir):
        rel = dirname[len(current_dir)+1:]
        parts = rel.split('/')
        # skip current dir
        if not rel:
            continue

        base = '' if parts[0] == 'tests' else 'salt'

        def f(x):
            if x[:-3] in unsafe_modules:
                return False
            if x == '__init__.py':
                return False
            if x[-3:] == '.py':
                return True
            if parts[-1] in ('files', 'mockbin'):
                return True
            return False

        for module in filter(f, filenames):
            yield (os.path.join(dirname, module),
                   os.path.join(target, base, rel, module))


def install(path):
    count = 0

    for f in get_files(path):
        # clear dead links
        if os.path.islink(f[1]) and os.path.realpath(f[1]) != f[0]:
            os.unlink(f[1])

        if not os.path.islink(f[1]):
            logger.info("Linking {0}".format(f[0]))
            try:
                os.symlink(f[0], f[1])
                count += 1
            except:
                logger.warning("Failed to created {0}".format(f[1]))

    print "Linked {0} items".format(count)


def uninstall(path):
    '''
    Finds files linked to the current directory and removes them
    '''
    count = 0

    for dirname, dirnames, filenames in os.walk(path):
        for filename in ["{0}/{1}".format(dirname, f) for f in filenames]:
            real = os.path.realpath(filename)
            if real.startswith(current_dir):
                logger.info("Unlinking {0}".format(filename))
                os.unlink(filename)

                # get rid of bytecode
                if os.path.exists(filename + "c"):
                    os.unlink(filename + "c")

                count += 1

    print "Unlinked {0} items".format(count)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser("Symlinks salt-contrib onto existing development environment")
    parser.add_argument('path', help='Path to salt dev (e.g. where you cloned saltstack/salt.git)')
    parser.add_argument('-u', '--uninstall', action='store_true', help='Remove symlinks from the dev environment')
    parser.add_argument('-r', '--refresh', action='store_true', help='Remove and re-apply links')

    options = parser.parse_args()

    if not os.path.isdir("{0}/salt/modules".format(options.path)):
        parser.error("{0} doesn't seem to be a valid salt environment".format(options.path))

    path = os.path.realpath(options.path)

    if options.refresh:
        uninstall(path)
        install(path)
    elif options.uninstall:
        uninstall(path)
    else:
        install(path)
