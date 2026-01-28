import base64
import hashlib
import hmac
import os
import time

from pathlib import Path
from tempfile import gettempdir

from quart import Quart, abort, redirect, render_template, request
from cache import FileCache
from modder import GAMES, pack


WEBSERVER = Quart(__name__)
CACHE_DIR = Path(gettempdir()) / "idlemod_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

cache = FileCache(CACHE_DIR, max_entries=10, max_age_seconds=3600)

BOT_TOKEN_SECRET = os.urandom(32).hex()
BOT_TOKEN_MAX_AGE = 300  # 5 min


def _generate_token() -> str:
    timestamp = int(time.time())
    message = str(timestamp).encode()
    signature = hmac.new(BOT_TOKEN_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return f"{timestamp}.{signature}"


def _obfuscate_token(token: str) -> tuple[str, str]:
    key = os.urandom(len(token))
    xored = bytes(a ^ b for a, b in zip(token.encode(), key))
    return base64.b64encode(xored).decode(), base64.b64encode(key).decode()


def _validate_token(token: str) -> bool:
    if not token or "." not in token:
        return False

    try:
        timestamp_str, signature = token.split(".", 1)
        timestamp = int(timestamp_str)
    except ValueError:
        return False

    if time.time() - timestamp > BOT_TOKEN_MAX_AGE:
        return False

    expected = hmac.new(
        BOT_TOKEN_SECRET.encode(), timestamp_str.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def _get_game(game_id: str):
    game = GAMES.get(game_id)
    if game is None:
        abort(404, f"Game with ID `{game_id}` not found.")
    return game


def _cache_key(game_id: str, mods: list[str]) -> str:
    return hashlib.md5(f"{game_id}:{'|'.join(sorted(mods))}".encode()).hexdigest()


@WEBSERVER.get("/")
@WEBSERVER.get("/game")
async def index():
    return await render_template("games.html", games=GAMES.values())


@WEBSERVER.get("/game/<string:game_id>")
async def game(game_id: str):
    token_data, token_key = _obfuscate_token(_generate_token())
    return await render_template(
        "game.html", game=_get_game(game_id), token_data=token_data, token_key=token_key
    )


@WEBSERVER.get("/game/<string:game_id>/packmod")
async def packmods(game_id: str):
    token = request.args.get("token", "")
    if not _validate_token(token):
        abort(403, "Invalid or expired token. Please go back and try again.")

    mods = request.args.getlist("mod")
    game = _get_game(game_id)
    mods_to_pack = [mod for mod in game.get_mods() if mod.id in mods]

    if not mods_to_pack:
        abort(400, "No valid mods selected to pack.")

    key = _cache_key(game_id, mods)
    cache_subdir = CACHE_DIR / key
    output_path = cache_subdir / game.out_filename

    if cache.get(key):
        return redirect(f"/cache/{key}/{game.out_filename}")

    cache_subdir.mkdir(exist_ok=True)
    result = await pack(game, output_path, mods_to_pack)

    if result.returncode != 0:
        err_msg = result.stderr.decode("utf-8") if result.stderr else "Unknown error"
        abort(500, f"Failed to pack mods: {err_msg}")

    if not output_path.exists():
        abort(500, "Pack command succeeded but output file was not created")

    cache.put(key, cache_subdir)

    return redirect(f"/cache/{key}/{game.out_filename}")
