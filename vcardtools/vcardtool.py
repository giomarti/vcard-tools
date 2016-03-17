#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys

try:
    import vcf_merge
    import vcf_splitter
except ImportError:
    print(sys.path)
    raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='vcardtool')
    sub_parsers = parser.add_subparsers(help='sub-command help')

    parser_merge = sub_parsers.add_parser('merge', help='merge help')
    vcf_merge.AddArguments(parser_merge)
    parser_merge.set_defaults(func=vcf_merge.main)

    parser_split = sub_parsers.add_parser('split', help='split help')
    vcf_splitter.AddArguments(parser_split)
    parser_split.set_defaults(func=vcf_splitter.main)

    args = parser.parse_args(sys.argv[1:])
    args.func(args)
