import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class DataSourceCryptoService:
    @staticmethod
    def _build_fernet() -> Fernet:
        secret = (settings.data_source_secret_key or "").strip()
        if not secret:
            raise RuntimeError("未配置 DATA_SOURCE_SECRET_KEY，无法保存数据源密码")

        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    @classmethod
    def encrypt(cls, value: str) -> str:
        return cls._build_fernet().encrypt(value.encode("utf-8")).decode("utf-8")

    @classmethod
    def decrypt(cls, encrypted_value: str) -> str:
        try:
            return cls._build_fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:  # pragma: no cover - 配置错误时的保护
            raise RuntimeError("数据源密码解密失败，请检查 DATA_SOURCE_SECRET_KEY") from exc
