import hashlib

from pathlib import Path
from tempfile import gettempdir

from quart import Quart, abort, render_template, request, send_file
from cache import FileCache
from modder import GAMES, pack


WEBSERVER = Quart(__name__)
CACHE_DIR = Path(gettempdir()) / "idlemod_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

cache = FileCache(CACHE_DIR, max_entries=10, max_age_seconds=3600)


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
    return await render_template("game.html", game=_get_game(game_id))


@WEBSERVER.get("/game/<string:game_id>/packmod")
async def packmods(game_id: str):
    mods = request.args.getlist("mod")
    game = _get_game(game_id)
    mods_to_pack = [mod for mod in game.get_mods() if mod.id in mods]

    if not mods_to_pack:
        abort(400, "No valid mods selected to pack.")

    key = _cache_key(game_id, mods)
    cached_path = cache.get(key)

    if cached_path:
        return await send_file(
            cached_path,
            as_attachment=True,
            mimetype="application/octet-stream",
            attachment_filename=game.out_filename,
        )

    output_path = CACHE_DIR / f"{key}{game.original_datafile.suffix}"
    result = await pack(game, output_path, mods_to_pack)

    if result.returncode != 0:
        err_msg = result.stderr.decode("utf-8") if result.stderr else "Unknown error"
        abort(500, f"Failed to pack mods: {err_msg}")

    if not output_path.exists():
        abort(500, "Pack command succeeded but output file was not created")

    cache.put(key, output_path)

    return await send_file(
        output_path,
        as_attachment=True,
        mimetype="application/octet-stream",
        attachment_filename=game.out_filename,
    )
