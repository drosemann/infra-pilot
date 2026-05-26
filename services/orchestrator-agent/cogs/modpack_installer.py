import asyncio
import logging
import json
import os
import tempfile
import zipfile
import shutil
import re
from typing import Optional

import aiohttp
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ModpackInstaller(commands.Cog):
    """One-click modpack installation for Minecraft servers."""

    def __init__(self, bot):
        self.bot = bot
        self.cache_file = 'data/modpack_cache.json'
        self._ensure_data_dir()
        self._load_cache()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file) as f:
                self.cache = json.load(f)
        else:
            self.cache = {'modpacks': [], 'last_updated': ''}

    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    async def search_modpacks(self, query: str, platform: str = 'all', limit: int = 10) -> list:
        results = []

        async with aiohttp.ClientSession() as session:
            if platform in ('all', 'modrinth'):
                try:
                    async with session.get(
                        'https://api.modrinth.com/v2/search',
                        params={'query': query, 'limit': limit, 'facets': '[[\"project_type:modpack\"]]'}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for hit in data.get('hits', []):
                                results.append({
                                    'id': f'modrinth:{hit["project_id"]}',
                                    'name': hit['title'],
                                    'platform': 'modrinth',
                                    'summary': hit.get('description', ''),
                                    'downloads': hit.get('downloads', 0),
                                    'iconUrl': hit.get('icon_url', ''),
                                    'minecraftVersions': hit.get('versions', []),
                                    'loaders': hit.get('categories', []),
                                    'url': f'https://modrinth.com/modpack/{hit["slug"]}',
                                })
                except Exception as e:
                    logger.error(f'Modrinth search error: {e}')

            if platform in ('all', 'curseforge'):
                api_key = os.getenv('CURSEFORGE_API_KEY', '')
                if api_key:
                    try:
                        async with session.get(
                            'https://api.curseforge.com/v1/mods/search',
                            params={'gameId': 432, 'slug': query, 'pageSize': limit},
                            headers={'x-api-key': api_key}
                        ) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                for mod in data.get('data', []):
                                    if mod.get('classId') == 4471:
                                        latest = mod.get('latestFiles', [{}])[0] if mod.get('latestFiles') else {}
                                        results.append({
                                            'id': f'curseforge:{mod["id"]}',
                                            'name': mod['name'],
                                            'platform': 'curseforge',
                                            'summary': mod.get('summary', ''),
                                            'downloads': mod.get('downloadCount', 0),
                                            'iconUrl': mod.get('logo', {}).get('url', ''),
                                            'minecraftVersions': [latest.get('gameVersion', '')] if latest else [],
                                            'loaders': latest.get('modLoaders', []) if latest else [],
                                            'url': mod.get('links', {}).get('websiteUrl', ''),
                                        })
                    except Exception as e:
                        logger.error(f'CurseForge search error: {e}')

        results.sort(key=lambda r: r['downloads'], reverse=True)
        return results[:limit]

    async def install_modpack(self, container_id: str, modpack_id: str, platform: str) -> dict:
        try:
            download_url = None
            server_dir = '/data'

            async with aiohttp.ClientSession() as session:
                if platform == 'modrinth':
                    project_id = modpack_id.split(':')[1]
                    async with session.get(
                        f'https://api.modrinth.com/v2/project/{project_id}/version'
                    ) as resp:
                        if resp.status == 200:
                            versions = await resp.json()
                            if versions:
                                version = versions[0]
                                for file in version.get('files', []):
                                    if file.get('primary', False):
                                        download_url = file['url']
                                        break

                elif platform == 'curseforge':
                    file_id = modpack_id.split(':')[1]
                    async with session.get(
                        f'https://api.curseforge.com/v1/mods/{file_id}/files',
                        headers={'x-api-key': os.getenv('CURSEFORGE_API_KEY', '')}
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('data'):
                                latest_file = data['data'][0]
                                download_url = latest_file.get('downloadUrl', '')

            if not download_url:
                return {'success': False, 'error': 'Could not find download URL'}

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as resp:
                    if resp.status != 200:
                        return {'success': False, 'error': f'Download failed: {resp.status}'}
                    zip_data = await resp.read()

            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp.write(zip_data)
                tmp_path = tmp.name

            try:
                extract_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(tmp_path, 'r') as zf:
                    zf.extractall(extract_dir)

                import subprocess
                subprocess.run(
                    ['docker', 'exec', container_id, 'mkdir', '-p', f'{server_dir}/mods'],
                    capture_output=True, timeout=30
                )

                mods_dir = os.path.join(extract_dir, 'mods')
                if os.path.exists(mods_dir):
                    for mod_file in os.listdir(mods_dir):
                        if mod_file.endswith('.jar'):
                            local_path = os.path.join(mods_dir, mod_file)
                            subprocess.run(
                                ['docker', 'cp', local_path, f'{container_id}:{server_dir}/mods/'],
                                capture_output=True, timeout=60
                            )

                config_dir = os.path.join(extract_dir, 'config')
                if os.path.exists(config_dir):
                    subprocess.run(
                        ['docker', 'exec', container_id, 'mkdir', '-p', f'{server_dir}/config'],
                        capture_output=True, timeout=30
                    )
                    for config_file in os.listdir(config_dir):
                        local_path = os.path.join(config_dir, config_file)
                        subprocess.run(
                            ['docker', 'cp', local_path, f'{container_id}:{server_dir}/config/'],
                            capture_output=True, timeout=60
                        )

                overrides_dir = os.path.join(extract_dir, 'overrides')
                if os.path.exists(overrides_dir):
                    for item in os.listdir(overrides_dir):
                        local_path = os.path.join(overrides_dir, item)
                        subprocess.run(
                            ['docker', 'cp', local_path, f'{container_id}:{server_dir}/'],
                            capture_output=True, timeout=60
                        )

                shutil.rmtree(extract_dir)

                return {
                    'success': True,
                    'message': 'Modpack installed successfully! Restart the server to apply changes.',
                }

            finally:
                os.unlink(tmp_path)

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Operation timed out'}
        except Exception as e:
            logger.error(f'Modpack installation error: {e}')
            return {'success': False, 'error': str(e)}

    @commands.group(name='modpack')
    async def modpack_group(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Subcommands: search, install, list')

    @modpack_group.command(name='search')
    async def modpack_search(self, ctx, query: str, platform: str = 'all'):
        await ctx.defer()
        results = await self.search_modpacks(query, platform, 5)

        if not results:
            await ctx.send(f'No modpacks found for "{query}".')
            return

        embed = discord.Embed(
            title=f'Modpacks: "{query}"',
            color=discord.Color.purple()
        )
        for r in results:
            loader_str = ', '.join(r['loaders'][:3]) if r['loaders'] else 'Unknown'
            mc_ver = r['minecraftVersions'][0] if r['minecraftVersions'] else '?'
            embed.add_field(
                name=f"{r['name']} ({r['platform']})",
                value=f"Down. {r['downloads']:,} | {mc_ver} | {loader_str}\n`ID: {r['id']}`",
                inline=False
            )
        await ctx.send(embed=embed)

    @modpack_group.command(name='install')
    async def modpack_install(self, ctx, modpack_id: str, container_id: str):
        await ctx.defer()

        platform = modpack_id.split(':')[0]
        result = await self.install_modpack(container_id, modpack_id, platform)

        if result['success']:
            await ctx.send(f'Done! {result["message"]}')
        else:
            await ctx.send(f'Installation failed: {result["error"]}')


async def setup(bot):
    await bot.add_cog(ModpackInstaller(bot))
