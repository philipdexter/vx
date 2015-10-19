import vx
import argparse

parser = argparse.ArgumentParser(description='ldit files')
parser.add_argument('files', metavar='FILE', type=str, nargs='*',
                    help='Files to edit')
parser.add_argument('-l', '--log', dest='log', action='store_true',
                    help='Log to \'log\' file')

vx.parsed_args = parser.parse_args()

vx.files = vx.parsed_args.files
