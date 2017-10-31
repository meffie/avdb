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

"""Create command line subcommands with argparse

This module provides a thin wrapper over the standard argparse package
to cleanly create command line subcommands. A decorator turns regular functions
into cli subcommands. The argument function defines command line options.

Example:

    @subcommand(
        argument("host", metavar="<host>", help="example postional option"),
        argument("--filename", "-f", help="example optional flag"),
        argument("--output", default="example", help="example option"),
        )
    def example(args):
        'example subcommand'
        print("example")
        print(args.host)
        print(args.filename)
        print(args.output)
        return 0

    dispatch()
    # usage: cli example [options]

# Note: Put trailing underscores on function names to create subcommands
#       which are Python reserved words, such as 'import'.

"""

from __future__ import print_function
import argparse, logging, os
try:
    from configparser import ConfigParser # python3
except ImportError:
    from ConfigParser import ConfigParser # python2

root = argparse.ArgumentParser()
parent = root.add_subparsers(dest='subcommand')
config = ConfigParser()
config.read(['/etc/avdb.ini', os.path.expanduser('~/.avdb.ini')])
URL = 'sqlite:///{}'.format(os.path.expanduser('~/avdb.db'))

def _long_opt(name_or_flags):
    for opt in name_or_flags:
        if opt.startswith('--'):
            return opt.lstrip('--')
    return None

def _get_config(section, option, default):
    if config.has_option(section, option):
        return config.get(section, option)
    else:
        return default

def subcommand(*args):
    """Decorator to declare command line subcommands."""
    def decorator(function):
        name = function.__name__.strip('_')
        desc = function.__doc__
        parser = parent.add_parser(name, description=desc)
        if name not in ('help', 'version'):
            url = _get_config('global', 'url', URL)
            log = _get_config('global', 'log', '-')
            parser.add_argument("-v", "--verbose", action='store_true', help="print more messages")
            parser.add_argument("-q", "--quiet", action='store_true', help="print less messages")
            parser.add_argument("--url", default=url, help="sql connection url")
            parser.add_argument("--log", default=log, help="log file (default: {})".format(log))
        for arg in args:
            name_or_flags,options = arg
            if 'default' in options:
                opt = _long_opt(name_or_flags)
                if opt:
                    options['default'] = _get_config(name, opt, options['default'])
                if 'help' in options:
                    options['help'] += " (default: {})".format(options['default'])
            parser.add_argument(*name_or_flags, **options)
        parser.set_defaults(function=function)
    return decorator

def argument(*name_or_flags, **options):
    """Helper to declare subcommand arguments."""
    return (name_or_flags, options)

def usage(msg):
    """Print a summary of the subcommands."""
    print("{msg}\ncommands:".format(msg=msg))
    for name,parser in parent.choices.items():
        print("  {name:12} {desc}".format(name=name, desc=parser.description))
    return 0

def dispatch():
    """Parse arguments and dispatch subcommand."""
    args = root.parse_args()
    verbose = getattr(args, 'verbose', False)
    quiet = getattr(args, 'quiet', False)
    log = getattr(args, 'log', '-')
    if verbose and quiet:
        root.error("Options --verbose and --quiet are exclusive")
    logopts = {}
    if quiet:
        logopts['level'] = logging.ERROR
    elif verbose:
        logopts['level'] = logging.INFO
    else:
        logopts['level'] = logging.WARNING
    if log != '-':
        logopts['filename'] = log
    logging.basicConfig(**logopts)
    return args.function(args)
