from __future__ import annotations

import asyncio
import orjson

from asyncio.subprocess import create_subprocess_shell
from dataclasses import dataclass, field
from os import name as os_name
from pathlib import Path

MODS_ROOT = Path(__file__).parent.parent / "mods"
DATAFILE_ROOT = Path(__file__).parent.parent / "data"
IDLEMOD_BINARY = (
    Path(__file__).parent.parent
    / "build"
    / ("idlemod.exe" if os_name == "nt" else "idlemod")
)


@dataclass
class Game:
    id: str
    name: str
    original_datafile: Path
    mods_folder: Path | None = None
    out_filename: str | None = None
    mods: list[Mod] = field(default_factory=list)

    def __post_init__(self):
        if self.mods_folder is None:
            self.mods_folder = MODS_ROOT / self.id
        if self.out_filename is None:
            self.out_filename = self.original_datafile.name
        self._load_mods()

    def _load_mods(self):
        if not self.mods_folder or not self.mods_folder.exists():
            return

        self.mods = [
            Mod(id=path.stem, game=self, path=path)
            for path in self.mods_folder.iterdir()
            if path.is_dir()
        ]

    def get_mods(self) -> list[Mod]:
        return self.mods


@dataclass
class Mod:
    id: str
    game: Game
    path: Path
    readme: str | None = None
    config: dict | None = None

    def __post_init__(self):
        readme_path = self.path / "README.md"
        if readme_path.exists():
            self.readme = readme_path.read_text()

        config_path = self.path / "config.json"
        if config_path.exists():
            self.config = orjson.loads(config_path.read_bytes())


@dataclass
class CommandResult:
    stdout: bytes
    stderr: bytes
    returncode: int | None


async def run_cmd(cmd: str) -> CommandResult:
    process = await create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await process.communicate()
    return CommandResult(stdout=out, stderr=err, returncode=process.returncode)


async def pack(game: Game, output_path: Path, mods: list[Mod]) -> CommandResult:
    game_id = game.id.split(".", 1)[0]
    mod_paths = " ".join(f'"{mod.path}"' for mod in mods)
    cmd = f'"{IDLEMOD_BINARY}" packmod {game_id} "{game.original_datafile}" "{output_path}" {mod_paths}'
    return await run_cmd(cmd)


GAMES = {
    "mhk_1": Game(
        id="mhk_1",
        name="Moorhuhn Kart: Extra (XXL)",
        out_filename="mhke.dat",
        original_datafile=DATAFILE_ROOT / "mhk_1.dat",
    ),
    "mhk_2.en": Game(
        id="mhk_2.en",
        name="Moorhuhn Kart 2 (English)",
        original_datafile=DATAFILE_ROOT / "mhk_2.en.dat",
        out_filename="mhk2-00.dat",
        mods_folder=MODS_ROOT / "mhk_2",
    ),
    "mhk_2.de": Game(
        id="mhk_2.de",
        name="Moorhuhn Kart 2 (German)",
        original_datafile=DATAFILE_ROOT / "mhk_2.de.dat",
        out_filename="mhk2-00.dat",
        mods_folder=MODS_ROOT / "mhk_2",
    ),
    "mhk_3": Game(
        id="mhk_3",
        name="Moorhuhn Kart 3",
        out_filename="data.sar",
        original_datafile=DATAFILE_ROOT / "mhk_3.sar",
    ),
    "mhk_4": Game(
        id="mhk_4",
        name="Moorhuhn Kart: Thunder",
        out_filename="data.sar",
        original_datafile=DATAFILE_ROOT / "mhk_4.sar",
    ),
}
