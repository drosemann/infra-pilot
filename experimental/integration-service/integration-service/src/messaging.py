import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp
import logging

logger = logging.getLogger(__name__)


class MessageBridge:
    """Cross-platform messaging bridge Discord<->Minecraft with format conversion"""

    SECTION_SIGN = '\u00a7'
    COLOR_MAP = {
        '0': '#000000', '1': '#0000AA', '2': '#00AA00', '3': '#00AAAA',
        '4': '#AA0000', '5': '#AA00AA', '6': '#FFAA00', '7': '#AAAAAA',
        '8': '#555555', '9': '#5555FF', 'a': '#55FF55', 'b': '#55FFFF',
        'c': '#FF5555', 'd': '#FF55FF', 'e': '#FFFF55', 'f': '#FFFFFF',
        'l': '**', 'm': '~~', 'n': '__', 'o': '*', 'r': ''
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.discord_webhook = config.get('discord_webhook')
        self.minecraft_webhook = config.get('minecraft_webhook')
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        logger.info("MessageBridge initialized")

    async def close(self):
        if self.session:
            await self.session.close()

    def minecraft_to_markdown(self, text: str) -> str:
        result = []
        parts = re.split(f'({self.SECTION_SIGN}.)', text)
        bold = False
        for part in parts:
            if re.match(f'^{self.SECTION_SIGN}.$', part):
                code = part[1]
                if code == 'l':
                    result.append('**')
                    bold = True
                elif code == 'm':
                    result.append('~~')
                elif code == 'n':
                    result.append('__')
                elif code == 'o':
                    result.append('*')
                elif code == 'r':
                    if bold:
                        result.append('**')
                        bold = False
            else:
                result.append(part)
        if bold:
            result.append('**')
        return ''.join(result)

    def markdown_to_minecraft(self, text: str) -> str:
        result = text
        result = re.sub(r'\*\*(.+?)\*\*', f'{self.SECTION_SIGN}l\\1{self.SECTION_SIGN}r', result)
        result = re.sub(r'\*\*(.+?)\*\*', f'{self.SECTION_SIGN}l\\1{self.SECTION_SIGN}r', result)
        result = re.sub(r'\*(.+?)\*', f'{self.SECTION_SIGN}o\\1{self.SECTION_SIGN}r', result)
        result = re.sub(r'__(.+?)__', f'{self.SECTION_SIGN}n\\1{self.SECTION_SIGN}r', result)
        result = re.sub(r'~~(.+?)~~', f'{self.SECTION_SIGN}m\\1{self.SECTION_SIGN}r', result)
        result = re.sub(r'`(.+?)`', f'{self.SECTION_SIGN}7\\1{self.SECTION_SIGN}r', result)
        return result

    async def send_discord_to_minecraft(self, message: Dict[str, Any]) -> bool:
        content = message.get('content', '')
        author = message.get('author', 'Unknown')
        minecraft_msg = f'[Discord] {author}: {self.markdown_to_minecraft(content)}'
        if self.minecraft_webhook:
            try:
                async with self.session.post(
                    self.minecraft_webhook,
                    json={'message': minecraft_msg, 'platform': 'discord'}
                ) as resp:
                    return resp.status == 200
            except Exception as e:
                logger.error(f"Minecraft webhook failed: {e}")
        return False

    async def send_minecraft_to_discord(self, message: Dict[str, Any]) -> bool:
        content = message.get('content', '')
        author = message.get('author', 'Server')
        discord_msg = self.minecraft_to_markdown(content)
        if self.discord_webhook:
            try:
                embed = {
                    'embeds': [{
                        'title': f'💬 {author}',
                        'description': discord_msg,
                        'color': 0x6C5CE7,
                        'timestamp': datetime.now().isoformat()
                    }]
                }
                async with self.session.post(self.discord_webhook, json=embed) as resp:
                    return resp.status in [200, 204]
            except Exception as e:
                logger.error(f"Discord webhook failed: {e}")
        return False

    async def process_webhook(self, platform: str, payload: Dict[str, Any]) -> bool:
        if platform == 'discord':
            return await self.send_discord_to_minecraft(payload)
        elif platform == 'minecraft':
            return await self.send_minecraft_to_discord(payload)
        return False

    async def convert_format(self, text: str, from_format: str, to_format: str) -> Dict[str, Any]:
        if from_format == 'minecraft' and to_format == 'markdown':
            return {'original': text, 'converted': self.minecraft_to_markdown(text)}
        elif from_format == 'markdown' and to_format == 'minecraft':
            return {'original': text, 'converted': self.markdown_to_minecraft(text)}
        return {'original': text, 'converted': text}
