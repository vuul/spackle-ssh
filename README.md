# Spackle 2.0

A lightweight SSH/Telnet client for macOS and Linux, providing a GUI for managing and launching terminal sessions.

## Features

- **SSH and Telnet** connections with saved session profiles
- **Native Terminal.app** integration on macOS (xterm on Linux)
- **Session management** - save, load, and delete connection profiles
- **Terminal customization** - foreground/background colors, font size, geometry (80x24, 80x43, 132x24, 132x43), and scrollback lines
- **SSH key support** - use the default key (~/.ssh/id_rsa or ~/.ssh/id_dsa) or specify a custom path
- **User@host parsing** - enter `user@hostname` or just a hostname (defaults to current user)
- **Connection validation** - DNS lookup before launching
- **macOS** - Shell runs `exit` after the SSH/telnet session ends

## Requirements

- Python 3.6+
- tkinter (included with most Python installations)
- ssh (pre-installed on macOS and most Linux distributions)
- telnet (optional; install on macOS with `brew install telnet`)
- xterm (Linux only)

## Quick Start

```bash
python3 spackle.py
```

If tkinter is not installed, the app will exit with a platform-specific install command. For example:

| Platform | Command |
|----------|---------|
| macOS | `brew install python-tk` |
| Debian/Ubuntu | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |

## Usage

1. Enter a hostname or IP address (optionally as `user@host`)
2. Set the port (defaults to 22 for SSH, 23 for Telnet)
3. Select the protocol (SSH or Telnet)
4. Click **Open** or press Enter to connect

### Saving Sessions

1. Fill in the connection details
2. Enter a name in the **Saved Session Name** field
3. Click **Save**

### Connection Properties

Click **Options** to configure:

- **SSH private key** - default or custom path
- **Terminal colors** - foreground and background
- **Terminal size** - 80x24, 80x43, 132x24, or 132x43
- **Font size** - 6 to 20 points
- **Scrollback lines** - 0 to 20,000

Click **Save as default** to persist your preferences across new sessions.

## Session Storage

Sessions are stored in `~/.spackle_2.0` using a Java-compatible properties format. This file is created automatically on first launch.

## Linux Installation

Install Spackle as a desktop application for the current user (no sudo required):

```bash
./install_linux.sh
```

This installs to `~/.local/`:
- `~/.local/bin/spackle` — the application
- `~/.local/share/icons/spackle.png` — the icon
- `~/.local/share/applications/spackle.desktop` — the GNOME launcher

The script checks for required dependencies (python3, tkinter, xterm) and provides install commands if any are missing.

## Building the macOS App Bundle

You can package Spackle as a standalone macOS `.app` using py2app:

```bash
./build_macos_app.sh
```

This creates `dist/Spackle.app`.

## Project Structure

```
spackle-ssh/
├── spackle.py           # Application source
├── build_macos_app.sh   # macOS .app build script (py2app)
├── install_linux.sh     # Linux install script (~/.local/)
├── spackle.desktop      # Freedesktop .desktop launcher template
├── setup.py             # py2app build configuration
├── src/spackle/resources/
│   └── Spackle-icon.png # Application icon
└── README.md
```

## History

Spackle was originally created as a Java Swing application to provide a cross-platform PuTTY alternative for macOS and Linux. Version 2.0 is a complete rewrite in Python using tkinter, replacing the xterm dependency on macOS with native Terminal.app integration via AppleScript.
