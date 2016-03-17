#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Other desireable things:
- walk through and bucket contacts with tab completion, and mkdirs if needed
- auto-bucket those with nothing more than a google profile and name
- drop craigslist addresses
- merge the item1.BLAH varients into the main fields when possible
    - seen TEL, ADR and URL there and not sure why

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import argparse
import codecs
import collections
import logging
import os
import re
import sys

import vobject
from six import u


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(('%(asctime)s - %(name)s - %(levelname)s'
                                   ' - %(message)s'))
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


VCARD_REGEX=r'^BEGIN:VCARD.*?END:VCARD'


class NameError(Exception):
    pass


def GetVcardsFromString(content):
    match = re.findall(VCARD_REGEX, content, re.M | re.S)
    for card in match:
        yield vobject.readOne(card)


def IsNotGplusOnly(vcard):
    gplus_only_fields = ('fn', 'n', 'url', 'version')
    card_keys = set(vcard.contents.keys())
    return card_keys.difference(gplus_only_fields)


def IsFileSystemCompatString(input_str, encoding='latin-1'):
    """Returns strings that can be read in the desired encoding or ''.

    Motivation: Even though filesystems frequently can support utf-8 file
    names today it can still pose an issue for people who lack the needed
    keys on their keyboards.  As such making sure filenames are written in
    a format people can easily manipulate them in is important -- even though
    the content may very well be utf-8.
    """
    try:
        input_str.encode(encoding)
    except (UnicodeDecodeError, UnicodeEncodeError):
        return ''
    return input_str


def CleanString(s):
    """Cleans up string.

    Doesn't catch everything, appears to sometimes allow double underscores
    to occur as a result of replacements.
    """
    punc = (' ', '-', '\'', '.', '&amp;', '&', '+', '@')
    pieces = []
    for part in s.split():
        part = part.strip()
        for p in punc:
            part = part.replace(p, '_')
        part = part.strip('_')
        part = part.lower()
        pieces.append(part)
    return '_'.join(pieces)


def GetEmailUsername(email_addr):
    login = email_addr.split('@')[0]
    return CleanString(login)


def GetVcardFilename(vcard, filename_charset='latin-1'):
    fname_pieces = []
    for name in ('family', 'given', 'additional'):
        val = getattr(vcard.n.value, name)
        if val and IsFileSystemCompatString(val, encoding=filename_charset):
            fname_pieces.append(CleanString(val.lower()))
    
    if not fname_pieces and 'email' in vcard.contents:
        fname_pieces.append(GetEmailUsername(vcard.email.value))

    if not fname_pieces:
        raise NameError('{} HAS NO POSSIBLE FILENAME!'.format(str(vcard)))
    return '{}.vcf'.format('_'.join(fname_pieces))


def DedupVcardFilenames(vcard_dict):
    """Make sure every vCard in the dictionary has a unique filename."""
    remove_keys = []
    add_pairs = []
    for k, v in vcard_dict.items():
        if not len(v) > 1:
            continue
        for idx, vcard in enumerate(v):
            fname, ext = os.path.splitext(k)
            fname = '{}-{}'.format(fname, idx + 1)
            fname = fname + ext
            assert fname not in vcard_dict
            add_pairs.append((fname, vcard))
        remove_keys.append(k)

    for k, v in add_pairs:
        vcard_dict[k].append(v)

    for k in remove_keys:
        vcard_dict.pop(k)

    return vcard_dict


def WriteVcard(filename, vcard, fopen=codecs.open):
    """Writes a vCard into the given filename."""
    if os.access(filename, os.F_OK):
        logger.warning('File exists at "{}", skipping.'.format(filename))
        return False
    try:
        with fopen(filename, 'w', encoding='utf-8') as f:
            logger.debug('Writing {}:\n{}'.format(filename, u(vcard.serialize())))
            f.write(u(vcard.serialize()))
    except OSError:
        logger.error('Error writing to file "{}", skipping.'.format(filename))
        return False
    return True


def AddArguments(parser):
    parser.add_argument('vcard_file',
                        nargs=1,
                        help='A multi-entry vCard to split.')
    parser.add_argument('--pretend',
                        action='store_true',
                        help='Print summary but do not write files')
    parser.add_argument('--filename_charset',
                        choices=['utf-8', 'latin-1'],
                        default='latin-1',
                        help='Restrict filenames to character set')
    parser.add_argument('--output_dir',
                        nargs=1,
                        help='Write output files in provided directory')


def main(args):
    with codecs.open(args.vcard_file[0], 'r', encoding='utf-8') as f:
        content = f.read()

    new_files = collections.defaultdict(list)
    for vcard in GetVcardsFromString(content):
        try:
            fname = GetVcardFilename(vcard,
                                     filename_charset=args.filename_charset)
            logger.debug('{}'.format(fname))
        except NameError as e:
            logger.warning('SKIPPING: Could not create filename for:\n{}'.format(
                u(vcard.serialize()))
            )
            continue
        new_files[fname].append(vcard)

    new_vcards = DedupVcardFilenames(new_files)
    if not args.pretend:
        for k, v in new_vcards.items():
            vcard_path = k
            if args.output_dir:
                output_dir = os.path.abspath(args.output_dir[0])
                if os.path.isdir(output_dir) and os.access(output_dir, os.W_OK):
                    vcard_path = os.path.join(output_dir, k)
                else:
                    logger.warning('--output_dir may not be a directory!')
                    logger.fatal('Cannot write to output directory.')
                    sys.exit(1)
            WriteVcard(vcard_path, v[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='vcf_splitter')
    AddArguments(parser)
    args = parser.parse_args(sys.argv[1:])
    main(args)
