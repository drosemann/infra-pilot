import asyncio
import logging
import os
import json
import secrets
import string
from datetime import datetime
from typing import Optional

import docker
from discord.ext import commands

logger = logging.getLogger(__name__)

class DatabaseManager(commands.Cog):
    """On-demand MySQL/MariaDB database provisioning."""
    
    def __init__(self, bot):
        self.bot = bot
        self.docker_client = docker.from_env()
        self.databases_file = 'data/databases.json'
        self._ensure_data_dir()
        self._load_databases()
        self.mysql_root_password = os.getenv('MYSQL_ROOT_PASSWORD', secrets.token_hex(16))
    
    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)
    
    def _load_databases(self):
        if os.path.exists(self.databases_file):
            with open(self.databases_file) as f:
                self.databases = json.load(f)
        else:
            self.databases = []
    
    def _save_databases(self):
        with open(self.databases_file, 'w') as f:
            json.dump(self.databases, f, indent=2)
    
    def _generate_password(self, length=24):
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    async def create_database_container(self, db_name: str, user_id: str, 
                                       app_id: Optional[str] = None) -> dict:
        """Create a MySQL container and return connection details."""
        db_password = self._generate_password()
        container_name = f'mysql-{db_name}-{user_id[:8]}'
        
        try:
            try:
                existing = self.docker_client.containers.get(container_name)
                return {'error': f'Container {container_name} already exists'}
            except docker.errors.NotFound:
                pass
            
            container = self.docker_client.containers.run(
                image='mysql:8.0',
                name=container_name,
                environment={
                    'MYSQL_ROOT_PASSWORD': self.mysql_root_password,
                    'MYSQL_DATABASE': db_name,
                    'MYSQL_USER': db_name,
                    'MYSQL_PASSWORD': db_password,
                },
                ports={'3306/tcp': None},
                detach=True,
                restart_policy={'Name': 'always'},
                labels={
                    'managed_by': 'infra-pilot',
                    'db_name': db_name,
                    'user_id': user_id,
                }
            )
            
            await asyncio.sleep(5)
            
            container.reload()
            port = container.attrs['NetworkSettings']['Ports']['3306/tcp'][0]['HostPort']
            
            host_ip = os.getenv('HOST_IP', '127.0.0.1')
            
            db_info = {
                'id': f'db_{len(self.databases) + 1}',
                'name': db_name,
                'container_name': container_name,
                'container_id': container.id,
                'host': host_ip,
                'port': int(port),
                'database': db_name,
                'username': db_name,
                'password': db_password,
                'root_password': self.mysql_root_password,
                'user_id': user_id,
                'app_id': app_id,
                'status': 'running',
                'created_at': datetime.utcnow().isoformat(),
                'connection_string': f'mysql://{db_name}:{db_password}@{host_ip}:{port}/{db_name}',
            }
            
            self.databases.append(db_info)
            self._save_databases()
            
            return db_info
            
        except docker.errors.APIError as e:
            logger.error(f'Docker API error creating database: {e}')
            return {'error': str(e)}
        except Exception as e:
            logger.error(f'Error creating database: {e}')
            return {'error': str(e)}
    
    async def delete_database_container(self, db_id: str, user_id: str) -> bool:
        """Stop and remove a MySQL container."""
        for db in self.databases:
            if db['id'] == db_id and db['user_id'] == user_id:
                try:
                    container = self.docker_client.containers.get(db['container_id'])
                    container.stop(timeout=10)
                    container.remove()
                except docker.errors.NotFound:
                    pass
                
                self.databases.remove(db)
                self._save_databases()
                return True
        return False
    
    def get_user_databases(self, user_id: str) -> list:
        return [db for db in self.databases if db['user_id'] == user_id]
    
    def get_database(self, db_id: str) -> Optional[dict]:
        for db in self.databases:
            if db['id'] == db_id:
                return db
        return None
    
    @commands.group(name='database')
    async def database_group(self, ctx):
        """Database management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Subcommands: create, list, delete, info')
    
    @database_group.command(name='create')
    async def db_create(self, ctx, name: str, app_id: str = None):
        """Create a new MySQL database. Usage: /database create <name> [app_id]"""
        result = await self.create_database_container(name, str(ctx.author.id), app_id)
        
        if 'error' in result:
            await ctx.send(f'\u274c Failed to create database: {result["error"]}')
            return
        
        try:
            dm = await ctx.author.create_dm()
            await dm.send(f'**\u2705 Database Created: {name}**\n\n'
                         f'```\n'
                         f'Host: {result["host"]}\n'
                         f'Port: {result["port"]}\n'
                         f'Database: {result["database"]}\n'
                         f'Username: {result["username"]}\n'
                         f'Password: {result["password"]}\n'
                         f'Connection String: {result["connection_string"]}\n'
                         f'```\n'
                         f'\u26a0\ufe0f Save these credentials securely!')
            await ctx.send(f'\u2705 Database **{name}** created! Check your DMs for credentials.')
        except:
            await ctx.send(f'\u2705 Database **{name}** created! (Could not DM you the credentials)')
    
    @database_group.command(name='list')
    async def db_list(self, ctx):
        """List your databases."""
        databases = self.get_user_databases(str(ctx.author.id))
        if not databases:
            await ctx.send('No databases created yet.')
            return
        lines = ['**Your Databases:**']
        for db in databases:
            lines.append(f'\u2022 **{db["name"]}** \u2014 Port: {db["port"]} \u2014 Status: {db["status"]}')
        await ctx.send('\n'.join(lines))
    
    @database_group.command(name='delete')
    async def db_delete(self, ctx, db_id: str):
        """Delete a database. Usage: /database delete <db_id>"""
        success = await self.delete_database_container(db_id, str(ctx.author.id))
        if success:
            await ctx.send(f'\U0001f5d1\ufe0f Database deleted successfully.')
        else:
            await ctx.send(f'\u274c Database not found or access denied.')
    
    @database_group.command(name='info')
    async def db_info(self, ctx, db_id: str):
        """Get database connection info. Usage: /database info <db_id>"""
        db = self.get_database(db_id)
        if not db or db['user_id'] != str(ctx.author.id):
            await ctx.send('\u274c Database not found or access denied.')
            return
        
        try:
            dm = await ctx.author.create_dm()
            await dm.send(f'**Database: {db["name"]}**\n\n```\n'
                         f'Host: {db["host"]}\nPort: {db["port"]}\n'
                         f'Database: {db["database"]}\nUsername: {db["username"]}\n'
                         f'Password: {db["password"]}\n```')
            await ctx.send('\u2705 Database info sent via DM.')
        except:
            await ctx.send('\u274c Could not DM you. Please check your privacy settings.')


async def setup(bot):
    await bot.add_cog(DatabaseManager(bot))
