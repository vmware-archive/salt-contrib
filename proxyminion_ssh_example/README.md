cmdshell.py
===========

Simple CLI to test the Salt Proxy Minion.

To test, setup an account on your machine, copy proxycmdshell to /usr/local/bin,
add it to /etc/shells, and set proxycmdshell as the test account's shell.

If you don't want to mess with your accounts you can setup an LXC container with
ssh installed and enabled, and add the test account there.

Ssh'ing to your machine as the test user should drop you into the shell.  Typing
'exit' or ^D should log you out.

