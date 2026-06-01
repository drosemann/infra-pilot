\"\"\"file_sharing CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('file_sharing', help='Manage file_sharing')
    parser.set_defaults(func=handle_file_sharing)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_file_sharing(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/file_sharing')
    for item in data:
        print(f'{item}')
