\"\"\"matchmaking CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('matchmaking', help='Manage matchmaking')
    parser.set_defaults(func=handle_matchmaking)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_matchmaking(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/matchmaking')
    for item in data:
        print(f'{item}')
