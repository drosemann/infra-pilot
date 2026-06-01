\"\"\"server_rental CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('server_rental', help='Manage server_rental')
    parser.set_defaults(func=handle_server_rental)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_server_rental(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/server_rental')
    for item in data:
        print(f'{item}')
