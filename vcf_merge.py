#!/usr/bin/env python

import argparse
import codecs
import pprint
import sys

import vobject


MERGEABLE_FIELDS = ('email', 'tel', 'adr', 'org', 'categories')


def VcardFieldsEqual(field1, field2):
    """Handle comparing vCard fields where inputs are lists of components.

    Handle parameters?  Are any used aside from 'TYPE'?
    Note: force cast to string to compare sub-objects like Name and Address
    """
    field1_vals = set([ str(f.value) for f in field1 ])
    field2_vals = set([ str(f.value) for f in field2 ])
    if field1_vals == field2_vals:
        return True
    else:
        return False


def VcardMergeFields(field1, field2):
    """Handle merging list fields that may include some overlap."""
    field_dict = {}
    for f in field1 + field2:
        field_dict[str(f)] = f
    return list(field_dict.values())


def MergeVcards(vcard1, vcard2):
    new_vcard = vobject.vCard()
    vcard1_fields = set(vcard1.contents.keys())
    vcard2_fields = set(vcard2.contents.keys())
    mutual_fields = vcard1_fields.intersection(vcard2_fields)
    for field in mutual_fields:
        val1 = vcard1.contents.get(field)
        val2 = vcard2.contents.get(field)
        if not VcardFieldsEqual(val1, val2):
            # we have a conflict, if a list maybe append otherwise prompt user
            if field not in MERGEABLE_FIELDS:
                context_str = GetVcardContextString(vcard1, vcard2)
                new_val = SelectFieldPrompt(field, context_str, val1, val2)
            else:
                new_val = VcardMergeFields(val1, val2)
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


def SelectFieldPrompt(field_name, context_str, *options):
    option_format_str = '[ {} ] "{}"'
    option_dict = {}
    print(context_str)
    print('Please select one of the following options for field "{}"'.format(
        field_name)
    )
    for cnt, option in enumerate(options):
        option_dict['{}'.format(cnt + 1)] = option
        if not callable(option):
            print(option_format_str.format(cnt + 1, option))
        else:
            print(option_format_str.format(cnt + 1, option.__name__))
    choice = None
    while choice not in option_dict:
        choice = input('option> ').strip()
    new_value = option_dict[choice]
    if callable(new_value):
        return new_value()
    else:
        return new_value


def GetVcardContextString(vcard1, vcard2):
    context = 'Option 1:\n{}\n\nOption 2:\n{}\n\n'.format(
        pprint.pformat(vcard1.contents),
        pprint.pformat(vcard2.contents)
    )
    return context


def AddArguments(parser):
    parser.add_argument('vcard_files',
                        nargs=2,
                        help='Two vCard files to merge')
    parser.add_argument('--outfile',
                        nargs='?',
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Write merged vCard to file')


def main(args):
    with codecs.open(args.vcard_files[0], 'r', encoding='utf-8') as f:
        vcard1_raw = f.read()

    with codecs.open(args.vcard_files[1], 'r', encoding='utf-8') as f:
        vcard2_raw = f.read()

    vcard1 = vobject.readOne(vcard1_raw)
    vcard2 = vobject.readOne(vcard2_raw)

    logger.debug(vcard1)
    logger.debug(vcard2)
    args.outfile.write(MergeVcards(vcard1, vcard2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='vcf_merge')
    AddArguments(parser)
    args = parser.parse_args(sys.argv[1:])
    main(args)
