============
Salt Contrib
============

The Salt Contrib is a destination for modules developed by the community.
Since Salt modules are nearly infinite in application not all of the modules
developed will be shipped with the main salt application. Salt Contrib will
hold modules that can be cleanly added to any of the modular componets of
Salt. This will also act as a gateway for new module development, generally
it will be asked that pull requests for new modules be made against the
salt-contrib git repo.

Development
===========

You symlink your ``salt-contrib`` against a development environment and run
the tests against it.  All python files, plus the contents of the ``files``
and ``mockbin`` directories will be symlinked to the same location in the
salt repo, so you can modify linked files and test without having to copy
files back and forward.  Running ``salt-contrib/patch_dev.py salt -u`` will
remove all links leaving the salt repo clean.  The ``contrib.tests`` 
target runs only the tests from ``salt-contrib``.

::

  $ git clone git://github.com/saltstack/salt.git
  $ git clone git@github.com:<me>/salt-contrib.git

  $ salt-contrib/patch-dev.py salt

  $ salt/tests/runtests.py -n contrib.tests
