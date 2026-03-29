# ShadowSIP

**Universal Open-Source SIP Softphone**

A cross-platform SIP softphone built with **PJSIP** + **PySide6 (Qt)**. Audio, video, chat — all in one lightweight, native application.

Companion client for [ShadowPBX](https://github.com/dhirendralive9/shadowpbx).

## Features (Phase 1)

- SIP registration to any standard SIP server
- Audio calls (make/receive) with G.711, G.722, Opus codecs
- Dial pad with DTMF
- Call hold, transfer, recording
- BLF extension monitoring
- Call history
- Light/Dark theme toggle
- System tray integration
- Multi-account support

## Stack

| Layer | Technology |
|-------|-----------|
| SIP/Media | PJSIP 2.14+ (pjsua2 Python bindings) |
| UI | PySide6 (Qt 6, LGPL) |
| Language | Python 3.10+ |
| Packaging | PyInstaller |
| Config | INI file + SQLite |

## Quick Start

### 1. Install dependencies

```bash
# Ubuntu
sudo apt install python3-dev python3-pip python3-venv build-essential swig \
  libasound2-dev libpulse-dev libssl-dev libsrtp2-dev libopus-dev

# Windows
# Install Visual Studio Build Tools, Python 3.10+, SWIG
```

### 2. Build PJSIP (required once)

```bash
# Linux
chmod +x scripts/build_pjsip_linux.sh
./scripts/build_pjsip_linux.sh

# Windows (run from VS Developer Command Prompt)
scripts\build_pjsip_windows.bat
```

### 3. Install & Run

```bash
pip install PySide6
pip install -e .
shadowsip
```

### 4. Package for distribution

```bash
pip install pyinstaller
python scripts/package.py
# Output: dist/ShadowSIP/
```

## Project Structure

```
shadowsip/
├── src/shadowsip/
│   ├── main.py              # Entry point
│   ├── app.py               # App controller, theme management
│   ├── core/                # SIP engine, call control, audio
│   ├── ui/                  # PySide6 widgets
│   │   ├── main_window.py   # Sidebar + content layout
│   │   ├── dialer.py        # Dial pad, extensions, call history
│   │   └── tray_icon.py     # System tray
│   ├── db/                  # SQLite storage
│   └── utils/               # Config, logging, platform helpers
├── resources/
│   ├── icons/               # App icons
│   ├── themes/              # light.qss, dark.qss
│   └── ringtones/           # Default ringtones
├── scripts/
│   ├── build_pjsip_linux.sh
│   ├── build_pjsip_windows.bat
│   └── package.py
├── tests/
├── shadowsip.spec           # PyInstaller config
└── requirements.txt
```

## Themes

ShadowSIP ships with two themes:

- **Aether Light** — Warm cream, DM Sans font, green accent
- **Slate Pro Dark** — Deep slate, Plus Jakarta Sans, teal accent with glow

Toggle via the sidebar sun/moon button or Settings.

## Roadmap

- [x] Phase 1.1 — Project setup & build system
- [ ] Phase 1.2 — SIP account management
- [ ] Phase 1.3 — Audio call engine
- [ ] Phase 2 — Conference, presence, NAT, encryption
- [ ] Phase 3 — Video calling + screen sharing
- [ ] Phase 4 — Chat + ShadowPBX integration
- [ ] Phase 5 — Auto-provisioning, CRM, i18n
- [ ] Phase 6 — v1.0 release

## License

GPL-3.0 — Free and open source.
