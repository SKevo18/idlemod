# Idlemod

An all-in-one Go command-line tool for patching & modding old game data files.

## Features

- [x] Unpacking data files;
- [x] Repacking data files;
- [x] Packing and merging multiple mods into unified data file;
- [x] A Python webserver, to patch and download modded data files on the fly;

## Supported games

- [x] Moorhuhn Kart Extra XXL (game ID: `mhk_1`/`mhk_extra`) - untested!;
- [x] Moorhuhn Kart 2 (game ID: `mhk_2`);
  - [ ] Schatzjäger (untested) (game ID: `schatzjaeger`) - note: this uses the exact same algorithm as MHK2;
- [x] Moorhuhn Kart 3 (game ID: `mhk_3`);
  - [x] TINcan Race (game ID: `tincan`, same format as `mhk_3`)
- [x] Moorhuhn Kart 4 (Thunder) (game ID: `mhk_4`/`mhk_thunder`);
- [x] Dino and Aliens (game ID: `dino_aliens`);

## Wait, what?

Moorhuhn Kart games are the games of my childhood. I've always wanted to mod them, however it seems that there are a very few enthusiasts like me who are interested in modding these games.

Later, I've randomly stumbled upon the [QuickBMS](https://aluigi.altervista.org/quickbms.htm) scripts for unpacking and repacking data files. I've quickly put a script together, which was a simple but clunky Python CLI tool for unpacking and repacking data files (back then, it was just a wrapper for the QuickBMS binary). It also included a webserver for building, merging and downloading modded data files on the fly for casual people that are not familiar with programming or CLI tools.

Then, I discovered the [Moorhuhnverse Discord server](https://discord.gg/buJ64SrHxY) which is a community of fellow Moorhuhn enthusiasts. It turns out that there are some very talented people who modded a few Moorhuhn games alrady.

By exchanging knowledge and helpful tips, I've been able to understand how the data files are structured and how to modify them (before, I had no idea how to do that, and would only plug existing tools together). As the repository grew, stacked on top of older and older code, I've decided to rewrite the whole thing in pure Go, to make it more maintainable, without the need to rely on QuickBMS scripts and Python. It has now matured into a modding tool for old games in general, not just Moorhuhn Kart.

## Downloading the binary

### Download existing mods

The [webserver](./webserver/) is a simple Python webserver, which can be used to build and download modded data files on the fly, without the need for end-users to use the command-line tool at all. See it live at [https://idlemod.svit.ac/](https://idlemod.svit.ac/).

### Download

You can obtain the latest version of the tool for your operating system from the [releases](https://github.com/SKevo18/idlemod/releases) page. They are cross-compiled for Windows, Linux and MacOS (GitHub Actions).

### Compile

If you want to compile the tool yourself, you must have Go installed on your system. Then, you can run the following command to compile the tool:

```bash
# clone the repository and `cd` to repo root, then:
go build -o build/
```

The binary for your OS will be available in the `build/` directory. You can also compile the tool and run it right away by using `go run .` in the repository root, without leaving lingering binaries around (useful for development or testing).

## Usage

This tool is designed to be used in a terminal. It's a command-line tool, and it's not meant to be used in a GUI environment. If you do not use a terminal, you can use the [webserver](./webserver/) instead to build and download existing modded data files.

However, if you want to create or contribute your own mods into the repository, you must use the command-line tool. I suggest that you get familiar with how terminal works, and how to use command-line tools in general.

The generic procedure for using the tool is as follows:

1. Download the [idlemod binary](https://github.com/SKevo18/idlemod/releases) for your operating system;
2. Unzip the downloaded file;
3. Move the binary somewhere you can execute it from. For Windows, there is not really a convention where non-MS binaries should be located. I suggest you move it to `C:\Program Files\idlemod.exe`, as `C:\Program Files\` should be in your `PATH` environment variable by default.
4. Go to the directory where the data files you want to work with are located. For example, if you want to work with Moorhuhn Kart XXL, you should go to the directory where the `mhke.dat` file is located (your game's installation directory).
5. In the file explorer, click on the top bar (where the full path is displayed), type in `cmd` and press Enter. This will open a command prompt in the current directory.
6. Now you can type in `idlemod` and press Enter. This will display the help message, confirming that the tool is working.

### Order of mods

If you are using the `packmod` command, then order of the mod paths is important. If a mod is applied after another mod, it will overwrite the changes made by the previous mod, *if they make the same change*.

In other words, if we have two mods, `wait_for_me` (that makes the AI wait for the player if they are too far ahead) and `no_rubberbanding` (that makes the AI not rubberband), and we want to apply them both, doing something like:

```bash
idlemod packmod mhk_1 mods/mhk_1/no_rubberbanding mods/mhk_1/wait_for_me
```

will result in a `mhk_1.dat` file that has the changes from both mods applied (because `no_rubberbanding` also modifies the speed of AI that is too far ahead, not just behind where they now go slower compared to the base game). If you swap the order of the mods like this:

```bash
idlemod packmod mhk_1 mods/mhk_1/wait_for_me mods/mhk_1/no_rubberbanding
```

...then the changes from the second mod (`no_rubberbanding`) will overwrite the changes from the first mod (`wait_for_me`), as the latter only modifies the speed of AI that is too far ahead, but this is also modified (overwritten) by `no_rubberbanding`. So, only the changes from `no_rubberbanding` will be applied, and the feature from `wait_for_me` will be lost (as if you didn't even apply the mod).

Sometimes, this can be confusing, but since this tool does not handle merge conflicts, it's the best system we can have. Just remember that mods in the CLI are applied from left to right, so mods on the right will overwrite mods on left (that is, only if they modify the same lines in their patches, or the `source` directory contains the same files).

Also, if you are developing mods, try to use the patches as much as possible and avoid modifying many lines or files in a single mod, to ensure that they can be properly combined in a variety of ways that preserve their characteristics.

## FaQ

### What data files are you talking about?

Many old games use a special data file format, which contains all the game assets, such as textures, models, sounds, configuration files, etc. The data files are often present in your game directory, and have the `.dat` (for example, Moorhuhn Kart 1 and 2) or `.sar` (Moorhuhn Kart 3 and Moorhuhn Kart: Thunder) extension.

These data files are packed with a custom compression algorithm, and are not directly readable by any standard tools. That's why a special tool is needed to unpack and repack them, which is what this repository is all about.

### What can I do with the tool?

While this tool is not a full-fledged modding suite (e. g.: it doesn't include a GUI level or game model editor, etc. - you have to use external tools for that), it provides the basic functionality to unpack and repack data files, and to merge multiple mods into a single data file, while attempting to preserve unique changes made by each mod.

Some games allow you to add new assets, such as models or textures (if the game was programmed to support that), but often you just want to modify the existing assets. For example, you can replace the textures of the game characters, modify existing levels/tracks or modify the configuration files to change the game behavior.

The tools aims to simplify this process as much as possible, and to provide a simple way to share mods with others. It also includes a webserver, which can be used to build and download modded data files on the fly, without the need for end-users to use the command-line tool at all.

### What is the gopatch format about?

It's a custom format I have developed for the purpose of patching and joining multiple modded files together in an unified way that doesn't make mods overwrite each others' changes. Please, see [this repository](https://github.com/SKevo18/gopatch) for more information.

## Credits

This tool wouldn't be possible without the help of a few talented humans! I'd like to thank the following people for their incredible help towards making this tool a reality:

- **Luigi Auriemma**, for creating the original QuickBMS tool that sparked my interest in (mainly Moorhuhn Kart) modding and gave me hope that it's possible to do it;
- **pyramidensurfer**, for their incredible dedication towards understanding the Moorhuhn data file format, and for providing example code and tools to work with the data files;
- **Blue Cap guy**, for their valuable insights and feedback on the tool;
- The entire **Moorhuhnverse Discord community** and other fellow Moorhuhn enthusiasts, for preserving the interest in Moorhuhn games;
- **...and you, for being invested in this project enough to read this far!**

Thank you all very much!
