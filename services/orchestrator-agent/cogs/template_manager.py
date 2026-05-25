import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
import json
import logging

from config import config
from vps_manager import VPSManager, VPSConfig


class TemplateManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vps_manager = VPSManager()

    @app_commands.command(name="templatecreate", description="Create a VPS template")
    @app_commands.describe(name="Template name", image="Docker image", cpu="CPU cores", memory="Memory MB", storage="Storage GB")
    async def template_create(self, interaction: discord.Interaction, name: str, image: str, cpu: float = 1, memory: int = 1024, storage: int = 20):
        template_config = {"image": image, "cpu": cpu, "memory": memory, "storage": storage}

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO templates (name, version, config, created_by) VALUES (%s, %s, %s, %s)",
                (name, 1, json.dumps(template_config), str(interaction.user.id)),
            )
            conn.commit()
            cursor.close()
            conn.close()

            embed = discord.Embed(title="Template Created", color=discord.Color.green())
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Image", value=image, inline=True)
            embed.add_field(name="CPU", value=str(cpu), inline=True)
            embed.add_field(name="Memory", value=f"{memory}MB", inline=True)
            embed.add_field(name="Storage", value=f"{storage}GB", inline=True)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="templateapply", description="Apply a template to create a VPS")
    @app_commands.describe(template_name="Template name", version="Template version (default: latest)")
    async def template_apply(self, interaction: discord.Interaction, template_name: str, version: int = None):
        await interaction.response.defer()

        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)

            if version:
                cursor.execute("SELECT * FROM templates WHERE name = %s AND version = %s", (template_name, version))
            else:
                cursor.execute("SELECT * FROM templates WHERE name = %s ORDER BY version DESC LIMIT 1", (template_name,))

            template = cursor.fetchone()
            cursor.close()
            conn.close()

            if not template:
                await interaction.followup.send(embed=discord.Embed(description="Template not found.", color=0xFF0000))
                return

            tmpl = json.loads(template["config"])
            cfg = VPSConfig(
                cpu_limit=tmpl["cpu"],
                memory_limit=tmpl["memory"],
                storage_limit=tmpl["storage"],
                image=tmpl["image"],
                ports={},
                env_vars={},
            )

            container_id = await self.vps_manager.create_vps(str(interaction.user.id), cfg)
            if container_id:
                embed = discord.Embed(title="VPS Created from Template", color=discord.Color.green())
                embed.add_field(name="Template", value=template_name, inline=True)
                embed.add_field(name="Container ID", value=container_id[:12], inline=True)
                embed.add_field(name="Image", value=tmpl["image"], inline=True)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(embed=discord.Embed(description="Failed to create VPS.", color=0xFF0000))
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))

    @app_commands.command(name="templatelist", description="List available templates")
    async def template_list(self, interaction: discord.Interaction):
        try:
            conn = self.vps_manager._get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM templates ORDER BY name, version DESC")
            templates = cursor.fetchall()
            cursor.close()
            conn.close()

            embed = discord.Embed(title="Available Templates", color=discord.Color.blue())
            if not templates:
                embed.description = "No templates defined."
            else:
                seen = set()
                for t in templates:
                    if t["name"] not in seen:
                        seen.add(t["name"])
                        tmpl = json.loads(t["config"])
                        embed.add_field(
                            name=f"{t['name']} (v{t['version']})",
                            value=f"Image: {tmpl['image']}\nCPU: {tmpl['cpu']} | RAM: {tmpl['memory']}MB | Storage: {tmpl['storage']}GB",
                            inline=False,
                        )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(description=f"Error: {str(e)}", color=0xFF0000))


async def setup(bot):
    await bot.add_cog(TemplateManager(bot))
