"""

Other desireable things:
- walk through and bucket contacts with tab completion, and mkdirs if needed
- auto-bucket those with nothing more than a google profile and name
- drop craigslist addresses
- merge the item1.BLAH varients into the main fields when possible
    - seen TEL, ADR and URL there and not sure why


"""
import codecs
import collections
import logging
import os
import re
import sys

import vobject


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
    except UnicodeEncodeError:
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


def GetEmailUsername(email_addr, cleaner=CleanString):
    login = email_addr.split('@')[0]
    return cleaner(login)


def LikelyName(vcard, cleaner=CleanString):
    fname_pieces = []
    for name in ('family', 'given', 'additional'):
        val = getattr(vcard.n.value, name)
        if val and IsFileSystemCompatString(val):
            fname_pieces.append(cleaner(val.lower()))
    
    if not fname_pieces and 'email' in vcard.contents:
        fname_pieces.append(GetEmailUsername(vcard.email.value,
                                             cleaner=cleaner))

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
            logger.debug('{} -> {}'.format(filename, vcard))
            f.write(vcard.serialize())
    except OSError:
        logger.error('Error writing to file "{}", skipping.'.format(filename))
        return False
    return True


def MergeVcards(vcard1, vcard2):
    new_vcard = vobject.vCard()
    vcard1_fields = set(vcard1.contents.keys())
    vcard2_fields = set(vcard2.contents.keys())
    mutual_fields = vcard1_fields.intersection(vcard2_fields)
    for field in mutual_fields:
        val1 = getattr(vcard1, field).value
        val2 = getattr(vcard2, field).value
        if val1 != val2:
            # we have a conflict, if a list maybe append otherwise prompt user
        else:
            new_val = val1
        new_field = new_vcard.add(field) 
        new_field.value = new_val

    for field in vcard1_fields.difference(vcard2_fields):
        val = getattr(vcard1, field).value
        new_field = new_vcard.add(field)
        new_field.value = val

    for field in vcard2_fields.difference(vcard1_fields):
        val = getattr(vcard2, field).value
        new_field = new_vcard.add(field)
        new_field.value = val

    return new_vcard


def main(argv):
    with codecs.open(argv[1], 'r', encoding='utf-8') as f:
        content = f.read()

    new_files = collections.defaultdict(list)
    for vcard in GetVcardsFromString(content):
        try:
            fname = LikelyName(vcard)
            logger.debug('{:30}'.format(fname))
        except NameError as e:
            logger.warning('SKIPPING: Could not determine name for {}'.format(
                str(vcard))
            )
            continue
        new_files[fname].append(vcard)

    new_vcards = DedupVcardFilenames(new_files)
    for k, v in new_vcards.items():
        WriteVcard(k, v[0])


if __name__ == '__main__':
    main(sys.argv) 
