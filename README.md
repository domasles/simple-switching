# simple-switching
A browser extension for switching through tabs in MRU (most recently used) order

## Local Build Instructions

For extension:
```bash
# Act build (GH actions local runner)
act workflow_dispatch -j build-extension --secret CRX_PRIVATE_KEY="$(cat /path/to/your/key.pem)"
```

For installers:
```bash
# Act build (GH actions local runner, only Linux builds currently working)
act workflow_dispatch -j build-extension

# Python PyInstaller builds
# Make sure to have Python >=3.11 with pip, as well as pyinstaller, textual, requests and psutil installed (through pip)

# Windows
python -m PyInstaller --onefile --paths . --name="ssi-cli-windows.exe" --add-data "config;config" --add-data "shells/cli/assets;assets" shells/cli/app.py

# Linux
python -m PyInstaller --onefile --paths . --name="ssi-cli-linux" --add-data "config:config" --add-data "shells/cli/assets:assets" shells/cli/app.py

# macOS
python -m PyInstaller --onefile --paths . --name="ssi-cli-macos" --add-data "config:config" --add-data "shells/cli/assets:assets" shells/cli/app.py
```
