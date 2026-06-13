\"\"\"object_storage_gateway CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('object_storage_gateway', help='Manage object_storage_gateway')
    parser.set_defaults(func=handle_object_storage_gateway)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_object_storage_gateway(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/object_storage_gateway')
    for item in data:
        print(f'{item}')
