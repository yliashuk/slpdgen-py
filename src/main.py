import sys
import json
import argparse
import subprocess
from backends import dissector, python
from core.slpd import SlpdProto
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def create_arg_paser():
    parser = argparse.ArgumentParser(prog='dissectgen')
    
    parser.add_argument(
        'input', 
        type=str, 
        help='path to input file (supported: .json, .slpd)'
    )
    
    parser.add_argument(
        '--port', 
        nargs='?',
        const=-1,
        default=None,
        metavar="PORT",
        help='generate dissector with listening on port (0-65535)'
    )

    return parser

def create_parser():
    parser = argparse.ArgumentParser(prog='slpdgen-py', description='SLPD Code Generator')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- Command: dissector ---
    parser_dissector = subparsers.add_parser('dissector', help='Generate Wireshark dissector')
    parser_dissector.add_argument('input', type=str, help='Path to input file (.json, .slpd)')
    parser_dissector.add_argument('--port', type=int, default=None, help='Listen on port (0-65535)')

    # --- Command: py-proto ---
    parser_protocol = subparsers.add_parser('py-proto', help='Generate Python protocol class')
    parser_protocol.add_argument('input', type=str, help='Path to input file')

    return parser


if __name__ == '__main__':    
    args = create_parser().parse_args()
    
    path = Path(args.input)

    if path.suffix == '.slpd':
        subprocess.run(['slpdgen', '-json', path])
        path = Path.cwd() / path.with_suffix('.json').name

    with open(path) as f:
        proto = SlpdProto(json.load(f))

    if args.command == 'dissector':
        dissector.generate(proto, path.stem, args.port)

    if args.command == 'py-proto':
        python.generate(proto, path.stem)
