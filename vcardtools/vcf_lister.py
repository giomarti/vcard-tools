#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Other desireable things:
- use a set of vcf files (like glob) instead of single file with multiple card
- manage other fields (right now only focus on email address and multiple email per VCARD)


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
logger.setLevel(logging.NOTSET)
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
    vl = []
    match = re.findall(VCARD_REGEX, content, re.M | re.S)
    for card in match:
        vl.append(vobject.readOne(card))
    return vl


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

#
# Plain email list, one address per line no way to 
#
def GetVcardEmail (vv):
    e_list = []

    try:
        vv.contents['email']
    except:
        #logger.warning('VCARD: Could not get email for:\n{}'.format(
        #        u(vv.serialize()))
        #    )
        return e_list
    
    for ee in vv.contents['email']:
        e_list.append(ee.value)

    return e_list

def GetVcardName (vcard):
    # fn is a mandatory field so we use it.
    return vcard.fn.value


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


def ListerDumpEmail (email_dict):

    for e,v in email_dict.items():
        print(e)
    return

lister_separator = ";"
def ListerDumpName (n_dict):

    for n,v in n_dict.items():
        to_print = n + lister_separator + " "
        for e in v:
            for ee in e:
                to_print += str(ee)
                to_print += " " 

        print(to_print)

    #print("\n\n")
    return


def AddArguments(parser):
    group = parser.add_mutually_exclusive_group()
    
    parser.add_argument('vcard_file',
                        nargs=1,
                        help='A multi-entry vCard to list.')
    group.add_argument('--email',
                        action='store_true',
                        help='list plain email addresses one per line')
    group.add_argument('--field',
                        choices=['fn'],
                        help='define fields to list, one line per vcard, with format \"<fields>; email-address*\"')
    group.add_argument('--raw',
                        action='store_true',
                        help='liste the serialization of vfc file')
    parser.add_argument('--filename_charset',
                        choices=['utf-8', 'latin-1'],
                        default='latin-1',
                        help='Restrict filenames to character set')


def main(args, usage=''):
    try:
        with codecs.open(args.vcard_file[0], 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, OSError):
        print('\nERROR: Check that all files specified exist and permissions'
              ' are OK.\n')
        print(usage)
        sys.exit(1)

    name_dict = collections.defaultdict(list)
    email_dict = collections.defaultdict(list)

    # first get the whole vcard dictionary, just save for futher processing
    vcard_list = GetVcardsFromString(content);

    # The raw printing much like the cat of vcf file
    if (args.raw):
        print("\nNumber of Vcards: " + str(len(vcard_list)) + "\n")
        for idx in range(len(vcard_list)):
            print("###" + str(idx) + "###" +vcard_list[idx].serialize())
        return 
    
    for vcard in vcard_list: 
        #print("==1==>")
        #print (vcard.serialize())
        #print("<==1==")
        
        email = GetVcardEmail(vcard)
        logger.debug('{}'.format(str(email)))

        for e in email:
            email_dict[e].append(vcard)

        name = GetVcardName(vcard)
        name_dict[name].append(email)

 
    if (args.email):
        ListerDumpEmail(email_dict)
        return
    
    if (args.field == 'fn'):
        ListerDumpName(name_dict)
        return

    ## END of processing with no options
    print ("Statistics for ", args.vcard_file[0], ":")
    print ("  Number of Vcards:", len(name_dict))
    print ("  Number of emails:", len(email_dict))
    print ()
    return

def dispatch_main():
    parser = argparse.ArgumentParser(prog='vcf_lister')
    AddArguments(parser)
    args = parser.parse_args(sys.argv[1:])
    main(args, usage=parser.format_usage())


if __name__ == '__main__':
    dispatch_main()
