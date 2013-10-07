#!/usr/bin/env python
'''
Make developing using salt-contrib easier.

Symlinks the contents of salt-contrib onto other environments
for testing or deployment.  See ``link_contrib.py --help`` for
more info.

Linking against a development repo::

  git clone git://github.com/saltstack/salt.git
  git clone git@github.com:<me>/salt-contrib.git
  
  salt-contrib/link_contrib.py salt
  
  salt/tests/runtests.py -n contrib.tests -v
  
Linking against an actual state env::

  salt_contrib/link_contrib.py /srv/salt
  
Removing links:
  
  salt_contrib/link_contrib.py /srv/salt --uninstall

'''
import os
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

current_dir = os.path.realpath(os.path.dirname(__file__))

base_folders = ('grains', 'modules', 'renderers', 'runners', 'states')

unsafe_modules = ('ansible','drizzle')

def get_files(target, exclude, folders = base_folders):
    '''
    Returns a list of files to link
    '''
    for dirname, dirnames, filenames in os.walk(current_dir):
        rel = dirname[len(current_dir)+1:]
        parts = rel.split('/')
        
        if len(parts) == 0:
            continue
        
        if not parts[0] in folders:
            continue
        
        # filter out unwanted items
        def f(x):
            if x[:-3] in exclude:
                return False
            if x == '__init__.py':
                return False
            if x[-4:] == '.pyc':
                return False
            return True

        for module in filter(f, filenames):
            yield os.path.join(rel, module)

def link(source, dest):
    '''
    Creates symlinks.
    Also creates directories if required and tries to clean out old links
    '''
    source = os.path.realpath(source)
    
    d = os.path.dirname(dest)
    if not os.path.isdir(d):
        os.makedirs(d)
    
    # remove dead links (e.g. to old salt-contrib)
    if os.path.islink(dest) and os.path.realpath(dest) != source:
        logger.warning("Removing dead link: {0}".format(dest))
        os.unlink(dest)
    
    # link to dest
    if not os.path.islink(dest):
        logger.debug("Linking {0}".format(source))
        try:
            os.symlink(source, dest)
            return True
        except:
            logger.warning("Failed to created {0}".format(dest))
            
    return False
            
def install(target, opts):
    '''
    Link files in current directory to another environment
    for testing / deployment.
    '''
    # figure out what type of install to do
    if os.path.exists(os.path.join(target, 'top.sls')):
        active = True
        logger.info("Linking to active env")
    elif os.path.exists(os.path.join(target, 'salt', '__init__.py')):
        active = False
        logger.info("Linking to development repo")
    else:
        raise Exception("Expected either a top.sls file or a salt module")
    
    exclude = unsafe_modules + tuple(opts.exclude)
    logger.info("Excluding {0}".format(', '.join(exclude)))
    
    # python modules
    count = 0
    for source in get_files(target, exclude):
        if active:
            dest = os.path.join(target, '_{0}'.format(source))
        else:
            dest = os.path.join(target, 'salt', source)
        
        if link(os.path.join(current_dir, source), dest):
            count += 1
            
    sys.stderr.write("Linked {0} items\n".format(count))
    
    if active == False:
        # add the tests as well
        count = 0
        for source in get_files(target, exclude, ('tests',)):
            dest = os.path.join(target, source)
            
            if link(os.path.join(current_dir, source), dest):
                count += 1
                
        sys.stderr.write("Linked {0} test items\n".format(count))
    

def uninstall(target, opts):
    '''
    Finds files in target path linked to the current directory and removes them.
    '''
    count = 0

    for dirname, dirnames, filenames in os.walk(target):
        for filename in ["{0}/{1}".format(dirname, f) for f in filenames]:
            real = os.path.realpath(filename)
            if real.startswith(current_dir):
                logger.debug("Unlinking {0}".format(filename))
                os.unlink(filename)

                # get rid of bytecode
                if os.path.exists(filename + "c"):
                    os.unlink(filename + "c")

                count += 1

    sys.stderr.write("Unlinked {0} items\n".format(count))

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to target, either a salt repo or an sls base')
    parser.add_argument('-u', '--uninstall', action='store_true', help='Remove symlinks from the environment')
    parser.add_argument('-r', '--refresh', action='store_true', help='Remove and re-apply links')
    parser.add_argument('-x', '--exclude', nargs='*', default=[], help='Exclude specific python modules')

    options = parser.parse_args()

    path = os.path.realpath(options.path)

    if options.refresh or options.uninstall:
        uninstall(path, options)
        
    if options.uninstall:
        return

    install(path, options)
        
if __name__ == '__main__':
    main()
