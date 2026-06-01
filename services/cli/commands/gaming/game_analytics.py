\"\"\"game_analytics CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('game_analytics', help='Manage game_analytics')
    parser.set_defaults(func=handle_game_analytics)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_game_analytics(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/game_analytics')
    for item in data:
        print(f'{item}')
