# Copyright (c) 2017 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#------------------------------------------------------------------------------

"""AFS CellServDB parser"""

import re
import urllib2
from collections import OrderedDict
from pprint import pformat

def readfile(path):
    """Read a CellServDB file from a url or local path."""
    if path.startswith('https://') or path.startswith('http://'):
        response = urllib2.urlopen(path)
        text = response.read()
    else:
        if path.startswith('file://'):
            path = path.replace('file://', '')
        with open(path, 'r') as f:
            text = f.read()
    return text

def parse(text):
    """Parse CellServDB text into a dictionary.

    cells = csdb.parse(csdb.readfile('/tmp/CellServDB'))
    pprint(cells.items())
    [('sinenomine.net',
      {'desc': 'Cell name',
       'hosts': [('207.89.43.108', 'afsdb3.sinenomine.net'),
                 ('207.89.43.109', 'afsdb4.sinenomine.net'),
                 ('207.89.43.110', 'afsdb5.sinenomine.net')]})]
    """
    cells = OrderedDict()
    name = None
    desc = ''
    hosts = []
    for line in text.splitlines():
        m = re.match('\S*$', line)
        if m:
            continue # skip blanks
        m = re.match('>(\S+)\s+#(.*)\s*$', line)
        if m:
            if name:
                cells[name] = {'desc':desc, 'hosts':hosts}
            name = m.group(1)
            desc = pformat(m.group(2)).strip("'") # Flatten descriptions to ascii.
            hosts = []
            continue # start of entry
        m = re.match('(\d+\.\d+\.\d+\.\d+)\s+#(.*)\s*$', line)
        if m:
            hostaddr = m.group(1)
            hostname = m.group(2)
            hosts.append((hostaddr, hostname))
    if name:
        cells[name] = {'desc':desc, 'hosts':hosts}
    return cells
