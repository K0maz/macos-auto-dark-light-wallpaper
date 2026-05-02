#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

APR_BASE64 = "YnBsaXN0MDDSAQIDBFFsUWQQABABCA0PERMAAAAAAAABAQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAFQ=="

SWIFT_SOURCE = r'''
import Foundation
import ImageIO
import CoreGraphics
import UniformTypeIdentifiers

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

let args = CommandLine.arguments
guard args.count >= 2 else {
    fail("Usage: generator inspect <file.heic> | generator make <light> <dark> <output.heic>")
}

func loadImage(_ url: URL) -> CGImage {
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fail("Could not load image: \(url.path)")
    }
    return image
}

if args[1] == "inspect" {
    guard args.count == 3 else { fail("Usage: generator inspect <file.heic>") }
    let url = URL(fileURLWithPath: args[2])
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
        fail("Could not inspect HEIC: \(url.path)")
    }
    print("count=\(CGImageSourceGetCount(source))")
    for index in 0..<CGImageSourceGetCount(source) {
        if let image = CGImageSourceCreateImageAtIndex(source, index, nil) {
            print("frame\(index)=\(image.width)x\(image.height)")
        }
    }
    if let metadata = CGImageSourceCopyMetadataAtIndex(source, 0, nil),
       let tag = CGImageMetadataCopyTagWithPath(metadata, nil, "apple_desktop:apr" as CFString),
       let value = CGImageMetadataTagCopyValue(tag) {
        print("apr=\(value)")
    } else {
        print("apr=missing")
    }
    exit(0)
}

guard args[1] == "make", args.count == 5 else {
    fail("Usage: generator make <light> <dark> <output.heic>")
}

let lightURL = URL(fileURLWithPath: args[2])
let darkURL = URL(fileURLWithPath: args[3])
let outputURL = URL(fileURLWithPath: args[4])
let lightImage = loadImage(lightURL)
let darkImage = loadImage(darkURL)

guard lightImage.width == darkImage.width, lightImage.height == darkImage.height else {
    fail("Images must have the same dimensions.")
}

guard let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, UTType.heic.identifier as CFString, 2, nil) else {
    fail("Could not create HEIC destination: \(outputURL.path)")
}

let metadata = CGImageMetadataCreateMutable()
let namespace = "http://ns.apple.com/namespace/1.0" as CFString
let prefix = "apple_desktop" as CFString
CGImageMetadataRegisterNamespaceForPrefix(metadata, namespace, prefix, nil)
CGImageMetadataSetValueWithPath(metadata, nil, "apple_desktop:apr" as CFString, "__APR_BASE64__" as CFString)

let options: [CFString: Any] = [kCGImageDestinationLossyCompressionQuality: 0.95]
CGImageDestinationAddImageAndMetadata(destination, lightImage, metadata, options as CFDictionary)
CGImageDestinationAddImage(destination, darkImage, options as CFDictionary)

guard CGImageDestinationFinalize(destination) else {
    fail("Could not finalize HEIC file.")
}

print(outputURL.path)
'''.replace("__APR_BASE64__", APR_BASE64)


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
    source = work / "generator.swift"
    binary = work / "generator"
    source.write_text(SWIFT_SOURCE)
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
        script = f'tell application "System Events" to tell every desktop to set picture to "{output}"'
        run(["osascript", "-e", script])


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
