\"\"\"tournament_api CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('tournament_api', help='Manage tournament_api')
    parser.set_defaults(func=handle_tournament_api)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_tournament_api(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/tournament_api')
    for item in data:
        print(f'{item}')
