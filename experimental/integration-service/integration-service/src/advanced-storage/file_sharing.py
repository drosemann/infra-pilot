"""File Sharing integration module."""
import asyncio
import hashlib
import hmac
import logging
import os
import re
import secrets
import string
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)
PBKDF2_ITERATIONS = 310000
PBKDF2_SALT_BYTES = 16


class SharingBackend(Enum):
    NEXTCLOUD = "nextcloud"
    SEAFILE = "seafile"
    OWNCLOUD = "owncloud"
    PYDIO = "pydio"
    FILEBROWSER = "filebrowser"


class SharePermission(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    ADMIN = "admin"


class ShareLinkStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PASSWORD_PROTECTED = "password_protected"


@dataclass
class ShareLink:
    link_id: str
    path: str
    backend: SharingBackend
    permission: SharePermission
    status: ShareLinkStatus
    created_by: str
    created_at: str
    expires_at: Optional[str] = None
    password_hash: Optional[str] = None
    max_downloads: Optional[int] = None
    download_count: int = 0
    description: str = ""
    allowed_users: List[str] = field(default_factory=list)
    notify_on_access: bool = False
    track_analytics: bool = True

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def is_expired(self) -> bool:
        if self.expires_at:
            expiry = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expiry
        return False

    def is_max_downloads_reached(self) -> bool:
        if self.max_downloads:
            return self.download_count >= self.max_downloads
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "path": self.path,
            "backend": self.backend.value,
            "permission": self.permission.value,
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "has_password": self.password_hash is not None,
            "max_downloads": self.max_downloads,
            "download_count": self.download_count,
            "description": self.description,
            "allowed_users": self.allowed_users,
            "notify_on_access": self.notify_on_access,
            "track_analytics": self.track_analytics,
            "url": self._generate_url(),
        }

    def _generate_url(self) -> str:
        return f"https://files.infrapilot.io/share/{self.link_id}"


@dataclass
class FileItem:
    path: str
    name: str
    size_bytes: int
    is_directory: bool
    content_type: str
    modified_at: str
    created_at: str
    owner: str
    shared: bool = False
    share_links: List[str] = field(default_factory=list)
    checksum: str = ""
    tags: List[str] = field(default_factory=list)
    starred: bool = False
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "size_bytes": self.size_bytes,
            "size_display": self._format_size(),
            "is_directory": self.is_directory,
            "content_type": self.content_type,
            "modified_at": self.modified_at,
            "created_at": self.created_at,
            "owner": self.owner,
            "shared": self.shared,
            "share_count": len(self.share_links),
            "checksum": self.checksum,
            "tags": self.tags,
            "starred": self.starred,
            "version": self.version,
        }

    def _format_size(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 ** 2:
            return f"{self.size_bytes / 1024:.1f} KB"
        elif self.size_bytes < 1024 ** 3:
            return f"{self.size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{self.size_bytes / 1024 ** 3:.2f} GB"


class FileSharingManager:
    """Multi-backend file sharing with Nextcloud/Seafile integration."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.share_links: Dict[str, ShareLink] = {}
        self.files: Dict[str, FileItem] = {}
        self.backend_connections: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._total_shares_created = 0
        self._total_downloads = 0
        self._active_users = set()
        self._storage_used = 0
        self._sync_queue: List[Dict[str, Any]] = []
        self._cross_server_syncs: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        self._running = True
        logger.info("File Sharing Manager initialized")

    async def close(self) -> None:
        self._running = False
        logger.info("File Sharing Manager shut down")

    async def create_share_link(
        self,
        path: str,
        backend: str = "nextcloud",
        permission: str = "read",
        expires_in_hours: Optional[int] = None,
        password: Optional[str] = None,
        max_downloads: Optional[int] = None,
        description: str = "",
        created_by: str = "admin",
        allowed_users: Optional[List[str]] = None,
    ) -> ShareLink:
        share_id = f"share-{uuid.uuid4().hex[:12]}"
        expires_at = None
        if expires_in_hours:
            expires_at = (datetime.utcnow() + timedelta(hours=expires_in_hours)).isoformat()

        password_hash = None
        if password:
            salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
            derived = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, PBKDF2_ITERATIONS
            )
            password_hash = (
                f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"
            )

        link = ShareLink(
            link_id=share_id,
            path=path,
            backend=SharingBackend(backend),
            permission=SharePermission(permission),
            status=ShareLinkStatus.PASSWORD_PROTECTED if password else ShareLinkStatus.ACTIVE,
            created_by=created_by,
            expires_at=expires_at,
            password_hash=password_hash,
            max_downloads=max_downloads,
            description=description,
            allowed_users=allowed_users or [],
        )
        self.share_links[share_id] = link
        self._total_shares_created += 1
        logger.info(f"Created share link '{share_id}' for '{path}'")
        return link

    async def get_share_link(self, link_id: str) -> Optional[ShareLink]:
        return self.share_links.get(link_id)

    async def revoke_share_link(self, link_id: str) -> bool:
        if link_id not in self.share_links:
            return False
        self.share_links[link_id].status = ShareLinkStatus.REVOKED
        return True

    async def access_share_link(
        self, link_id: str, password: Optional[str] = None, user: Optional[str] = None
    ) -> Optional[FileItem]:
        link = self.share_links.get(link_id)
        if not link:
            return None

        if link.status == ShareLinkStatus.REVOKED:
            raise PermissionError("Share link has been revoked")

        if link.is_expired():
            link.status = ShareLinkStatus.EXPIRED
            raise PermissionError("Share link has expired")

        if link.is_max_downloads_reached():
            raise PermissionError("Share link download limit reached")

        if link.password_hash:
            if not password:
                raise PermissionError("Password required")
            try:
                algorithm, iterations_str, salt_hex, expected_hex = link.password_hash.split("$", 3)
                if algorithm != "pbkdf2_sha256":
                    raise ValueError("Unsupported password hash algorithm")
                iterations = int(iterations_str)
                salt = bytes.fromhex(salt_hex)
                expected = bytes.fromhex(expected_hex)
            except (ValueError, TypeError):
                raise PermissionError("Incorrect password")

            calculated = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
            if not hmac.compare_digest(calculated, expected):
                raise PermissionError("Incorrect password")

        if link.allowed_users and user and user not in link.allowed_users:
            raise PermissionError("User not authorized for this share")

        link.download_count += 1
        self._total_downloads += 1

        file_item = self.files.get(link.path)
        if not file_item:
            raise FileNotFoundError(f"File not found: {link.path}")
        return file_item

    async def list_share_links(
        self, path: Optional[str] = None, created_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        links = list(self.share_links.values())
        if path:
            links = [l for l in links if l.path.startswith(path)]
        if created_by:
            links = [l for l in links if l.created_by == created_by]
        return [l.to_dict() for l in links]

    async def upload_file(
        self,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        owner: str = "admin",
        tags: Optional[List[str]] = None,
    ) -> FileItem:
        checksum = hashlib.sha256(data).hexdigest()
        name = os.path.basename(path)

        file_item = FileItem(
            path=path,
            name=name,
            size_bytes=len(data),
            is_directory=False,
            content_type=content_type,
            modified_at=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
            owner=owner,
            checksum=checksum,
            tags=tags or [],
        )
        self.files[path] = file_item
        self._storage_used += len(data)
        return file_item

    async def create_directory(
        self,
        path: str,
        owner: str = "admin",
        tags: Optional[List[str]] = None,
    ) -> FileItem:
        name = os.path.basename(path.rstrip("/"))
        dir_item = FileItem(
            path=path,
            name=name,
            size_bytes=0,
            is_directory=True,
            content_type="inode/directory",
            modified_at=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
            owner=owner,
            tags=tags or [],
        )
        self.files[path] = dir_item
        return dir_item

    async def delete_file(self, path: str) -> bool:
        if path not in self.files:
            return False
        item = self.files.pop(path)
        if not item.is_directory:
            self._storage_used -= item.size_bytes
        return True

    async def list_files(
        self, directory: str = "/", recursive: bool = False
    ) -> List[Dict[str, Any]]:
        items = []
        for path, item in self.files.items():
            if recursive:
                if path.startswith(directory):
                    items.append(item.to_dict())
            else:
                parent = os.path.dirname(path.rstrip("/")) + "/"
                if parent == directory or (directory == "/" and parent == "\\"):
                    items.append(item.to_dict())
        items.sort(key=lambda x: (not x["is_directory"], x["name"]))
        return items

    async def search_files(
        self,
        query: str,
        file_type: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = []
        for path, item in self.files.items():
            if query_lower in item.name.lower() or query_lower in path.lower():
                if file_type and not path.endswith(file_type):
                    continue
                if owner and item.owner != owner:
                    continue
                results.append(item.to_dict())
        return results

    async def star_file(self, path: str, starred: bool = True) -> bool:
        if path not in self.files:
            return False
        self.files[path].starred = starred
        return True

    async def add_tags(self, path: str, tags: List[str]) -> bool:
        if path not in self.files:
            return False
        existing = set(self.files[path].tags)
        existing.update(tags)
        self.files[path].tags = list(existing)
        return True

    async def remove_tags(self, path: str, tags: List[str]) -> bool:
        if path not in self.files:
            return False
        existing = set(self.files[path].tags)
        existing.difference_update(tags)
        self.files[path].tags = list(existing)
        return True

    async def setup_cross_server_sync(
        self,
        source_backend: str,
        source_path: str,
        dest_backend: str,
        dest_path: str,
        sync_interval_minutes: int = 60,
        bidirectional: bool = False,
    ) -> Dict[str, Any]:
        sync_id = f"sync-{uuid.uuid4().hex[:8]}"
        sync_config = {
            "sync_id": sync_id,
            "source_backend": source_backend,
            "source_path": source_path,
            "dest_backend": dest_backend,
            "dest_path": dest_path,
            "sync_interval_minutes": sync_interval_minutes,
            "bidirectional": bidirectional,
            "last_sync": None,
            "status": "active",
            "files_synced": 0,
            "bytes_synced": 0,
            "last_error": None,
        }
        self._cross_server_syncs[sync_id] = sync_config
        return sync_config

    async def get_cross_server_syncs(self) -> List[Dict[str, Any]]:
        return list(self._cross_server_syncs.values())

    async def delete_cross_server_sync(self, sync_id: str) -> bool:
        if sync_id not in self._cross_server_syncs:
            return False
        del self._cross_server_syncs[sync_id]
        return True

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_shares": len(self.share_links),
            "active_shares": sum(1 for l in self.share_links.values() if l.status == ShareLinkStatus.ACTIVE),
            "total_downloads": self._total_downloads,
            "total_files": sum(1 for f in self.files.values() if not f.is_directory),
            "total_directories": sum(1 for f in self.files.values() if f.is_directory),
            "storage_used": self._storage_used,
            "storage_display": self._format_bytes(self._storage_used),
            "active_users": len(self._active_users),
            "sync_count": len(self._cross_server_syncs),
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._running else "unhealthy",
            "shares": len(self.share_links),
            "backends": list(self.backend_connections.keys()),
        }

    def _format_bytes(self, bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 ** 2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 ** 3:
            return f"{bytes_val / 1024 ** 2:.1f} MB"
        else:
            return f"{bytes_val / 1024 ** 3:.2f} GB"

    async def run_sync_cycle(self) -> Dict[str, Any]:
        synced = 0
        errors = 0
        for sync_id, sync_cfg in self._cross_server_syncs.items():
            try:
                sync_cfg["last_sync"] = datetime.utcnow().isoformat()
                sync_cfg["files_synced"] += 1
                synced += 1
            except Exception as e:
                errors += 1
                sync_cfg["last_error"] = str(e)
        return {"synced": synced, "errors": errors}
