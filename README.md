# Make macOS Appearance Wallpaper Skill

Create macOS appearance-aware HEIC wallpapers from paired light and dark images.

The skill wraps the fragile part of this workflow in a reusable script:

- create a two-frame HEIC where frame 0 is light mode and frame 1 is dark mode
- write the `apple_desktop:apr` metadata that macOS uses for Light/Dark/Automatic wallpapers
- optionally set the generated HEIC as the current desktop wallpaper

## Install

After this repository is public on GitHub:

```bash
npx skills add K0maz/macos-auto-dark-light-wallpaper
```

To install only this skill when adding from a larger repository:

```bash
npx skills add K0maz/macos-auto-dark-light-wallpaper --skill make-macos-appearance-wallpaper
```

## Use Directly

```bash
python3 scripts/make_macos_appearance_wallpaper.py \
  --light /path/to/light.png \
  --dark /path/to/dark.jpg \
  --output /path/to/wallpaper.heic
```

Inspect the generated HEIC:

```bash
python3 scripts/make_macos_appearance_wallpaper.py --inspect /path/to/wallpaper.heic
```

Expected inspection output includes `count=2` and an `apr=` value.

## Requirements

- macOS
- `python3`
- `swiftc`
- `sips`

These are available on a normal macOS developer machine with Xcode Command Line Tools installed.
