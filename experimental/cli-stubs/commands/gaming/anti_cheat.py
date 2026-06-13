\"\"\"anti_cheat CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('anti_cheat', help='Manage anti_cheat')
    parser.set_defaults(func=handle_anti_cheat)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_anti_cheat(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/anti_cheat')
    for item in data:
        print(f'{item}')
