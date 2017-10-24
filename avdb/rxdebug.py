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

"""AFS version database"""

from sh import rxdebug
import logging

log = logging.getLogger(__name__)

def get_version(host, port):
    """Get the version string from the remote host."""
    version = None
    prefix = "AFS version:"
    try:
        output = rxdebug(host, port, '-version')
        for line in output.stdout.splitlines():
            if line.startswith(prefix):
                version = line.replace(prefix, "").strip()
                break
    except:
        log.warn("Unable to reach host %s:%d", host, port)
    return version

# Example
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print get_version('207.89.43.108', 7003)  # afsdb3
    print get_version('207.89.43.100', 7003)  # bogus
