\"\"\"game_server_stats CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('game_server_stats', help='Manage game_server_stats')
    parser.set_defaults(func=handle_game_server_stats)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_game_server_stats(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/game_server_stats')
    for item in data:
        print(f'{item}')
