"""Password login for the copilot when it is served publicly (e.g. on Vercel).

Requests from this machine are trusted as before. Anyone else needs the shared APP_PASSWORD; a successful login sets
a signed, expiring cookie. Without APP_PASSWORD there is no way in from outside: the copilot stays private by default.
The prospect's call page (/sala/...) never needs a login.
"""

from __future__ import annotations

import hmac
import os
import time
from typing import Any, Mapping

from .videocall import is_local, sign

COOKIE = "copilot_auth"
SESSION_DAYS = 30


def password() -> str:
    return os.environ.get("APP_PASSWORD", "").strip()


def make_cookie(now: float | None = None) -> str:
    expires = str(int((now or time.time()) + SESSION_DAYS * 86400))
    return f"{expires}.{sign('login:' + expires)}"


def cookie_valid(value: str | None, now: float | None = None) -> bool:
    if not value or "." not in value or not password():
        return False
    expires, sig = value.split(".", 1)
    return expires.isdigit() and int(expires) > (now or time.time()) and hmac.compare_digest(sig, sign("login:" + expires))


def authorized(headers: Mapping[str, Any], cookies: Mapping[str, str]) -> bool:
    return is_local(headers) or cookie_valid(cookies.get(COOKIE))


def password_ok(candidate: str) -> bool:
    return bool(password()) and hmac.compare_digest(candidate.encode(), password().encode())


LOGIN_PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Sales Copilot · entrar</title>
<style>
  body { margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #0e1117; color: #e6e9ef;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif; }
  form { background: #161b22; border: 1px solid #2a3140; border-radius: 12px; padding: 28px; width: min(360px, calc(100vw - 32px)); }
  h1 { font-size: 18px; margin: 0 0 6px; } p { color: #8b95a7; font-size: 13px; margin: 0 0 18px; }
  input { width: 100%; box-sizing: border-box; background: #1c2330; color: #e6e9ef; border: 1px solid #2a3140; border-radius: 8px; padding: 10px; font-size: 15px; }
  button { margin-top: 12px; width: 100%; background: #6ea8fe; color: #0b0f16; border: 0; border-radius: 8px; padding: 10px; font-size: 15px; font-weight: 600; cursor: pointer; }
  .err { color: #ff5c5c; font-size: 13px; margin-top: 10px; }
</style></head>
<body><form method="post" action="/login">
  <h1>Sales Copilot</h1><p>Entre com a senha da equipe.</p>
  <input type="password" name="password" autofocus autocomplete="current-password" placeholder="senha" />
  <button type="submit">Entrar</button>{error}
</form></body></html>"""
