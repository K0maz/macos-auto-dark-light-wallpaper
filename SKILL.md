---
name: make-macos-appearance-wallpaper
description: Create macOS appearance-aware HEIC wallpapers from paired light and dark images. Use when the user asks to make a Mac wallpaper that switches with Light Mode, Dark Mode, Auto appearance, or asks to fix a custom HEIC that appears as photo shuffle instead of showing the Automatic/Light/Dark wallpaper option.
---

# Make macOS Appearance Wallpaper

## Workflow

Use `scripts/make_macos_appearance_wallpaper.py` whenever possible. It encodes the fragile part correctly: a two-frame HEIC with first frame = light, second frame = dark, and `apple_desktop:apr` set to a valid binary-plist base64 for `{"l": 0, "d": 1}`.

```bash
python3 /path/to/skill/scripts/make_macos_appearance_wallpaper.py \
  --light /path/to/light.png \
  --dark /path/to/dark.jpg \
  --output /path/to/name.heic
```

Add `--set-wallpaper` only when the user wants the current desktop changed. On recent macOS versions, directly setting the HEIC as an `imageFile` is what makes System Settings show the appearance popup, such as `Automatic`. Adding the file through the Photos/Your Photos picker can make macOS treat the two HEIC frames as a photo shuffle instead.

## Important Details

- Keep light as frame 0 and dark as frame 1.
- If source dimensions differ but aspect ratio matches, resize the dark image to the light image size unless the user requested a specific target size.
- The `apple_desktop:apr` value must be valid plist data. Do not use the older copied string `YnBsaXN0MDDSAQMC...`; it can decode as an invalid binary plist and be ignored.
- The known-good value for light index 0, dark index 1 is:

```text
YnBsaXN0MDDSAQIDBFFsUWQQABABCA0PERMAAAAAAAABAQAAAAAAAAAFAAAAAAAAAAAAAAAAAAAAFQ==
```

## Validation

After generation, verify:

```bash
sips -g pixelWidth -g pixelHeight /path/to/name.heic
python3 /path/to/skill/scripts/make_macos_appearance_wallpaper.py --inspect /path/to/name.heic
```

Expected inspection output includes `count=2` and `apr=YnBsa...AAAFQ==`.

If HEIC finalization fails in Codex with an IOSurface or sandbox error, rerun the same script with escalated permissions. The system HEIC encoder may need to run outside the sandbox.
