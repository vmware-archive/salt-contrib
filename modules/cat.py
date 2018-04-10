#!/usr/bin/env python
"""
This module allows Jinja to include lines one or more files into a Jinja template.

This module is created to work around Salt Issue #22063, "Wildcard inside top.sls
file for pillar".

You still cannot use wildcard in the pillar top.sls file itself, but you can create
a 'subtop' sls as such:

some-key:
{%- for ln in salt.cat.directory(subdir, recurse=True, file_filter=flt) %}
  {{ ln }}
{%- endfor %}

The drawback for this simplistic iterating over the lines of files, of course, is
that it does not have 'merging smarts'; so when using this, each included file
needs to have a unique top-level key.

This example will work:

  # a.sls
  key_a:
    - something
    - or
    - other

  # b.sls
  key_b:
    - more
    - things
    - here

But these will fail:

  # c.sls
  non_unique_key:
    - something
    - or
    - other

  # d.sls
  non_unique_key:
    - more
    - things
    - here


 (c) 2017, Pandu POLUAN <pepoluan@gmail.com>
 .
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
 .
     http://www.apache.org/licenses/LICENSE-2.0
 .
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

"""
from __future__ import print_function, unicode_literals

import os
import fnmatch


def file(name, indent=0):
    """
    Iterates over the lines of a file, stripping newlines, and optionally
    adding an indent.
    """
    ind = ' ' * indent
    with open(name, 'rt') as fin:
        for ln in fin:
            yield '{0}{1}'.format(ind, ln.rstrip('\r\n'))
    return


def directory(name, recurse=False, indent=0, file_filter='*', dir_filter='*'):
    """
    Find files that match :file_filter:, in directories that match :dir_filter:.
    Optionally also recurse and/or add indentation.
    """
    for root, dirs, files in os.walk(name):
        root_base = os.path.basename(root)
        if fnmatch.fnmatch(root_base, dir_filter):
            for fn in files:
                if fnmatch.fnmatch(fn, file_filter):
                    for ln in file(os.path.join(root, fn), indent=indent):
                        yield ln
        if not recurse:
            break
    return
