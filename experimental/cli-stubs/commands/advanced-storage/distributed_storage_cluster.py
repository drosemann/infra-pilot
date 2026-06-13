\"\"\"distributed_storage_cluster CLI command.\"\"\"
import argparse
from typing import Any, Dict
from ..client import ApiClient

def add_subparser(subparsers) -> None:
    parser = subparsers.add_parser('distributed_storage_cluster', help='Manage distributed_storage_cluster')
    parser.set_defaults(func=handle_distributed_storage_cluster)
    parser.add_argument('--action', choices=['list', 'show', 'create', 'delete'], default='list')
    parser.add_argument('--id', help='Resource ID')

async def handle_distributed_storage_cluster(args: argparse.Namespace, client: ApiClient) -> None:
    data = await client.get(f'/api/distributed_storage_cluster')
    for item in data:
        print(f'{item}')
