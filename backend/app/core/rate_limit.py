import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status

# Simple in-memory rate limiter: maps IP -> list of timestamps
_login_attempts: Dict[str, List[float]] = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60  # 10 attempts per minute per IP


def check_rate_limit(request: Request) -> None:
    """
    Enforces rate limiting on sensitive endpoints (e.g. login).
    Raises HTTP 429 Too Many Requests if limit is exceeded.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    
    # Filter attempts within the window
    attempts = [t for t in _login_attempts[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _login_attempts[client_ip] = attempts
    
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait a minute before trying again."
        )
    
    _login_attempts[client_ip].append(now)
