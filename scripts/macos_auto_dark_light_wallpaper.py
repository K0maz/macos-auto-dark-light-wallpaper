#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(cmd, *, env=None):
    subprocess.run(cmd, check=True, env=env)


def sips_dimensions(path: Path):
    proc = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        check=True,
        text=True,
        capture_output=True,
    )
    width = height = None
    for line in proc.stdout.splitlines():
        if "pixelWidth:" in line:
            width = int(line.rsplit(":", 1)[1].strip())
        if "pixelHeight:" in line:
            height = int(line.rsplit(":", 1)[1].strip())
    if not width or not height:
        raise RuntimeError(f"Could not read dimensions for {path}")
    return width, height


def compile_generator(work: Path):
    source = Path(__file__).resolve().with_name("generator.swift")
    binary = work / "generator"
    env = os.environ.copy()
    env["CLANG_MODULE_CACHE_PATH"] = str(work / "module-cache")
    env["TMPDIR"] = str(work / "tmp")
    (work / "module-cache").mkdir(parents=True, exist_ok=True)
    (work / "tmp").mkdir(parents=True, exist_ok=True)
    run(["swiftc", str(source), "-o", str(binary)], env=env)
    return binary, env


def inspect(path: Path):
    with tempfile.TemporaryDirectory() as td:
        binary, env = compile_generator(Path(td))
        run([str(binary), "inspect", str(path)], env=env)


def make(args):
    light = Path(args.light).expanduser().resolve()
    dark = Path(args.dark).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    lw, lh = sips_dimensions(light)
    dw, dh = sips_dimensions(dark)

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        prepared_light = work / f"light{light.suffix or '.png'}"
        prepared_dark = work / f"dark{dark.suffix or '.jpg'}"
        shutil.copy2(light, prepared_light)

        if (lw, lh) == (dw, dh):
            shutil.copy2(dark, prepared_dark)
        else:
            run(["sips", "-z", str(lh), str(lw), str(dark), "--out", str(prepared_dark)])

        binary, env = compile_generator(work)
        run([str(binary), "make", str(prepared_light), str(prepared_dark), str(output)], env=env)

    if args.set_wallpaper:
        run(
            [
                "osascript",
                "-e",
                "on run argv",
                "-e",
                "set imagePath to item 1 of argv",
                "-e",
                'tell application "System Events" to tell every desktop to set picture to imagePath',
                "-e",
                "end run",
                str(output),
            ]
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--light")
    parser.add_argument("--dark")
    parser.add_argument("--output")
    parser.add_argument("--set-wallpaper", action="store_true")
    parser.add_argument("--inspect")
    args = parser.parse_args()

    if args.inspect:
        inspect(Path(args.inspect).expanduser().resolve())
        return

    if not args.light or not args.dark or not args.output:
        parser.error("--light, --dark, and --output are required unless --inspect is used")
    make(args)


if __name__ == "__main__":
    main()
