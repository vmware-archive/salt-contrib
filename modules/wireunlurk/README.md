==========
wireunlurk
==========

Python script and Salt execution module to detect and remove WireLurker.
Based on WireLurkerDectectorOSX.py by Claud Xiao, Palo Alto Networks and the
bash-based WireLurker cleaner 'killer.sh' by wxzjohn.

https://github.com/PaloAltoNetworks-BD/WireLurkerDetector
https://github.com/wzxjohn/WireLurkerDetector

Usage:

    From the command line:

```
        wireunlurk.py [-c] [-h]
          -h: Show help

          -c: Clean as well as detect.  Cleaning will move infected files to
              a dynamically determined temporary directory.  Cleaned machines
              should be rebooted after disinfection.
```
    From Salt:
        
        Drop this file in your master's /srv/salt/_modules directory
        or equivalent and execute a `salt '*' modules.sync_modules`

        then

        General target:
```
        salt //target// wireunlurk.scan [clean=True]
```
        Grains based OS match:
```
        salt -G 'os:MacOS' wireunlurk.scan [clean=True]
```



License:

Copyright (c) 2014, SaltStack, Inc.
Copyright (c) 2014, Palo Alto Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted, provided that the above copyright notice
and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
