============
Salt Contrib
============

The Salt Contrib is a destination for modules developed by the community.
Since Salt modules are nearly infinite in application not all of the modules
developed will be shipped with the main salt application. Salt Contrib will
hold modules that can be cleanly added to any of the modular components of
Salt. This will also act as a gateway for new module development, generally
it will be asked that pull requests for new modules be made against the
salt-contrib git repo.

Development
===========

.. image:: https://travis-ci.org/tf198/salt-contrib.png?branch=develop

You can symlink your ``salt-contrib`` against a development environment and run
the tests against it.

All relevant files will be symlinked to the appropriate location in the
target environment, so you can modify linked files and test without having to copy
files back and forward.  Running ``salt-contrib/link_contrib.py salt -u`` will
remove all links leaving the salt repo clean.

The ``contrib.tests`` target runs only the tests from ``salt-contrib``.  A travis config
is also included which will run the contrib tests if you enable it.

::

  $ git clone git://github.com/saltstack/salt.git
  $ git clone git@github.com:<me>/salt-contrib.git

  $ salt-contrib/link_contrib.py salt

  $ salt/tests/runtests.py -n contrib.tests -v

You can also link against a state folder so the modules are pushed out to clients via
``_modules``, ``_states`` etc

::

  $ salt-contrib/link_contrib.py /srv/salt
