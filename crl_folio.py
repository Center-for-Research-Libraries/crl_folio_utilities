#!/usr/bin/python3
#*- coding: utf-8 -*-
import argparse
import pymarc
from utilities.crl_folio_utilities import *


def parse_command_line_args():
    parser = argparse.ArgumentParser(description='Access Folio api.')
    parser.add_argument('--getmarc', '--get_marc', action='store_true', dest='get_marc', help='Gets marc record')
    parser.add_argument('--getmarcall', '--get_marc_all', action='store_true', dest='get_marc_all', help='Gets marc record')
    parser.add_argument('--outputfolder', '--output_folder', action='store', dest='output_folder', nargs=1, help='Output folder location')
    parser.add_argument('--marcfile', '--marc_file', action='store', dest='marc_file', nargs=1, help='Marc file name')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_command_line_args()
    if args.get_marc or args.get_marc_all:
        output_folder = os.path.dirname(os.path.realpath('__file__'))
        if args.output_folder is not None:
            output_folder = args.output_folder
        marc_file = 'marc_file.mrk'
        if args.marc_file is not None:
            marc_file = args.marc_file + '.mrk'
        marc_file = open(os.path.join(output_folder, marc_file), 'wt', encoding='utf8')
        marc_writer = pymarc.TextWriter(marc_file)
        if args.get_marc:
            marc_writer.write(get_marc(get_uuid_from_user()))
        elif args.get_marc_all:
            for record in get_marc_records_all():
                marc_writer.write(record)
