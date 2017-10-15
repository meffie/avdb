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

"""AFS version database cli"""

import sys
import argparse

root = argparse.ArgumentParser(description="afs version database")
parent = root.add_subparsers(dest='subcommand')

def subcommand(*args):
    """Decorator to declare command line subcommands."""
    def decorator(function):
        name = function.__name__.strip('_')
        desc = function.__doc__
        parser = parent.add_parser(name, description=desc)
        if name not in ('help', 'version'):
            parser.add_argument("-v", "--verbose", help="print more messages")
            parser.add_argument("-q", "--quiet", help="print less messages")
        for arg in args:
            name_or_flags,options = arg
            parser.add_argument(*name_or_flags, **options)
        parser.set_defaults(function=function)
    return decorator

def argument(*name_or_flags, **options):
    """Helper to declare subcommand arguments."""
    # Pass the same args as the argparse add_arguments() method.
    return (name_or_flags, options)

@subcommand(
    argument("host", metavar="<host>", help="example postional option"),
    argument("--filename", "-f", help="example optional flag"),
    argument("--output", default="example", help="example option"),
    )
def example(args):
    """example subcommand"""
    print "example"
    print args.host
    print args.filename
    print args.output
    return 0

@subcommand()
def help(args):
    """Display help message"""
    print """avdb [command] [options]

Scan public AFS servers and clients for version information and generate
reports.
"""
    print "commands:"
    for name,parser in parent.choices.items():
        print "  %-12s %s" % (name, parser.description)
    return 0

@subcommand()
def version(args):
    """Print the version number and exit"""
    print "version"
    return 0

@subcommand()
def init(args):
    """describe init here"""
    return 0

@subcommand()
def add(args):
    """describe add here"""
    return 0

@subcommand()
def remove(args):
    """describe remove here"""
    return 0

@subcommand()
def import_(args): #  Trailing underscore to avoid reserved name.
    """describe import here"""
    return 0

@subcommand()
def scan(args):
    """describe scan here"""
    return 0

@subcommand()
def report(args):
    """describe report here"""
    return 0

def main():
    args = root.parse_args()
    return args.function(args)

if __name__ == '__main__':
    sys.exit(main())
