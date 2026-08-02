# Simple Switching

A browser extension for switching through tabs in MRU (most recently used) order, with a cross-platform enterprise policy installer for managed deployments.

## Why?

I always had the urge to switch tabs in most recently used order. That is faster than grouping tabs myself and saves time.

The problems I was constantly having with other similar extensions were:
1. No native Ctrl+Tab shortcut override (even if it's a Chromium's limitation)
2. Not open-source
3. Dependency on Chrome Web Store

So, I decided to make my own implementation that fixes these issues.

## What this repository includes

Simple Switching consists of two parts:

**Browser Extension** - A lightweight extension that lets you cycle through tabs in most recently used order.

**Enterprise Installer** - A user friendly tool that deploys the extension via browser enterprise policies. It discovers installed browsers and profiles automatically, lets you select which ones to target, and handles provisioning. Overrides Chromium's Ctrl+Tab shortcut by default.

## Features

- **MRU Tab Cycling** - Switch tabs by recent usage order, per window
- **Cross-Browser Support** - Has presets for Chrome, Edge, Brave and Vivaldi (new browser versions might require tweaks within installer/config/config.json, not every browser and platform is guaranteed to work)
- **Enterprise Policy Deployment** - Force-installs extension via native browser management systems
- **Automatic Profile Discovery** - Scans filesystem for browser profiles with valid Preferences files
- **Shortcut Injection** - Configures the keyboard shortcut directly in browser Preferences
- **Flexible Distribution** - Downloads from GitHub Releases or uses a local .crx file
- **Clean Uninstall** - Removes policies and extension directories

## How It Works

### Extension

The extension runs as a background service worker. When you activate a tab, it moves that tab to the front of the window's history. New tabs are added as the second item. When you trigger the cycle command, the current history is frozen and you step through it with each press. After a short delay (230ms), the final selection is committed back to the actual history.

### Installer

The installer reads a configuration file defining supported browsers and their platform-specific paths. On launch it scans each browser's profile folders containing a valid Preferences file. You select profiles in the TUI, then the installer:

1. Downloads the extension .crx (or uses a local file)
2. Deploys enterprise policies to force-install the extension with an update URL
3. Injects the shortcut keybinding into each profile's Preferences
4. Serves the .crx and update manifest locally for policy consumption

On Windows it writes to Registry. On macOS it writes to /Library/Preferences. On Linux it uses pkexec to write JSON policy files to managed directories. Windows and macOS requires admin/root rights elevation.

## Build Instructions

### Extension

**nektos/act build (GH actions local runner)**

```bash
# Windows Powershell
act workflow_dispatch -j build-extension --secret CRX_PRIVATE_KEY="$(Get-Content -Raw C:\path\to\your\key.pem)"

# Linux/macOS
act workflow_dispatch -j build-extension --secret CRX_PRIVATE_KEY="$(cat /path/to/your/key.pem)"
```

**npm build**

> NOTE: Make sure to have Node >=26 with npm installed

```bash
cd extension

npm install
npm run build

# Generate a key
openssl genrsa -out key.pem 2048

npx crx3 -p ./key.pem -o ./build/extension.crx ./dist
```

You will find built files within the root `build/` folder

### Installer

**nektos/act build (GH actions local runner)**

> NOTE: Only Linux builds currently working

```bash
act workflow_dispatch -j build-extension
```

**Python PyInstaller builds**
> NOTE: Make sure to have Python >=3.11 with pip, as well as pyinstaller installed

```bash
cd installer

# Windows
python -m PyInstaller --onefile --paths . --name="ssi-cli.exe" --add-data "config;config" --add-data "shells/cli/assets;assets" shells/cli/app.py

# Linux/macOS
python -m PyInstaller --onefile --paths . --name="ssi-cli" --add-data "config:config" --add-data "shells/cli/assets:assets" shells/cli/app.py
```

You will find built files within the root `build/` folder

## Configuration

The installer pre-build is configured via `installer/config/config.json`. It defines:

- Extension filename and download source (Download vendor, repo, tag, or direct URL)
- Supported browsers with display names and platform-specific paths:
  - Config directory (where profiles live)
  - Executable names (for PATH lookup)
  - Policy keys (Windows Registry path, macOS bundle ID, Linux policy directory)
- Shortcut mappings per platform (Windows, macOS, Linux)

## Architecture

```
simple-switching/
├── extension/                    # Browser Extension (TypeScript + Vite)
│   ├── src/
│   │   ├── background.ts        # Service worker, event listeners
│   │   ├── cycle.ts             # MRU cycling logic, frozen history
│   │   ├── history.ts           # Per-window tab history management
│   │   ├── config.ts            # Constants (CYCLE_DELAY_MS)
│   │   └── manifest.json        # MV3/MV2 template
│   ├── public/icon/             # Extension icons
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── installer/                     # Enterprise Policy Installer (Python + Textual)
│   ├── core/
│   │   ├── config_loader.py       # Loads config.json into typed models
│   │   ├── discovery.py           # Filesystem profile scanner
│   │   ├── models.py              # Dataclasses (AppConfig, BrowserProfile)
│   │   ├── policy_installer.py    # Cross-platform policy deployment
│   │   ├── preferences_editor.py  # Shortcut injection into Preferences
│   │   ├── uninstaller.py         # Policy/shortcut/extension cleanup
│   │   ├── local_server.py        # Local HTTP server for .crx + update XML
│   │   ├── download/              # Download vendors (GitHub, custom URL)
│   │   └── process_manager.py
│   ├── shells/cli/                # Textual TUI Application
│   │   ├── app.py                 # Main app controller, screen routing
│   │   ├── screens/               # Welcome, Selector, Progress, Finish
│   │   └── assets/style.css       # TUI styling
│   ├── config/config.json         # Browser definitions & settings
│   └── pyproject.toml
│
├── .github/workflows/             # CI/CD pipelines
│   ├── build-extension.yaml
│   └── build-cli.yaml
│
├── LICENSE                        # Apache-2.0
└── README.md
```

## Support

For issues, feature requests, or questions, open an issue or pull request on GitHub.

---

_Open source, as intended._
