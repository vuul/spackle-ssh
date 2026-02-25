#!/usr/bin/env python3
"""
Spackle - A Python-based SSH/Telnet client for Mac and Linux.
Requires ssh and telnet to be installed on the system.
Uses native Terminal.app on macOS; falls back to xterm on Linux.

Author: vuul
"""

import os
import sys
import socket
import ssl
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, colorchooser, filedialog
except ImportError:
    print("Error: tkinter is not installed.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Install it for your platform:", file=sys.stderr)
    if sys.platform == "darwin":
        print("  brew install python-tk", file=sys.stderr)
    elif shutil.which("apt"):
        print("  sudo apt install python3-tk", file=sys.stderr)
    elif shutil.which("dnf"):
        print("  sudo dnf install python3-tkinter", file=sys.stderr)
    else:
        print("  macOS:   brew install python-tk", file=sys.stderr)
        print("  Debian:  sudo apt install python3-tk", file=sys.stderr)
        print("  Fedora:  sudo dnf install python3-tkinter", file=sys.stderr)
    sys.exit(1)

# Application constants
APP_NAME = "Spackle"
APP_VERSION = "2.0"
APP_VENDOR = "TCM"
APP_HOMEPAGE = "https://github.com/vuul/spackle-ssh"
APP_DESCRIPTION = (
    "A Python based version of the popular PuTTY, but for Mac and Linux."
)
PREFS_FILE = os.path.join(str(Path.home()), ".spackle_2.0")


class SortedProperties:
    """A simple Java-style properties file handler with sorted keys.
    Maintains backward compatibility with the original Java properties file format."""

    def __init__(self):
        self._props = {}

    def get(self, key, default=None):
        return self._props.get(key, default)

    def set(self, key, value):
        self._props[key] = str(value)

    def remove(self, key):
        self._props.pop(key, None)

    def property_names(self):
        return sorted(self._props.keys())

    def load(self, filepath):
        """Load properties from a Java-style properties file."""
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        self._props[key.strip()] = value.strip()
        except FileNotFoundError:
            pass

    def store(self, filepath):
        """Save properties to a Java-style properties file."""
        with open(filepath, "w") as f:
            f.write(f"#\n#{datetime.now()}\n")
            for key in sorted(self._props.keys()):
                f.write(f"{key}={self._props[key]}\n")


class ConnectionProperties(tk.Toplevel):
    """Connection properties/options dialog window."""

    DEFAULT_KEY_PATH = ""
    DEFAULT_BACKGROUND = "#ffffff"
    DEFAULT_FOREGROUND = "#000000"
    DEFAULT_SCROLLBACK = 10000
    DEFAULT_FONT_SIZE = 10
    GEOMETRY_OPTIONS = ["80x24", "80x43", "132x24", "132x43"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Connection Properties")
        self.resizable(False, False)
        self.transient(parent)

        self._bg_color = self.DEFAULT_BACKGROUND
        self._fg_color = self.DEFAULT_FOREGROUND
        self._key_path = self.DEFAULT_KEY_PATH
        self._geometry_var = tk.StringVar(value=self.GEOMETRY_OPTIONS[0])
        self._scrollback_var = tk.IntVar(value=self.DEFAULT_SCROLLBACK)
        self._fontsize_var = tk.IntVar(value=self.DEFAULT_FONT_SIZE)
        self._key_choice = tk.StringVar(value="default")
        self._save_default_callback = None

        self._build_ui()
        self.withdraw()  # Start hidden

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Main options frame
        options_frame = ttk.LabelFrame(self, text="Spackle Options", padding=10)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- SSH Key section ---
        key_frame = ttk.LabelFrame(
            options_frame, text="SSH private key", padding=5
        )
        key_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(
            key_frame,
            text="Default (~/.ssh/id_rsa or ~/.ssh/id_dsa)",
            variable=self._key_choice,
            value="default",
            command=self._on_default_key,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            key_frame,
            text="Other",
            variable=self._key_choice,
            value="other",
            command=self._on_other_key,
        ).pack(anchor=tk.W)

        key_path_frame = ttk.Frame(key_frame)
        key_path_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(key_path_frame, text="Selected Key:").pack(side=tk.LEFT)
        self._key_entry = ttk.Entry(key_path_frame, state="readonly")
        self._key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # --- Colors section ---
        colors_frame = ttk.LabelFrame(
            options_frame, text="Terminal Colors", padding=5
        )
        colors_frame.pack(fill=tk.X, pady=(0, 10))

        color_row = ttk.Frame(colors_frame)
        color_row.pack(fill=tk.X)

        ttk.Label(color_row, text="Foreground:").pack(side=tk.LEFT)
        self._fg_label = tk.Label(
            color_row,
            width=5,
            height=2,
            bg=self._fg_color,
            relief=tk.SOLID,
            borderwidth=2,
        )
        self._fg_label.pack(side=tk.LEFT, padx=5)
        self._fg_label.bind("<Button-1>", self._choose_foreground)

        ttk.Label(color_row, text="Background:").pack(
            side=tk.LEFT, padx=(20, 0)
        )
        self._bg_label = tk.Label(
            color_row,
            width=5,
            height=2,
            bg=self._bg_color,
            relief=tk.SOLID,
            borderwidth=2,
        )
        self._bg_label.pack(side=tk.LEFT, padx=5)
        self._bg_label.bind("<Button-1>", self._choose_background)

        # --- Size and Font row ---
        size_font_row = ttk.Frame(options_frame)
        size_font_row.pack(fill=tk.X, pady=(0, 10))

        # Terminal size
        size_frame = ttk.LabelFrame(
            size_font_row, text="Terminal Size", padding=5
        )
        size_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        for i, geo in enumerate(self.GEOMETRY_OPTIONS):
            row = i // 2
            col = i % 2
            ttk.Radiobutton(
                size_frame, text=geo, variable=self._geometry_var, value=geo
            ).grid(row=row, column=col, sticky=tk.W, padx=5)

        # Font size
        font_frame = ttk.LabelFrame(
            size_font_row, text="Font size", padding=5
        )
        font_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self._font_spinner = tk.Spinbox(
            font_frame,
            from_=6,
            to=20,
            width=5,
            textvariable=self._fontsize_var,
            justify=tk.RIGHT,
        )
        self._font_spinner.pack(pady=10)

        # --- Scrollback and Save-as-default row ---
        scroll_row = ttk.Frame(options_frame)
        scroll_row.pack(fill=tk.X, pady=(0, 10))

        scroll_frame = ttk.LabelFrame(
            scroll_row, text="Scrollback lines", padding=5
        )
        scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self._scroll_spinner = tk.Spinbox(
            scroll_frame,
            from_=0,
            to=20000,
            width=8,
            textvariable=self._scrollback_var,
            justify=tk.RIGHT,
        )
        self._scroll_spinner.pack(pady=10)

        right_col = ttk.Frame(scroll_row)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Button(
            right_col, text="Save as default", command=self._save_as_default
        ).pack(pady=(15, 5))

        # --- Bottom buttons ---
        btn_frame = ttk.Frame(options_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="Reset", command=self._reset).pack(
            side=tk.LEFT
        )
        ttk.Button(btn_frame, text="Close", command=self._on_close).pack(
            side=tk.RIGHT
        )

    # --- Event handlers ---

    def _on_close(self):
        self.withdraw()

    def _on_default_key(self):
        self._key_path = ""
        self._key_entry.configure(state="normal")
        self._key_entry.delete(0, tk.END)
        self._key_entry.configure(state="readonly")

    def _on_other_key(self):
        filepath = filedialog.askopenfilename(
            title="Select SSH private key"
        )
        if filepath:
            self._key_path = filepath
            self._key_entry.configure(state="normal")
            self._key_entry.delete(0, tk.END)
            self._key_entry.insert(0, filepath)
            self._key_entry.configure(state="readonly")
        else:
            self._key_choice.set("default")

    def _choose_foreground(self, event=None):
        color = colorchooser.askcolor(
            color=self._fg_color, title="Choose foreground color"
        )
        if color[1]:
            self._fg_color = color[1]
            self._fg_label.configure(bg=self._fg_color)

    def _choose_background(self, event=None):
        color = colorchooser.askcolor(
            color=self._bg_color, title="Choose background color"
        )
        if color[1]:
            self._bg_color = color[1]
            self._bg_label.configure(bg=self._bg_color)

    def _reset(self):
        self._key_choice.set("default")
        self._key_path = self.DEFAULT_KEY_PATH
        self._key_entry.configure(state="normal")
        self._key_entry.delete(0, tk.END)
        self._key_entry.configure(state="readonly")
        self._fg_color = self.DEFAULT_FOREGROUND
        self._fg_label.configure(bg=self._fg_color)
        self._bg_color = self.DEFAULT_BACKGROUND
        self._bg_label.configure(bg=self._bg_color)
        self._geometry_var.set(self.GEOMETRY_OPTIONS[0])
        self._scrollback_var.set(self.DEFAULT_SCROLLBACK)
        self._fontsize_var.set(self.DEFAULT_FONT_SIZE)

    def _save_as_default(self):
        if self._save_default_callback:
            self._save_default_callback()

    # --- Public API ---

    def set_save_default_callback(self, callback):
        self._save_default_callback = callback

    def get_terminal_background_color(self):
        return self._bg_color

    def get_terminal_foreground_color(self):
        return self._fg_color

    def set_terminal_background_color(self, color):
        self._bg_color = color
        self._bg_label.configure(bg=color)

    def set_terminal_foreground_color(self, color):
        self._fg_color = color
        self._fg_label.configure(bg=color)

    def get_geometry(self):
        return self._geometry_var.get()

    def set_geometry(self, geo):
        if geo in self.GEOMETRY_OPTIONS:
            self._geometry_var.set(geo)
        else:
            self._geometry_var.set(self.GEOMETRY_OPTIONS[0])

    def get_scrollback_lines(self):
        return str(self._scrollback_var.get())

    def set_scrollback_lines(self, lines):
        try:
            self._scrollback_var.set(int(lines))
        except (ValueError, TypeError):
            self._scrollback_var.set(self.DEFAULT_SCROLLBACK)

    def get_font_size(self):
        return str(self._fontsize_var.get())

    def set_font_size(self, size):
        try:
            self._fontsize_var.set(int(size))
        except (ValueError, TypeError):
            self._fontsize_var.set(self.DEFAULT_FONT_SIZE)

    def get_key_path(self):
        return self._key_path

    def set_key_path(self, path):
        self._key_path = path
        self._key_entry.configure(state="normal")
        self._key_entry.delete(0, tk.END)
        self._key_entry.insert(0, path)
        self._key_entry.configure(state="readonly")

    def other_key_is_selected(self):
        return self._key_choice.get() == "other"

    def default_key_is_selected(self):
        return self._key_choice.get() == "default"

    def other_key_set_selected(self):
        self._key_choice.set("other")

    def default_key_set_selected(self):
        self._key_choice.set("default")

    def show(self):
        self.deiconify()
        self.lift()
        self.focus_force()


class AboutDialog(tk.Toplevel):
    """About dialog window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"About: {APP_NAME} {APP_VERSION}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            frame, text=APP_NAME, font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack()

        # Description
        desc_label = ttk.Label(frame, text=APP_DESCRIPTION, wraplength=350)
        desc_label.pack(pady=(10, 15))

        # Info grid
        info_frame = ttk.Frame(frame)
        info_frame.pack()

        labels = [
            ("Product Version:", APP_VERSION),
            ("Vendor:", APP_VENDOR),
            ("Homepage:", APP_HOMEPAGE),
        ]
        for i, (label, value) in enumerate(labels):
            ttk.Label(
                info_frame, text=label, font=("TkDefaultFont", 0, "bold")
            ).grid(row=i, column=0, sticky=tk.W, padx=(0, 10))
            ttk.Label(info_frame, text=value).grid(
                row=i, column=1, sticky=tk.W
            )

        # Close button
        ttk.Button(frame, text="Close", command=self.destroy).pack(
            pady=(20, 0)
        )

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = (
            parent.winfo_y()
            + (parent.winfo_height() - self.winfo_height()) // 2
        )
        self.geometry(f"+{x}+{y}")


class SpackleApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("Spackle")
        self.resizable(False, False)

        # Check OS
        if sys.platform == "win32":
            messagebox.showerror(
                "Incompatible OS",
                "E099 This program is not for Windows. Please use PuTTY",
            )
            sys.exit(1)

        # State
        self._xterm_path = ""
        self._ssh_path = ""
        self._telnet_path = ""
        self._sessions = SortedProperties()

        # Connection properties dialog
        self._cp = ConnectionProperties(self)
        self._cp.set_save_default_callback(self._save_defaults)

        self._build_ui()
        self._center_window()

        # Load preferences
        self._load_prefs()

        # Locate commands (xterm only needed on Linux; macOS uses Terminal.app)
        try:
            if sys.platform != "darwin":
                self._xterm_path = self._locate_command("xterm")
            self._ssh_path = self._locate_command("ssh")
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"E100 {e}")

        # Telnet is optional (removed from modern macOS)
        try:
            self._telnet_path = self._locate_command("telnet")
        except FileNotFoundError:
            pass

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Connection section ---
        conn_frame = ttk.LabelFrame(
            main_frame,
            text="Specify your connection by hostname or IP address",
            padding=10,
        )
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(conn_frame, text="Hostname or IP address").grid(
            row=0, column=0, columnspan=2, sticky=tk.W
        )

        self._hostname_entry = ttk.Entry(conn_frame, width=35)
        self._hostname_entry.grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )

        ttk.Label(conn_frame, text="Port").grid(
            row=0, column=2, sticky=tk.W, padx=(20, 0)
        )

        self._port_entry = ttk.Entry(conn_frame, width=8)
        self._port_entry.insert(0, "22")
        self._port_entry.grid(
            row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(0, 10)
        )

        ttk.Label(conn_frame, text="Protocol:").grid(
            row=2, column=0, sticky=tk.W
        )

        self._protocol_var = tk.StringVar(value="ssh")
        proto_frame = ttk.Frame(conn_frame)
        proto_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W)

        ttk.Radiobutton(
            proto_frame,
            text="ssh",
            variable=self._protocol_var,
            value="ssh",
            command=self._on_ssh_selected,
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            proto_frame,
            text="telnet",
            variable=self._protocol_var,
            value="telnet",
            command=self._on_telnet_selected,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # --- Stored sessions section ---
        stored_frame = ttk.LabelFrame(
            main_frame,
            text="Load, save or delete a stored connection",
            padding=10,
        )
        stored_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(stored_frame, text="Saved Session Name").grid(
            row=0, column=0, sticky=tk.W
        )

        self._session_entry = ttk.Entry(stored_frame, width=30)
        self._session_entry.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        # Session list with scrollbar
        list_frame = ttk.Frame(stored_frame)
        list_frame.grid(row=2, column=0, sticky=tk.NSEW, pady=(0, 5))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self._session_list = tk.Listbox(
            list_frame,
            width=30,
            height=8,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
        )
        scrollbar.configure(command=self._session_list.yview)
        self._session_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._session_list.bind(
            "<Double-Button-1>", self._on_list_double_click
        )

        # Session buttons column
        btn_col = ttk.Frame(stored_frame)
        btn_col.grid(row=1, column=1, rowspan=2, sticky=tk.N, padx=(10, 0))

        ttk.Button(
            btn_col, text="Load", width=10, command=self._load_selected_session
        ).pack(pady=(0, 5))
        ttk.Button(
            btn_col, text="Save", width=10, command=self._save_session
        ).pack(pady=(0, 5))
        ttk.Button(
            btn_col, text="Delete", width=10, command=self._delete_session
        ).pack()

        # --- Session controls section ---
        ctrl_frame = ttk.LabelFrame(
            main_frame, text="Session controls", padding=10
        )
        ctrl_frame.pack(fill=tk.X)

        btn_row1 = ttk.Frame(ctrl_frame)
        btn_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            btn_row1, text="Options", width=12, command=self._show_properties
        ).pack(side=tk.LEFT)
        ttk.Button(
            btn_row1, text="Open", width=12, command=self._launch_terminal
        ).pack(side=tk.RIGHT)

        btn_row2 = ttk.Frame(ctrl_frame)
        btn_row2.pack(fill=tk.X)

        ttk.Button(
            btn_row2, text="About", width=12, command=self._show_about
        ).pack(side=tk.LEFT)
        ttk.Button(
            btn_row2, text="Exit", width=12, command=self.quit
        ).pack(side=tk.RIGHT)

        # Bind Enter key to Open
        self.bind("<Return>", lambda e: self._launch_terminal())

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _locate_command(self, command):
        """Find a command on the system using 'which', with shutil fallback."""
        env = os.environ.copy()
        if sys.platform == "darwin":
            env["PATH"] = env.get("PATH", "") + ":/usr/X11/bin"

        try:
            result = subprocess.run(
                ["/usr/bin/which", command],
                capture_output=True,
                text=True,
                env=env,
            )
            path = result.stdout.strip()
            if path:
                return path
        except Exception:
            pass

        # Fallback to shutil.which
        path = shutil.which(command)
        if path:
            return path
        raise FileNotFoundError(f"{command} not found on the system.")

    def _load_prefs(self):
        """Load preferences from file, creating defaults if needed."""
        if not os.path.exists(PREFS_FILE):
            Path(PREFS_FILE).touch()

        self._sessions.load(PREFS_FILE)

        # Check if defaults exist
        has_defaults = any(
            name.startswith("default.")
            for name in self._sessions.property_names()
        )

        if not has_defaults:
            self._sessions.set(
                "default.background",
                self._color_to_rgb_int(
                    self._cp.get_terminal_background_color()
                ),
            )
            self._sessions.set(
                "default.foreground",
                self._color_to_rgb_int(
                    self._cp.get_terminal_foreground_color()
                ),
            )
            self._sessions.set("default.geometry", self._cp.get_geometry())
            self._sessions.set(
                "default.scrollback", self._cp.get_scrollback_lines()
            )
            self._sessions.set("default.keypath", "default")
            self._sessions.set("default.fontsize", self._cp.get_font_size())
            self._write_sessions()
        else:
            self._load_session("default")

        self._refresh_sessions()

    @staticmethod
    def _color_to_rgb_int(hex_color):
        """Convert hex color (#rrggbb) to Java-compatible signed RGB int."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Java Color.getRGB() returns signed 32-bit int with alpha=255
        rgb = (255 << 24) | (r << 16) | (g << 8) | b
        if rgb >= 2**31:
            rgb -= 2**32
        return str(rgb)

    @staticmethod
    def _rgb_int_to_hex(rgb_int_str):
        """Convert Java-style signed RGB int to hex color (#rrggbb)."""
        try:
            rgb = int(rgb_int_str)
            if rgb < 0:
                rgb += 2**32
            r = (rgb >> 16) & 0xFF
            g = (rgb >> 8) & 0xFF
            b = rgb & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, TypeError):
            return "#000000"

    def _launch_terminal(self):
        """Validate inputs, build the SSH/Telnet command, and open a terminal."""
        hostname = self._hostname_entry.get().strip()
        port = self._port_entry.get().strip()
        geometry = self._cp.get_geometry()

        if not hostname:
            messagebox.showinfo("Spackle", "Please enter a hostname.")
            return

        # Parse user@host format
        username = ""
        title = ""
        if "@" in hostname:
            parts = hostname.split("@")
            title = hostname
            if len(parts) == 2 and parts[0] and parts[1]:
                username = parts[0]
                hostname = parts[1]
            else:
                messagebox.showinfo("Spackle", "Invalid hostname format.")
                return
        else:
            username = os.environ.get("USER", os.environ.get("LOGNAME", ""))
            title = f"{username}@{hostname}"

        # Build protocol-specific command
        if self._protocol_var.get() == "ssh":
            key_path = self._cp.get_key_path()
            if key_path:
                launch_cmd = (
                    f"{self._ssh_path} -p {port} -i {key_path} "
                    f"{username}@{hostname}"
                )
            else:
                launch_cmd = (
                    f"{self._ssh_path} -p {port} {username}@{hostname}"
                )
        else:
            title = f"telnet: {hostname}"
            launch_cmd = f"{self._telnet_path} {hostname} {port}"

        try:
            if not port:
                messagebox.showerror(
                    "Spackle",
                    "E105 No port specified: Please enter a port number.",
                )
                return

            # DNS check
            socket.gethostbyname(hostname)

            # Port connectivity check
            self._check_port(hostname, int(port))

            # Launch using platform-appropriate terminal
            if sys.platform == "darwin":
                self._open_macos_terminal(launch_cmd, title, geometry)
            else:
                self._open_xterm(launch_cmd, title, geometry)

        except socket.gaierror:
            messagebox.showerror(
                "Spackle", f"E105 Unknown Host: {hostname}"
            )
        except ValueError as e:
            messagebox.showerror(
                "Spackle", f"E105 No port specified: {e}"
            )
        except OSError as e:
            messagebox.showerror("Spackle", f"E105 IOException: {e}")

    def _open_macos_terminal(self, launch_cmd, title, geometry):
        """Open a new Terminal.app window via AppleScript with custom settings."""
        cols, rows = geometry.split("x")
        font_size = self._cp.get_font_size()

        fg_hex = self._cp.get_terminal_foreground_color().lstrip("#")
        bg_hex = self._cp.get_terminal_background_color().lstrip("#")

        # Convert hex colors to AppleScript color values (0-65535 range)
        def hex_to_as(h):
            r = int(h[0:2], 16) * 257
            g = int(h[2:4], 16) * 257
            b = int(h[4:6], 16) * 257
            return f"{{{r}, {g}, {b}}}"

        fg_as = hex_to_as(fg_hex)
        bg_as = hex_to_as(bg_hex)

        # Escape special characters for AppleScript string
        escaped_cmd = launch_cmd.replace("\\", "\\\\").replace('"', '\\"')
        escaped_title = title.replace("\\", "\\\\").replace('"', '\\"')

        script = f'''
tell application "Terminal"
    activate
    do script "{escaped_cmd}"
    set targetWindow to front window
    set custom title of targetWindow to "{escaped_title}"
    set number of columns of targetWindow to {cols}
    set number of rows of targetWindow to {rows}
    set background color of current settings of selected tab of targetWindow to {bg_as}
    set normal text color of current settings of selected tab of targetWindow to {fg_as}
    set font size of current settings of selected tab of targetWindow to {font_size}
end tell
'''
        subprocess.Popen(
            ["osascript", "-e", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _open_xterm(self, launch_cmd, title, geometry):
        """Open an xterm window (Linux fallback)."""
        font = f'"mono-{self._cp.get_font_size()}"'
        scrollback = self._cp.get_scrollback_lines()

        fg_hex = self._cp.get_terminal_foreground_color().lstrip("#")
        fg_xterm = f"rgb:{fg_hex[0:2]}/{fg_hex[2:4]}/{fg_hex[4:6]}"

        bg_hex = self._cp.get_terminal_background_color().lstrip("#")
        bg_xterm = f"rgb:{bg_hex[0:2]}/{bg_hex[2:4]}/{bg_hex[4:6]}"

        cmd = [
            self._xterm_path,
            "-T", title,
            "-geometry", geometry,
            "-sl", scrollback,
            "-fa", font,
            "-fg", fg_xterm,
            "-bg", bg_xterm,
            "-e", launch_cmd,
        ]

        subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    @staticmethod
    def _check_port(hostname, port):
        """Test that the specified port is open on the remote host."""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                server_hostname=hostname,
            )
            sock.settimeout(5)
            sock.connect((hostname, port))
            sock.close()
        except ssl.SSLError:
            # SSL handshake may fail but the port is open if we got this far
            pass
        except Exception:
            # Fallback: try a plain socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((hostname, port))
            sock.close()

    def _refresh_sessions(self):
        """Update the stored session list in the UI."""
        self._session_list.delete(0, tk.END)
        names = []
        for key in self._sessions.property_names():
            if key.endswith(".name"):
                val = self._sessions.get(key)
                if val:
                    names.append(val)
        names.sort()
        for name in names:
            self._session_list.insert(tk.END, name)

    def _load_session(self, session_name):
        """Load a session's settings into the UI."""
        s = session_name

        # name, hostname, port, and mode are NOT stored for "default"
        if s != "default":
            name = self._sessions.get(f"{s}.name")
            if name:
                self._session_entry.delete(0, tk.END)
                self._session_entry.insert(0, name)
            hostname = self._sessions.get(f"{s}.hostname")
            if hostname:
                self._hostname_entry.delete(0, tk.END)
                self._hostname_entry.insert(0, hostname)
            port = self._sessions.get(f"{s}.port")
            if port:
                self._port_entry.delete(0, tk.END)
                self._port_entry.insert(0, port)
            mode = self._sessions.get(f"{s}.mode")
            if mode == "ssh":
                self._protocol_var.set("ssh")
            elif mode == "telnet":
                self._protocol_var.set("telnet")

        # These properties apply to both default and named sessions
        geo = self._sessions.get(f"{s}.geometry")
        if geo:
            self._cp.set_geometry(geo)

        scrollback = self._sessions.get(f"{s}.scrollback")
        if scrollback:
            self._cp.set_scrollback_lines(scrollback)

        fontsize = self._sessions.get(f"{s}.fontsize")
        if fontsize:
            self._cp.set_font_size(fontsize)

        keypath = self._sessions.get(f"{s}.keypath")
        if keypath is None or keypath == "default":
            self._cp.default_key_set_selected()
            self._cp.set_key_path("")
        else:
            self._cp.other_key_set_selected()
            self._cp.set_key_path(keypath)

        bg = self._sessions.get(f"{s}.background")
        if bg:
            self._cp.set_terminal_background_color(self._rgb_int_to_hex(bg))

        fg = self._sessions.get(f"{s}.foreground")
        if fg:
            self._cp.set_terminal_foreground_color(self._rgb_int_to_hex(fg))

    def _load_selected_session(self):
        """Load the currently selected session from the list."""
        selection = self._session_list.curselection()
        if not selection:
            messagebox.showinfo(
                "Spackle", "E102 Please select an item from the list"
            )
            return
        name = self._session_list.get(selection[0])
        self._load_session(name)

    def _save_session(self):
        """Save the current connection settings as a named session."""
        hostname = self._hostname_entry.get().strip()
        session_name = self._session_entry.get().strip()
        port = self._port_entry.get().strip()
        mode = self._protocol_var.get()

        if not session_name or not hostname or not port:
            messagebox.showerror(
                "Save session",
                "Please enter a hostname, a port number, and a session name.",
            )
            return

        s = session_name
        self._sessions.set(f"{s}.name", session_name)
        self._sessions.set(f"{s}.hostname", hostname)
        self._sessions.set(f"{s}.mode", mode)
        self._sessions.set(f"{s}.port", port)
        self._sessions.set(
            f"{s}.background",
            self._color_to_rgb_int(self._cp.get_terminal_background_color()),
        )
        self._sessions.set(
            f"{s}.foreground",
            self._color_to_rgb_int(self._cp.get_terminal_foreground_color()),
        )
        self._sessions.set(f"{s}.geometry", self._cp.get_geometry())
        self._sessions.set(
            f"{s}.scrollback", self._cp.get_scrollback_lines()
        )
        self._sessions.set(f"{s}.fontsize", self._cp.get_font_size())

        if self._cp.other_key_is_selected():
            self._sessions.set(f"{s}.keypath", self._cp.get_key_path())
        elif self._cp.default_key_is_selected():
            self._sessions.set(f"{s}.keypath", "default")

        self._write_sessions()
        self._refresh_sessions()

    def _delete_session(self):
        """Delete the currently selected session."""
        selection = self._session_list.curselection()
        if not selection:
            messagebox.showinfo(
                "Spackle", "E103 Please select an item from the list"
            )
            return

        name = self._session_list.get(selection[0])
        for suffix in [
            ".background", ".foreground", ".hostname", ".mode",
            ".name", ".port", ".geometry", ".keypath",
            ".scrollback", ".fontsize",
        ]:
            self._sessions.remove(name + suffix)

        self._write_sessions()
        self._refresh_sessions()

    def _write_sessions(self):
        """Persist sessions to the preferences file."""
        self._sessions.store(PREFS_FILE)

    def _save_defaults(self):
        """Save current properties as the default session settings."""
        self._sessions.set(
            "default.background",
            self._color_to_rgb_int(self._cp.get_terminal_background_color()),
        )
        self._sessions.set(
            "default.foreground",
            self._color_to_rgb_int(self._cp.get_terminal_foreground_color()),
        )
        self._sessions.set("default.geometry", self._cp.get_geometry())
        self._sessions.set(
            "default.scrollback", self._cp.get_scrollback_lines()
        )
        self._sessions.set("default.fontsize", self._cp.get_font_size())

        if self._cp.other_key_is_selected():
            self._sessions.set("default.keypath", self._cp.get_key_path())
        elif self._cp.default_key_is_selected():
            self._sessions.set("default.keypath", "default")

        self._write_sessions()

    def _show_properties(self):
        self._cp.show()

    def _show_about(self):
        AboutDialog(self)

    def _on_ssh_selected(self):
        if not self._ssh_path:
            messagebox.showerror(
                "Spackle", "E101 SSH not found on the system."
            )
            return
        self._port_entry.delete(0, tk.END)
        self._port_entry.insert(0, "22")

    def _on_telnet_selected(self):
        if not self._telnet_path:
            msg = "E101 Telnet not found on the system."
            if sys.platform == "darwin":
                msg += "\n\nInstall it with:  brew install telnet"
            messagebox.showerror("Spackle", msg)
            return
        self._port_entry.delete(0, tk.END)
        self._port_entry.insert(0, "23")

    def _on_list_double_click(self, event):
        """Double-click loads and launches the selected session."""
        selection = self._session_list.curselection()
        if selection:
            name = self._session_list.get(selection[0])
            self._load_session(name)
            self._launch_terminal()


def main():
    app = SpackleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
