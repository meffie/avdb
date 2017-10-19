
from sh import rxdebug
import logging

log = logging.getLogger(__name__)

def version(host, port):
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
        log.info("Unable to reach host %s:%d", host, port)
    return version

# Example
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    hosts = [
        '207.89.43.100',  # bogus
        '207.89.43.108',  # afsdb3.sinenomine.net
        '207.89.43.109',  # afsdb4.sinenomine.net
    ]
    ports = [7002, 7003, 7007]
    for host in hosts:
        for port in ports:
            print "%s:%d %s" % (host, port, version(host, port))

