\"\"\"dedup_compression CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('dedup_compression', help='Manage dedup_compression')
    parser.set_defaults(func=handle_dedup_compression)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_dedup_compression(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/dedup_compression')
    for item in data:
        print(f'{item}')
