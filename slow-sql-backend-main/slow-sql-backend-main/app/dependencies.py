from fastapi import Header, HTTPException, status
from app.config import settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """
    API_KEY认证依赖
    验证请求头中的X-API-Key是否匹配配置的API_KEY
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key

