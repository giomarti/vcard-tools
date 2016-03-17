#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import codecs
import logging
import pprint
import sys

import vobject
from six import u
from six.moves import input


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(('%(asctime)s - %(name)s - %(levelname)s'
                                   ' - %(message)s'))
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


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


def VcardMergeListFields(field1, field2):
    """Handle merging list fields that may include some overlap."""
    field_dict = {}
    for f in field1 + field2:
        field_dict[str(f)] = f
    return list(field_dict.values())


def SetVcardField(new_vcard, field_name, values):
    """Set vCard field values and parameters on a new vCard."""
    for val in values:
        new_field = new_vcard.add(field_name)
        new_field.value = val.value
        if val.params:
            new_field.params = val.params
    return new_vcard


def CopyVcardFields(new_vcard, auth_vcard, field_names):
    """Copy vCard field values from an authoritative vCard into a new one."""
    for field in field_names:
        value_list = auth_vcard.contents.get(field)
        new_vcard = SetVcardField(new_vcard, field, value_list)
    return new_vcard


def MergeVcards(vcard1, vcard2):
    """Create a new vCard and populate it."""
    new_vcard = vobject.vCard()
    vcard1_fields = set(vcard1.contents.keys())
    vcard2_fields = set(vcard2.contents.keys())
    mutual_fields = vcard1_fields.intersection(vcard2_fields)
    logger.debug('Potentially conflicting fields: {}'.format(mutual_fields))
    for field in mutual_fields:
        val1 = vcard1.contents.get(field)
        val2 = vcard2.contents.get(field)
        new_values = []
        if not VcardFieldsEqual(val1, val2):
            # we have a conflict, if a list maybe append otherwise prompt user
            if field not in MERGEABLE_FIELDS:
                context_str = GetVcardContextString(vcard1, vcard2)
                new_values.extend(SelectFieldPrompt(field,
                                                    context_str,
                                                    val1,
                                                    val2))
            else:
                new_values.extend(VcardMergeListFields(val1, val2))
        else:
            new_values.extend(val1)

        logger.debug('Merged values for field {}: {}'.format(
            field.upper(),
            u(str(new_values)))
        )
        new_vcard = SetVcardField(new_vcard, field, new_values)

    new_vcard = CopyVcardFields(new_vcard,
                                vcard1,
                                vcard1_fields - vcard2_fields)
    new_vcard = CopyVcardFields(new_vcard,
                                vcard2,
                                vcard2_fields - vcard1_fields)

    return new_vcard


def SelectFieldPrompt(field_name, context_str, *options):
    """Prompts user to pick from provided options.

    It is possible to provide a function as an option although it is
    not yet tested.  This could allow a user to be prompted to provide
    their own value rather than the listed options.

    Args:
      field_name (string): Name of the field.
      context_str (string): Printed to give the user context.
      options: Variable arguments, should be vobject Components
          in a list. As retrieved from a vCard.contents dictionary.

    Returns:
        One of the options passed in.  Ideally always a list.
    """
    option_format_str = '[ {} ] "{}"'
    option_dict = {}
    print(context_str)
    print('Please select one of the following options for field "{}"'.format(
        field_name)
    )
    for cnt, option in enumerate(options):
        option_dict['{}'.format(cnt + 1)] = option
        if not callable(option):
            print(option_format_str.format(cnt + 1, u(str(option))))
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
    logger.debug('Input vCard 1:\n{}'.format(u(vcard1.serialize())))
    logger.debug('Input vCard 2:\n{}'.format(u(vcard2.serialize())))
    context = 'Option 1:\n{}\n\nOption 2:\n{}\n\n'.format(
        pprint.pformat(u(str(vcard1.contents))),
        pprint.pformat(u(str(vcard2.contents)))
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
    logger.debug('First vCard:\n{}'.format(u(vcard1.serialize())))
    logger.debug('Second vCard:\n{}'.format(u(vcard2.serialize())))

    merged_vcard = MergeVcards(vcard1, vcard2)
    logger.debug('Merged vCard:\n{}'.format(u(merged_vcard.serialize())))
    args.outfile.write(u(merged_vcard.serialize()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='vcf_merge')
    AddArguments(parser)
    args = parser.parse_args(sys.argv[1:])
    main(args)
