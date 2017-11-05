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

import sys
import avdb
import logging
from bs4 import BeautifulSoup
from sh import cmdebug
try:
    from urllib.request import urlopen # python3
except ImportError:
    from urllib2 import urlopen # python2

def cfg(option):
    return avdb.subcmd.config.get('global', option)

def items(soup, id_):
    return [li.text.strip() for li in soup.find('div', id=id_).find_all('li')]

def main():
    level = logging.INFO if cfg('verbose') else logging.WARNING
    logging.basicConfig(filename=cfg('log'), level=level)
    log = logging.getLogger()

    avdb.model.init_db(cfg('url'))

    try:
        html = urlopen(sys.argv[1]).read()
    except IndexError:
        sys.stderr.write("usage: update <url>\n")
        return 1
    soup = BeautifulSoup(html, 'html.parser')
    for cellservdb in items(soup, 'cellservdbs'):
        log.info("importing celservdb %s", cellservdb)
        log.info("cellservdb %s", cellservdb)
    for client in items(soup, 'clients'):
        log.info("importing cmdebug %s -cellservdb", client)
        avdb.import_(cmdebug(client, cellservdb=True), '-')
    for cellname in items(soup, 'cellnames'):
        log.info("adding cellname %s", cellname)
        avdb.add_(cell=cellname)

    log.info("starting scan")
    avdb.scan_(nprocs=100)

    log.info("writing report")
    avdb.report_(format='html', output='/var/www/html/avdb/index.html')
    avdb.report_(format='csv', output='/var/www/html/avdb/avdb.csv')

main()
