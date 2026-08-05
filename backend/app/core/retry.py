import json
from pydantic import ValidationError
from app.config import settings

def should_retry(exception: Exception, retry_count: int) -> bool:
    if retry_count >= settings.MAX_RETRIES:
        return False
        
    fatal_exceptions = (
        ValidationError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    )
    
    if isinstance(exception, fatal_exceptions):
        return False
        
    return True
