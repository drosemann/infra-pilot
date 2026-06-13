\"\"\"crossplay_proxy CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('crossplay_proxy', help='Manage crossplay_proxy')
    parser.set_defaults(func=handle_crossplay_proxy)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_crossplay_proxy(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/crossplay_proxy')
    for item in data:
        print(f'{item}')
