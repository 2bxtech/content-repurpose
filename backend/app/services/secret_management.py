"""
Secret Management Service

Provides secure handling of API keys, credentials, and sensitive configuration
with rotation capabilities and access logging.
"""

import os
import json
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import base64

from app.services.redis_service import redis_service
from app.services.audit_service import audit_service, AuditEventType, AuditLevel


# Simple encryption using base64 for now (in production, use proper encryption)
class SimpleCipher:
    """Simple cipher for secret encryption (replace with proper encryption in production)"""

    def __init__(self, key: bytes):
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """Simple XOR encryption (not cryptographically secure - replace in production)"""
        # For now, just use base64 encoding
        # In production, use proper encryption like Fernet from cryptography
        return base64.b64encode(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Simple XOR decryption"""
        # For now, just use base64 decoding
        # In production, use proper decryption
        return base64.b64decode(encrypted_data)


logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Types of secrets managed"""

    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    WEBHOOK_SECRET = "webhook_secret"
    OAUTH_SECRET = "oauth_secret"


class SecretStatus(str, Enum):
    """Secret status"""

    ACTIVE = "active"
    ROTATED = "rotated"
    EXPIRED = "expired"
    COMPROMISED = "compromised"


@dataclass
class SecretMetadata:
    """Metadata for a managed secret"""

    secret_id: str
    name: str
    secret_type: SecretType
    status: SecretStatus
    created_at: str
    expires_at: Optional[str] = None
    last_rotated: Optional[str] = None
    last_accessed: Optional[str] = None
    access_count: int = 0
    rotation_policy_days: Optional[int] = None
    description: Optional[str] = None


@dataclass
class SecretAccessLog:
    """Log entry for secret access"""

    secret_id: str
    accessed_at: str
    accessed_by: Optional[str] = None
    access_type: str = "read"  # read, rotate, delete
    source_ip: Optional[str] = None
    success: bool = True
    reason: Optional[str] = None


class SecretManager:
    """Secure secret management with encryption and rotation"""

    def __init__(self):
        self.secrets_dir = Path("secrets")
        self.secrets_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encryption key
        self.encryption_key = self._get_or_create_master_key()
        self.cipher = SimpleCipher(self.encryption_key)

        # Secret metadata storage
        self.metadata_file = self.secrets_dir / "metadata.json"
        self.metadata: Dict[str, SecretMetadata] = self._load_metadata()

        # Access logs
        self.access_logs: List[SecretAccessLog] = []

        # Default rotation policies (in days)
        self.default_rotation_policies = {
            SecretType.API_KEY: 90,  # 3 months
            SecretType.JWT_SECRET: 30,  # 1 month
            SecretType.DATABASE_PASSWORD: 90,  # 3 months
            SecretType.ENCRYPTION_KEY: 365,  # 1 year
            SecretType.WEBHOOK_SECRET: 180,  # 6 months
            SecretType.OAUTH_SECRET: 90,  # 3 months
        }

    def _get_or_create_master_key(self) -> bytes:
        """Get or create the master encryption key"""
        key_file = self.secrets_dir / ".master_key"

        if key_file.exists():
            # Load existing key
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new key (32 bytes for simple cipher)
            key = secrets.token_bytes(32)

            # Save key with restricted permissions
            with open(key_file, "wb") as f:
                f.write(key)

            # Set restrictive permissions (Unix-like systems)
            try:
                os.chmod(key_file, 0o600)
            except Exception:
                pass  # Windows doesn't support this

            logger.info("Generated new master encryption key")
            return key

    def _load_metadata(self) -> Dict[str, SecretMetadata]:
        """Load secret metadata from file"""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, "r") as f:
                data = json.load(f)

            return {
                secret_id: SecretMetadata(**metadata)
                for secret_id, metadata in data.items()
            }
        except Exception as e:
            logger.error(f"Failed to load secret metadata: {e}")
            return {}

    def _save_metadata(self):
        """Save secret metadata to file"""
        try:
            data = {
                secret_id: asdict(metadata)
                for secret_id, metadata in self.metadata.items()
            }

            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2)

            # Set restrictive permissions
            try:
                os.chmod(self.metadata_file, 0o600)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to save secret metadata: {e}")

    def _generate_secret_id(self, name: str) -> str:
        """Generate unique secret ID"""
        timestamp = str(int(datetime.now().timestamp()))
        content = f"{name}_{timestamp}_{secrets.token_hex(8)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_secret_file_path(self, secret_id: str) -> Path:
        """Get file path for secret"""
        return self.secrets_dir / f"{secret_id}.enc"

    async def store_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType,
        description: Optional[str] = None,
        rotation_policy_days: Optional[int] = None,
        accessed_by: Optional[str] = None,
    ) -> str:
        """Store a new secret securely"""

        try:
            # Generate unique ID
            secret_id = self._generate_secret_id(name)

            # Encrypt the secret value
            encrypted_value = self.cipher.encrypt(value.encode())

            # Store encrypted secret to file
            secret_file = self._get_secret_file_path(secret_id)
            with open(secret_file, "wb") as f:
                f.write(encrypted_value)

            # Set restrictive permissions
            try:
                os.chmod(secret_file, 0o600)
            except Exception:
                pass

            # Create metadata
            rotation_days = rotation_policy_days or self.default_rotation_policies.get(
                secret_type
            )
            expires_at = None
            if rotation_days:
                expires_at = (
                    datetime.now() + timedelta(days=rotation_days)
                ).isoformat()

            metadata = SecretMetadata(
                secret_id=secret_id,
                name=name,
                secret_type=secret_type,
                status=SecretStatus.ACTIVE,
                created_at=datetime.now().isoformat(),
                expires_at=expires_at,
                rotation_policy_days=rotation_days,
                description=description,
            )

            self.metadata[secret_id] = metadata
            self._save_metadata()

            # Log access
            await self._log_secret_access(
                secret_id, "create", accessed_by, success=True
            )

            # Audit log
            await audit_service.log_event(
                event_type=AuditEventType.SECURITY_TOKEN_BLACKLISTED,  # Reusing for secret events
                level=AuditLevel.INFO,
                details={
                    "secret_id": secret_id,
                    "secret_name": name,
                    "secret_type": secret_type,
                    "action": "created",
                    "has_rotation_policy": rotation_days is not None,
                },
            )

            logger.info(f"Secret '{name}' stored with ID: {secret_id}")
            return secret_id

        except Exception as e:
            await self._log_secret_access(
                secret_id if "secret_id" in locals() else "unknown",
                "create",
                accessed_by,
                success=False,
                reason=str(e),
            )
            logger.error(f"Failed to store secret '{name}': {e}")
            raise

    async def get_secret(
        self, secret_id: str, accessed_by: Optional[str] = None
    ) -> Optional[str]:
        """Retrieve a secret value"""

        try:
            # Check if secret exists
            if secret_id not in self.metadata:
                await self._log_secret_access(
                    secret_id,
                    "read",
                    accessed_by,
                    success=False,
                    reason="Secret not found",
                )
                return None

            metadata = self.metadata[secret_id]

            # Check if secret is active
            if metadata.status != SecretStatus.ACTIVE:
                await self._log_secret_access(
                    secret_id,
                    "read",
                    accessed_by,
                    success=False,
                    reason=f"Secret status is {metadata.status}",
                )
                return None

            # Check if expired
            if metadata.expires_at:
                expires_at = datetime.fromisoformat(metadata.expires_at)
                if datetime.now() > expires_at:
                    # Mark as expired
                    metadata.status = SecretStatus.EXPIRED
                    self._save_metadata()

                    await self._log_secret_access(
                        secret_id,
                        "read",
                        accessed_by,
                        success=False,
                        reason="Secret expired",
                    )
                    return None

            # Read and decrypt secret
            secret_file = self._get_secret_file_path(secret_id)
            if not secret_file.exists():
                await self._log_secret_access(
                    secret_id,
                    "read",
                    accessed_by,
                    success=False,
                    reason="Secret file not found",
                )
                return None

            with open(secret_file, "rb") as f:
                encrypted_value = f.read()

            decrypted_value = self.cipher.decrypt(encrypted_value).decode()

            # Update access metadata
            metadata.last_accessed = datetime.now().isoformat()
            metadata.access_count += 1
            self._save_metadata()

            # Log successful access
            await self._log_secret_access(secret_id, "read", accessed_by, success=True)

            return decrypted_value

        except Exception as e:
            await self._log_secret_access(
                secret_id, "read", accessed_by, success=False, reason=str(e)
            )
            logger.error(f"Failed to retrieve secret {secret_id}: {e}")
            return None

    async def rotate_secret(
        self, secret_id: str, new_value: str, accessed_by: Optional[str] = None
    ) -> bool:
        """Rotate a secret to a new value"""

        try:
            if secret_id not in self.metadata:
                return False

            metadata = self.metadata[secret_id]

            # Create backup of old secret (optional)
            old_secret_file = self._get_secret_file_path(secret_id)
            backup_file = (
                self.secrets_dir
                / f"{secret_id}_backup_{int(datetime.now().timestamp())}.enc"
            )

            if old_secret_file.exists():
                import shutil

                shutil.copy2(old_secret_file, backup_file)

            # Encrypt and store new value
            encrypted_value = self.cipher.encrypt(new_value.encode())
            with open(old_secret_file, "wb") as f:
                f.write(encrypted_value)

            # Update metadata
            metadata.last_rotated = datetime.now().isoformat()
            metadata.status = SecretStatus.ACTIVE

            # Update expiration if rotation policy exists
            if metadata.rotation_policy_days:
                metadata.expires_at = (
                    datetime.now() + timedelta(days=metadata.rotation_policy_days)
                ).isoformat()

            self._save_metadata()

            # Log rotation
            await self._log_secret_access(
                secret_id, "rotate", accessed_by, success=True
            )

            # Audit log
            await audit_service.log_event(
                event_type=AuditEventType.SECURITY_TOKEN_BLACKLISTED,
                level=AuditLevel.INFO,
                details={
                    "secret_id": secret_id,
                    "secret_name": metadata.name,
                    "action": "rotated",
                    "rotation_time": metadata.last_rotated,
                },
            )

            logger.info(f"Secret {secret_id} rotated successfully")
            return True

        except Exception as e:
            await self._log_secret_access(
                secret_id, "rotate", accessed_by, success=False, reason=str(e)
            )
            logger.error(f"Failed to rotate secret {secret_id}: {e}")
            return False

    async def mark_compromised(
        self, secret_id: str, accessed_by: Optional[str] = None
    ) -> bool:
        """Mark a secret as compromised"""

        try:
            if secret_id not in self.metadata:
                return False

            metadata = self.metadata[secret_id]
            metadata.status = SecretStatus.COMPROMISED
            self._save_metadata()

            # Log compromise
            await self._log_secret_access(
                secret_id, "compromise", accessed_by, success=True
            )

            # Critical audit log
            await audit_service.log_event(
                event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
                level=AuditLevel.CRITICAL,
                details={
                    "secret_id": secret_id,
                    "secret_name": metadata.name,
                    "action": "marked_compromised",
                    "requires_immediate_rotation": True,
                },
            )

            logger.warning(f"Secret {secret_id} marked as compromised")
            return True

        except Exception as e:
            logger.error(f"Failed to mark secret {secret_id} as compromised: {e}")
            return False

    async def delete_secret(
        self, secret_id: str, accessed_by: Optional[str] = None
    ) -> bool:
        """Securely delete a secret"""

        try:
            if secret_id not in self.metadata:
                return False

            metadata = self.metadata[secret_id]

            # Securely delete file
            secret_file = self._get_secret_file_path(secret_id)
            if secret_file.exists():
                # Overwrite with random data before deletion
                file_size = secret_file.stat().st_size
                with open(secret_file, "wb") as f:
                    f.write(secrets.token_bytes(file_size))

                secret_file.unlink()

            # Remove metadata
            del self.metadata[secret_id]
            self._save_metadata()

            # Log deletion
            await self._log_secret_access(
                secret_id, "delete", accessed_by, success=True
            )

            # Audit log
            await audit_service.log_event(
                event_type=AuditEventType.SECURITY_TOKEN_BLACKLISTED,
                level=AuditLevel.WARNING,
                details={
                    "secret_id": secret_id,
                    "secret_name": metadata.name,
                    "action": "deleted",
                },
            )

            logger.info(f"Secret {secret_id} deleted successfully")
            return True

        except Exception as e:
            await self._log_secret_access(
                secret_id, "delete", accessed_by, success=False, reason=str(e)
            )
            logger.error(f"Failed to delete secret {secret_id}: {e}")
            return False

    def list_secrets(self, include_expired: bool = False) -> List[SecretMetadata]:
        """List all secrets with their metadata"""
        secrets_list = []

        for metadata in self.metadata.values():
            # Skip expired secrets unless requested
            if not include_expired and metadata.status == SecretStatus.EXPIRED:
                continue

            secrets_list.append(metadata)

        return secrets_list

    def get_secrets_requiring_rotation(
        self, days_ahead: int = 7
    ) -> List[SecretMetadata]:
        """Get secrets that need rotation within specified days"""
        requiring_rotation = []
        threshold_date = datetime.now() + timedelta(days=days_ahead)

        for metadata in self.metadata.values():
            if metadata.status != SecretStatus.ACTIVE:
                continue

            if metadata.expires_at:
                expires_at = datetime.fromisoformat(metadata.expires_at)
                if expires_at <= threshold_date:
                    requiring_rotation.append(metadata)

        return requiring_rotation

    async def initialize(self):
        """Initialize secret manager"""
        logger.info("Secret manager initialized")

    async def cleanup(self):
        """Cleanup secret manager"""
        logger.info("Secret manager cleaned up")

    async def _log_secret_access(
        self,
        secret_id: str,
        access_type: str,
        accessed_by: Optional[str],
        success: bool = True,
        reason: Optional[str] = None,
    ):
        """Log secret access for audit trail"""

        access_log = SecretAccessLog(
            secret_id=secret_id,
            accessed_at=datetime.now().isoformat(),
            accessed_by=accessed_by,
            access_type=access_type,
            success=success,
            reason=reason,
        )

        self.access_logs.append(access_log)

        # Store in Redis for monitoring
        if redis_service.is_connected():
            try:
                redis_service.lpush(
                    "secret_access_logs", json.dumps(asdict(access_log))
                )
                redis_service.ltrim("secret_access_logs", 0, 9999)  # Keep last 10k logs
            except Exception as e:
                logger.error(f"Failed to store secret access log in Redis: {e}")

    async def get_secret_analytics(self) -> Dict[str, Any]:
        """Get analytics about secret usage and security"""

        total_secrets = len(self.metadata)
        active_secrets = len(
            [m for m in self.metadata.values() if m.status == SecretStatus.ACTIVE]
        )
        expired_secrets = len(
            [m for m in self.metadata.values() if m.status == SecretStatus.EXPIRED]
        )
        compromised_secrets = len(
            [m for m in self.metadata.values() if m.status == SecretStatus.COMPROMISED]
        )

        # Secrets by type
        by_type = {}
        for secret_type in SecretType:
            by_type[secret_type] = len(
                [
                    m
                    for m in self.metadata.values()
                    if m.secret_type == secret_type and m.status == SecretStatus.ACTIVE
                ]
            )

        # Rotation analytics
        requiring_rotation_7d = len(self.get_secrets_requiring_rotation(7))
        requiring_rotation_30d = len(self.get_secrets_requiring_rotation(30))

        # Access analytics (last 24 hours)
        recent_accesses = [
            log
            for log in self.access_logs
            if datetime.fromisoformat(log.accessed_at)
            > datetime.now() - timedelta(hours=24)
        ]

        return {
            "total_secrets": total_secrets,
            "active_secrets": active_secrets,
            "expired_secrets": expired_secrets,
            "compromised_secrets": compromised_secrets,
            "secrets_by_type": by_type,
            "requiring_rotation_7d": requiring_rotation_7d,
            "requiring_rotation_30d": requiring_rotation_30d,
            "recent_accesses_24h": len(recent_accesses),
            "failed_accesses_24h": len(
                [log for log in recent_accesses if not log.success]
            ),
        }


class ConfigurationManager:
    """Manages application configuration with secret integration"""

    def __init__(self, secret_manager: SecretManager):
        self.secret_manager = secret_manager
        self.config_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_update = {}

    async def get_secure_config(self, key: str) -> Optional[str]:
        """Get configuration value, checking secrets first"""

        # Check cache first
        if key in self.config_cache:
            last_update = self.last_cache_update.get(key, 0)
            if time.time() - last_update < self.cache_ttl:
                return self.config_cache[key]

        # Try to get from secrets first
        secret_value = await self.secret_manager.get_secret(key)
        if secret_value:
            self.config_cache[key] = secret_value
            self.last_cache_update[key] = time.time()
            return secret_value

        # Fall back to environment variables
        env_value = os.getenv(key)
        if env_value:
            self.config_cache[key] = env_value
            self.last_cache_update[key] = time.time()
            return env_value

        return None

    async def update_secret_config(
        self, key: str, value: str, secret_type: SecretType
    ) -> bool:
        """Update a configuration secret"""
        try:
            # Store new secret
            await self.secret_manager.store_secret(
                name=key,
                value=value,
                secret_type=secret_type,
                description=f"Configuration secret for {key}",
            )

            # Clear cache
            if key in self.config_cache:
                del self.config_cache[key]
                del self.last_cache_update[key]

            return True

        except Exception as e:
            logger.error(f"Failed to update secret config {key}: {e}")
            return False

    def clear_cache(self):
        """Clear configuration cache"""
        self.config_cache.clear()
        self.last_cache_update.clear()


# Global secret manager instance
secret_manager = SecretManager()
config_manager = ConfigurationManager(secret_manager)
