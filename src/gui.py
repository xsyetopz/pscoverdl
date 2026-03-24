"""
⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀
    
    NO COVERS?
"""

import sys
import threading
import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
import os
from pathlib import Path
from PIL import Image, ImageTk
import configparser
import pscoverdl
import requests
import certifi

VERSION = 1.1

# Cross-platform font: MS Sans Serif only exists on Windows
if sys.platform == "win32":
    APP_FONT = ("MS Sans Serif", 12, "bold")
else:
    APP_FONT = ("Helvetica", 12, "bold")


def get_config_path() -> Path:
    """
    Return a platform-appropriate path for pscoverdl.ini.

    - Windows : %APPDATA%\\pscoverdl\\pscoverdl.ini
    - macOS   : ~/Library/Application Support/pscoverdl/pscoverdl.ini
    - Linux   : $XDG_CONFIG_HOME/pscoverdl/pscoverdl.ini  (default ~/.config)
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    config_dir = base / "pscoverdl"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "pscoverdl.ini"


class pscoverdl_gui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.check_updates(VERSION)

        # --- Cross-platform icon loading ---
        # .ico is Windows-only. Use .png on macOS/Linux.
        icon_dir = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "app")
        if sys.platform == "win32":
            icon_file = os.path.join(icon_dir, "icon.ico")
        else:
            icon_file = os.path.join(icon_dir, "icon.png")

        if os.path.isfile(icon_file):
            icon_photo = ImageTk.PhotoImage(Image.open(icon_file))
            self.wm_iconphoto(True, icon_photo)

        self.geometry("450x400")
        self.resizable(False, False)
        self.font = APP_FONT
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Phase 1 Fix: use os.path.join consistently for image paths ---
        image_path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), "icons")

        self.ps1_image = ctk.CTkImage(
            Image.open(os.path.join(image_path, "ps1.png")), size=(20, 20)
        )
        self.ps2_image = ctk.CTkImage(
            Image.open(os.path.join(image_path, "ps2.png")), size=(20, 20)
        )

        # region nav frame
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.duckstation = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            font=self.font,
            text="DuckStation",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.ps1_image,
            anchor="w",
            command=self.duckstation_button_event,
        )
        self.duckstation.grid(row=1, column=0, sticky="ew")

        self.pcsx2 = ctk.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            font=self.font,
            text="PCSX2",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.ps2_image,
            anchor="w",
            command=self.pcsx2_button_event,
        )
        self.pcsx2.grid(row=2, column=0, sticky="ew")

        # endregion

        # region duckstation frame
        self.duckstation_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )

        # covers Dir
        self.duckstation_covers_directory_textbox = ctk.CTkEntry(
            self.duckstation_frame, placeholder_text="Cover Directory", width=200
        )
        self.duckstation_covers_directory_textbox.grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )

        self.duckstation_covers_directory_button = ctk.CTkButton(
            self.duckstation_frame,
            text="Browse",
            command=lambda: self.select_directory("duckstation", False),
            width=10,
        )
        self.duckstation_covers_directory_button.grid(
            row=0, column=1, padx=5, pady=5, sticky="e"
        )

        self.duckstation_gamecache_textbox = ctk.CTkEntry(
            self.duckstation_frame, placeholder_text="Game Cache", width=200
        )
        self.duckstation_gamecache_textbox.grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )

        self.duckstation_gamecache_button = ctk.CTkButton(
            self.duckstation_frame,
            text="Browse",
            command=lambda: self.select_directory("duckstation", True),
            width=10,
        )
        self.duckstation_gamecache_button.grid(
            row=1, column=1, padx=5, pady=5, sticky="e"
        )

        self.duckstation_cover_type_var = tk.IntVar(value=0)

        self.duckstation_label_radio_group = ctk.CTkLabel(
            master=self.duckstation_frame, text="Cover Type:"
        )
        self.duckstation_label_radio_group.grid(
            row=2, column=0, padx=10, pady=10, sticky="w"
        )

        self.duckstation_radio_button_1 = ctk.CTkRadioButton(
            master=self.duckstation_frame,
            text="Default",
            variable=self.duckstation_cover_type_var,
            value=0
        )
        self.duckstation_radio_button_1.grid(
            row=3, column=0, pady=10, padx=20, sticky="w"
        )

        self.duckstation_radio_button_2 = ctk.CTkRadioButton(
            master=self.duckstation_frame,
            text="3D",
            variable=self.duckstation_cover_type_var,
            value=1
        )
        self.duckstation_radio_button_2.grid(
            row=4, column=0, pady=10, padx=20, sticky="w"
        )

        self.duckstation_use_ssl_checkbox = ctk.CTkCheckBox(
            self.duckstation_frame, text="Use SSL"
        )
        self.duckstation_use_ssl_checkbox.grid(
            row=5, column=0, padx=10, pady=10, sticky="w"
        )
        
        self.duckstation_fallback_checkbox = ctk.CTkCheckBox(
            self.duckstation_frame, text="Fallback to other cover type if not found"
        )
        self.duckstation_fallback_checkbox.grid(
            row=6, column=0, columnspan=2, padx=10, pady=10, sticky="w"
        )


        # duckstation download button
        self.start_download_button = ctk.CTkButton(
            self.duckstation_frame,
            text="Start Download",
            command=lambda: self.start_download("duckstation"),
        )
        self.start_download_button.grid(row=7, column=0, padx=10, pady=10, sticky="w")

        # endregion

        # region pcsx2 frame
        self.pcsx2_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent")

        # pcsx2 covers Dir textbox
        self.pcsx2_covers_directory_textbox = ctk.CTkEntry(
            self.pcsx2_frame, placeholder_text="Cover Directory", width=200
        )
        self.pcsx2_covers_directory_textbox.grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )

        # pcsx2 browser button
        self.pcsx2_covers_directory_button = ctk.CTkButton(
            self.pcsx2_frame,
            text="Browse",
            command=lambda: self.select_directory("pcsx2", False),
            width=10,
        )
        self.pcsx2_covers_directory_button.grid(
            row=0, column=1, padx=5, pady=5, sticky="e"
        )

        # pcsx2 cache textbox
        self.pcsx2_gamecache_textbox = ctk.CTkEntry(
            self.pcsx2_frame, placeholder_text="Game Cache", width=200
        )
        self.pcsx2_gamecache_textbox.grid(
            row=1, column=0, padx=10, pady=10, sticky="w")

        # pcsx2 browser button
        self.pcsx2_gamecache_button = ctk.CTkButton(
            self.pcsx2_frame,
            text="Browse",
            command=lambda: self.select_directory("pcsx2", True),
            width=10,
        )
        self.pcsx2_gamecache_button.grid(
            row=1, column=1, padx=5, pady=5, sticky="e")

        self.pcsx2_cover_type_var = tk.IntVar(value=0)

        # pcsx2 covertype radiobuttons
        self.pcsx2_label_radio_group = ctk.CTkLabel(
            master=self.pcsx2_frame, text="Cover Type:"
        )
        self.pcsx2_label_radio_group.grid(
            row=2, column=0, padx=10, pady=10, sticky="w")

        self.pcsx2_radio_button_1 = ctk.CTkRadioButton(
            master=self.pcsx2_frame,
            text="Default",
            variable=self.pcsx2_cover_type_var,
            value=0
        )
        self.pcsx2_radio_button_1.grid(
            row=3, column=0, pady=10, padx=20, sticky="w")

        self.pcsx2_radio_button_2 = ctk.CTkRadioButton(
            master=self.pcsx2_frame,
            text="3D",
            variable=self.pcsx2_cover_type_var,
            value=1
        )
        self.pcsx2_radio_button_2.grid(
            row=4, column=0, pady=10, padx=20, sticky="w")

        # pcsx2 use_ssl button
        self.pcsx2_use_ssl_checkbox = ctk.CTkCheckBox(self.pcsx2_frame, text="Use SSL")
        self.pcsx2_use_ssl_checkbox.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        self.pcsx2_fallback_checkbox = ctk.CTkCheckBox(
            self.pcsx2_frame, text="Fallback to other cover type if not found"
        )
        self.pcsx2_fallback_checkbox.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # pcsx2 download button
        self.start_download_button = ctk.CTkButton(
            self.pcsx2_frame,
            text="Start Download",
            command=lambda: self.start_download("pcsx2"),
        )
        self.start_download_button.grid(row=7, column=0, padx=10, pady=10, sticky="w")

        # endregion

        self.load_configurations()

    def select_frame_by_name(self, name):
        self.duckstation.configure(
            fg_color=("gray75", "gray25")
            if name == "duckstation_frame"
            else "transparent"
        )
        self.pcsx2.configure(
            fg_color=(
                "gray75", "gray25") if name == "pcsx2_frame" else "transparent"
        )

        # show selected frame
        if name == "duckstation_frame":
            self.duckstation_frame.grid(row=0, column=1, sticky="nsew")
            self.pcsx2_frame.grid_forget()
        elif name == "pcsx2_frame":
            self.pcsx2_frame.grid(row=0, column=1, sticky="nsew")
            self.duckstation_frame.grid_forget()

    def duckstation_button_event(self):
        self.select_frame_by_name("duckstation_frame")

    def pcsx2_button_event(self):
        self.select_frame_by_name("pcsx2_frame")

    def select_directory(self, emulator: str, is_cache: bool):
        # emulator - pcsx2, duckstation
        if emulator == "pcsx2":
            if is_cache:
                filetypes = (("gamelist", "*.cache"),)
                file_path = filedialog.askopenfilename(filetypes=filetypes)
                self.pcsx2_gamecache_textbox.delete(0, "end")
                self.pcsx2_gamecache_textbox.insert(0, file_path)
            else:
                file_path = filedialog.askdirectory()
                self.pcsx2_covers_directory_textbox.delete(0, "end")
                self.pcsx2_covers_directory_textbox.insert(0, file_path)
        elif emulator == "duckstation":
            if is_cache:
                filetypes = (("gamelist", "*.cache"),)
                file_path = filedialog.askopenfilename(filetypes=filetypes)
                self.duckstation_gamecache_textbox.delete(0, "end")
                self.duckstation_gamecache_textbox.insert(0, file_path)
            else:
                file_path = filedialog.askdirectory()
                self.duckstation_covers_directory_textbox.delete(0, "end")
                self.duckstation_covers_directory_textbox.insert(0, file_path)

    def load_configurations(self):
        config_path = get_config_path()
        if config_path.is_file():
            try:
                config = configparser.ConfigParser()
                config.read(config_path)

                duckstation_covers_dir = config.get("Duckstation", "cover_directory")
                duckstation_game_cache = config.get("Duckstation", "game_cache")
                duckstation_cover_type = config.getint("Duckstation", "cover_type")
                duckstation_use_ssl = config.getboolean("Duckstation", "use_ssl")
                duckstation_fallback = config.getboolean("Duckstation", "fallback")

                pcsx2_covers_dir = config.get("PCSX2", "cover_directory")
                pcsx2_game_cache = config.get("PCSX2", "game_cache")
                pcsx2_cover_type = config.getint("PCSX2", "cover_type")
                pcsx2_use_ssl = config.getboolean("PCSX2", "use_ssl")
                pcsx2_fallback = config.getboolean("PCSX2", "fallback")

                self.duckstation_covers_directory_textbox.insert(
                    0, duckstation_covers_dir
                )
                self.duckstation_gamecache_textbox.insert(
                    0, duckstation_game_cache)
                self.duckstation_cover_type_var.set(duckstation_cover_type)

                if duckstation_use_ssl:
                    self.duckstation_use_ssl_checkbox.select()
                
                if duckstation_fallback:
                    self.duckstation_fallback_checkbox.select()
                else:
                    self.duckstation_fallback_checkbox.deselect()

                self.pcsx2_covers_directory_textbox.insert(0, pcsx2_covers_dir)
                self.pcsx2_gamecache_textbox.insert(0, pcsx2_game_cache)
                self.pcsx2_cover_type_var.set(pcsx2_cover_type)
                
                if pcsx2_use_ssl:
                    self.pcsx2_use_ssl_checkbox.select()
                    
                if pcsx2_fallback:
                    self.pcsx2_fallback_checkbox.select()
                else:
                    self.pcsx2_fallback_checkbox.deselect()
            except:
                print("A problem occurred while trying to read pscoverdl.ini")

    def save_configurations(self):
        config = configparser.ConfigParser()

        config["Duckstation"] = {
            "cover_directory": self.duckstation_covers_directory_textbox.get(),
            "game_cache": self.duckstation_gamecache_textbox.get(),
            "cover_type": str(self.duckstation_cover_type_var.get()),
            "use_ssl": str(self.duckstation_use_ssl_checkbox.get()),
            "fallback": str(self.duckstation_fallback_checkbox.get())
        }

        config["PCSX2"] = {
            "cover_directory": self.pcsx2_covers_directory_textbox.get(),
            "game_cache": self.pcsx2_gamecache_textbox.get(),
            "cover_type": str(self.pcsx2_cover_type_var.get()),
            "use_ssl": str(self.pcsx2_use_ssl_checkbox.get()),
            "fallback": str(self.pcsx2_fallback_checkbox.get())
        }

        with open(get_config_path(), "w") as configfile:
            config.write(configfile)

    def start_download(self, emulator: str):
        # Collect args before entering the thread (must read Tkinter widgets on main thread)
        if emulator == "pcsx2":
            args = (
                self.pcsx2_covers_directory_textbox.get(),
                self.pcsx2_gamecache_textbox.get(),
                self.pcsx2_cover_type_var.get(),
                self.pcsx2_use_ssl_checkbox.get(),
                emulator,
                self.pcsx2_fallback_checkbox.get()
            )
        elif emulator == "duckstation":
            args = (
                self.duckstation_covers_directory_textbox.get(),
                self.duckstation_gamecache_textbox.get(),
                self.duckstation_cover_type_var.get(),
                self.duckstation_use_ssl_checkbox.get(),
                emulator,
                self.duckstation_fallback_checkbox.get()
            )
        else:
            return

        # Disable both download buttons while running
        self._set_download_buttons_state("disabled")

        def _run():
            pscoverdl.download_covers(*args)
            # Schedule UI updates back on the main thread via after()
            self.after(0, self._on_download_complete)

        threading.Thread(target=_run, daemon=True).start()

    def _on_download_complete(self):
        """Called on the main thread when the background download finishes."""
        self.save_configurations()
        self._set_download_buttons_state("normal")

    def _set_download_buttons_state(self, state: str):
        """Enable or disable both emulator download buttons at once."""
        for frame in (self.duckstation_frame, self.pcsx2_frame):
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Start Download":
                    widget.configure(state=state)

    def check_updates(self, version: float):
        """Fetch the latest version number in a background thread to avoid blocking startup."""
        def _fetch():
            try:
                rep_version_str = requests.get(
                    "https://github.com/xlenore/pscoverdl/raw/main/VERSION",
                    timeout=5,
                    verify=certifi.where(),
                ).text.strip()
                try:
                    rep_version = float(rep_version_str)
                except ValueError:
                    rep_version = version
            except requests.exceptions.RequestException:
                rep_version = version

            new_title = (
                f"PSCoverDL - {version}"
                f"{' | NEW VERSION AVAILABLE' if version != rep_version else ''}"
            )
            self.after(0, lambda: self.title(new_title))

        # Set a neutral title immediately, then update it when the request completes
        self.title(f"PSCoverDL - {version}")
        threading.Thread(target=_fetch, daemon=True).start()


if __name__ == "__main__":
    app = pscoverdl_gui()
    app.mainloop()
