import asyncio
import logging
import os
import subprocess
import json
import tempfile
import shutil
from datetime import datetime
from typing import Optional

import aiohttp
from discord.ext import commands

logger = logging.getLogger(__name__)

class GitDeployer(commands.Cog):
    """Automated Git deployment via webhooks."""

    def __init__(self, bot):
        self.bot = bot
        self.deployments_file = 'data/git_deployments.json'
        self._ensure_data_dir()
        self._load_deployments()

    def _ensure_data_dir(self):
        os.makedirs('data', exist_ok=True)

    def _load_deployments(self):
        if os.path.exists(self.deployments_file):
            with open(self.deployments_file) as f:
                self.deployments = json.load(f)
        else:
            self.deployments = []

    def _save_deployments(self):
        with open(self.deployments_file, 'w') as f:
            json.dump(self.deployments, f, indent=2)

    async def handle_webhook(self, request):
        """Handle incoming GitHub webhook POST request."""
        data = await request.json()
        event = request.headers.get('X-GitHub-Event', '')

        if event == 'push':
            return await self._handle_push_event(data)
        elif event == 'ping':
            return aiohttp.web.Response(text='pong')
        return aiohttp.web.Response(status=400, text='Unsupported event')

    async def _handle_push_event(self, data):
        """Handle a GitHub push event."""
        repo_name = data.get('repository', {}).get('full_name', '')
        ref = data.get('ref', '')
        branch = ref.replace('refs/heads/', '')
        commits = data.get('commits', [])

        matched = [d for d in self.deployments
                   if d['repo'] == repo_name
                   and d['branch'] == branch
                   and d['enabled']]

        results = []
        for deployment in matched:
            result = await self._execute_deployment(deployment, commits)
            results.append(result)

        return aiohttp.web.json_response({'deployments': results})

    async def _execute_deployment(self, deployment: dict, commits: list) -> dict:
        """Execute a deployment: git pull, install, restart."""
        deploy_id = deployment['id']
        container_id = deployment.get('container_id', '')
        repo_url = deployment.get('repo_url', '')
        target_dir = deployment.get('target_dir', '/app')
        install_command = deployment.get('install_command', '')
        restart_command = deployment.get('restart_command', '')

        try:
            pull_cmd = ['docker', 'exec', container_id, 'bash', '-c',
                       f'cd {target_dir} && git pull origin {deployment["branch"]}']
            pull_result = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=120)

            if pull_result.returncode != 0:
                clone_cmd = ['docker', 'exec', container_id, 'bash', '-c',
                            f'cd {os.path.dirname(target_dir)} && git clone {repo_url} {os.path.basename(target_dir)}']
                subprocess.run(clone_cmd, capture_output=True, text=True, timeout=120)

            if install_command:
                install_cmd = ['docker', 'exec', container_id, 'bash', '-c',
                              f'cd {target_dir} && {install_command}']
                subprocess.run(install_cmd, capture_output=True, text=True, timeout=300)

            if restart_command:
                restart_cmd = ['docker', 'exec', container_id, 'bash', '-c', restart_command]
                subprocess.run(restart_cmd, capture_output=True, text=True, timeout=30)

            result = {
                'deployment_id': deploy_id,
                'status': 'success',
                'commits': len(commits),
                'timestamp': datetime.utcnow().isoformat()
            }

        except subprocess.TimeoutExpired:
            result = {'deployment_id': deploy_id, 'status': 'timeout', 'timestamp': datetime.utcnow().isoformat()}
        except Exception as e:
            result = {'deployment_id': deploy_id, 'status': 'failed', 'error': str(e), 'timestamp': datetime.utcnow().isoformat()}

        deployment.setdefault('history', []).append(result)
        self._save_deployments()

        return result

    @commands.group(name='deploy')
    async def deploy_group(self, ctx):
        """Git deployment management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send('Subcommands: create, list, delete, toggle, logs')

    @deploy_group.command(name='create')
    async def deploy_create(self, ctx, name: str, repo_url: str, branch: str = 'main',
                           container_id: str = None, target_dir: str = '/app'):
        """Register a new deployment configuration."""
        deployment = {
            'id': f'dep_{len(self.deployments) + 1}',
            'name': name,
            'repo_url': repo_url,
            'repo': '/'.join(repo_url.rstrip('.git').split('/')[-2:]),
            'branch': branch,
            'container_id': container_id,
            'target_dir': target_dir,
            'install_command': '',
            'restart_command': '',
            'enabled': True,
            'webhook_secret': os.urandom(20).hex(),
            'created_at': datetime.utcnow().isoformat(),
            'history': []
        }
        self.deployments.append(deployment)
        self._save_deployments()
        await ctx.send(f'✅ Deployment **{name}** created!\nWebhook URL: `http://your-host:8000/webhook/github/{deployment["id"]}`\nSecret: `{deployment["webhook_secret"]}`')

    @deploy_group.command(name='list')
    async def deploy_list(self, ctx):
        """List all deployments."""
        if not self.deployments:
            await ctx.send('No deployments configured.')
            return
        lines = ['**Git Deployments:**']
        for d in self.deployments:
            status = '✅' if d['enabled'] else '⏸️'
            last = d.get('history', [None])[-1]
            last_status = f" (last: {last['status']})" if last else ''
            lines.append(f'{status} **{d["name"]}** — {d["repo"]}/{d["branch"]}{last_status}')
        await ctx.send('\n'.join(lines))

    @deploy_group.command(name='delete')
    async def deploy_delete(self, ctx, name: str):
        """Delete a deployment."""
        self.deployments = [d for d in self.deployments if d['name'] != name]
        self._save_deployments()
        await ctx.send(f'🗑️ Deployment **{name}** deleted.')

    @deploy_group.command(name='toggle')
    async def deploy_toggle(self, ctx, name: str):
        """Enable/disable a deployment."""
        for d in self.deployments:
            if d['name'] == name:
                d['enabled'] = not d['enabled']
                self._save_deployments()
                status = 'enabled' if d['enabled'] else 'disabled'
                await ctx.send(f'{"✅" if d["enabled"] else "⏸️"} Deployment **{name}** {status}.')
                return
        await ctx.send(f'❌ Deployment **{name}** not found.')

    @deploy_group.command(name='logs')
    async def deploy_logs(self, ctx, name: str):
        """Show deployment history."""
        for d in self.deployments:
            if d['name'] == name:
                history = d.get('history', [])
                if not history:
                    await ctx.send(f'No deployment history for **{name}**.')
                    return
                lines = [f'**Deployment History: {name}**']
                for h in history[-5:]:
                    icon = '✅' if h['status'] == 'success' else '❌'
                    lines.append(f'{icon} {h["timestamp"][:19]} — {h["status"]}')
                await ctx.send('\n'.join(lines))
                return
        await ctx.send(f'❌ Deployment **{name}** not found.')


async def setup(bot):
    await bot.add_cog(GitDeployer(bot))
