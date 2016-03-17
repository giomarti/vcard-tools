#!/usr/bin/env python

import argparse
import sys

try:
    import vcf_merge
    import vcf_splitter
except:
    print(sys.path)
    raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='vcardtool')
    sub_parsers = parser.add_subparsers(help='sub-command help')

    parser_merge = sub_parsers.add_parser('merge', help='merge help')
    parser_merge.add_argument('vcard_files',
                              nargs=2,
                              help='Two vCard files to merge')
    parser_merge.add_argument('--outfile',
                              nargs='?',
                              type=argparse.FileType('w'),
                              default=sys.stdout,
                              help='Write merged vCard to file')
    parser_merge.set_defaults(func=vcf_merge.main)

    parser_split = sub_parsers.add_parser('split', help='split help')
    parser_split.add_argument('vcard_file',
                              nargs=1,
                              help='A multi-entry vCard to split.')
    parser_split.add_argument('--pretend',
                              action='store_true',
                              help='Print summary but do not write files')
    parser_split.add_argument('--filename_charset',
                              choices=['utf-8', 'latin-1'],
                              default='latin-1',
                              help='Restrict filenames to character set')
    parser_split.add_argument('--output_dir',
                              nargs=1,
                              help='Write output files in provided directory')
    parser_split.set_defaults(func=vcf_splitter.main)

    args = parser.parse_args(sys.argv[1:])
    args.func(args)
