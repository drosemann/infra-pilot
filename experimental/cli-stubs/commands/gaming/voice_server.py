\"\"\"voice_server CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('voice_server', help='Manage voice_server')
    parser.set_defaults(func=handle_voice_server)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_voice_server(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/voice_server')
    for item in data:
        print(f'{item}')
