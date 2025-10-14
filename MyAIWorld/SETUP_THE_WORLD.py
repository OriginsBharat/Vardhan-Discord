import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
import subprocess
import sys
import ctypes
import platform
import threading

# --- Definitive Path Fix ---
# Get the absolute path of the directory containing this script.
# All other paths will be built from this, making the script robust.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("My AI World - World Setup")
        self.geometry("650x850")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)

        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self.main_frame, text="My AI World Setup", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(10, 10))

        # --- Secrets ---
        secrets_label = ctk.CTkLabel(self.main_frame, text="Secrets & Credentials", font=ctk.CTkFont(size=16, weight="bold"))
        secrets_label.grid(row=1, column=0, columnspan=3, padx=20, pady=(10,0), sticky="w")
        self.secrets_frame = ctk.CTkFrame(self.main_frame)
        self.secrets_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        self.secrets_frame.grid_columnconfigure(1, weight=1)

        # --- File Paths ---
        paths_label = ctk.CTkLabel(self.main_frame, text="AI Engine Folder Paths", font=ctk.CTkFont(size=16, weight="bold"))
        paths_label.grid(row=3, column=0, columnspan=3, padx=20, pady=(10,0), sticky="w")
        self.paths_frame = ctk.CTkFrame(self.main_frame)
        self.paths_frame.grid(row=4, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        self.paths_frame.grid_columnconfigure(1, weight=1)

        # --- Voices ---
        self.voices_label = ctk.CTkLabel(self.main_frame, text="Character Voice Files (.wav)", font=ctk.CTkFont(size=16, weight="bold"))
        self.voices_label.grid(row=5, column=0, columnspan=3, padx=20, pady=(10, 0), sticky="w")
        self.voices_frame = ctk.CTkFrame(self.main_frame)
        self.voices_frame.grid(row=6, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        self.voices_frame.grid_columnconfigure(1, weight=1)
        self.voice_entries = {}

        # --- Kink Profiles ---
        self.kinks_label = ctk.CTkLabel(self.main_frame, text="Character Kink Profiles", font=ctk.CTkFont(size=16, weight="bold"))
        self.kinks_label.grid(row=7, column=0, columnspan=3, padx=20, pady=(10, 0), sticky="w")
        self.kinks_frame = ctk.CTkFrame(self.main_frame)
        self.kinks_frame.grid(row=8, column=0, columnspan=3, padx=20, pady=10, sticky="ew")
        self.kinks_frame.grid_columnconfigure(1, weight=1)
        self.kink_entries = {}

        # --- Setup Button ---
        self.setup_button = ctk.CTkButton(self.main_frame, text="Begin World Setup", command=self.begin_setup, font=ctk.CTkFont(size=14, weight="bold"))
        self.setup_button.grid(row=9, column=0, columnspan=3, padx=20, pady=20, sticky="ew")

        self.populate_all_fields()
        self.auto_detect_paths()

    def populate_all_fields(self):
        # Secrets
        ctk.CTkLabel(self.secrets_frame, text="Discord Token:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.discord_token_entry = ctk.CTkEntry(self.secrets_frame, show="*")
        self.discord_token_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.secrets_frame, text="Pinecone API Key:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.pinecone_key_entry = ctk.CTkEntry(self.secrets_frame, show="*")
        self.pinecone_key_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.secrets_frame, text="Pinecone Host URL:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.pinecone_env_entry = ctk.CTkEntry(self.secrets_frame, placeholder_text="e.g., https://my-index-12345.svc.us-west1-gcp.pinecone.io")
        self.pinecone_env_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(self.secrets_frame, text="Your Discord User ID:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.master_id_entry = ctk.CTkEntry(self.secrets_frame)
        self.master_id_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Paths
        ctk.CTkLabel(self.paths_frame, text="Ollama Path:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ollama_path_entry = ctk.CTkEntry(self.paths_frame)
        self.ollama_path_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.paths_frame, text="Browse", width=70, command=lambda: self.browse_directory(self.ollama_path_entry)).grid(row=0, column=2, padx=10, pady=5)
        ctk.CTkLabel(self.paths_frame, text="ComfyUI Path:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.comfyui_path_entry = ctk.CTkEntry(self.paths_frame)
        self.comfyui_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.paths_frame, text="Browse", width=70, command=lambda: self.browse_directory(self.comfyui_path_entry)).grid(row=1, column=2, padx=10, pady=5)

        # Voices & Kinks
        try:
            # Use absolute path
            with open(os.path.join(BASE_DIR, "data", "character_canon.json"), "r") as f:
                characters = json.load(f)
            for i, name in enumerate(characters.keys()):
                ctk.CTkLabel(self.voices_frame, text=f"{name} Voice:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
                v_entry = ctk.CTkEntry(self.voices_frame)
                v_entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                ctk.CTkButton(self.voices_frame, text="Browse", width=70, command=lambda e=v_entry: self.browse_file(e)).grid(row=i, column=2, padx=10, pady=5)
                self.voice_entries[name] = v_entry
                ctk.CTkLabel(self.kinks_frame, text=f"{name}:").grid(row=i, column=0, padx=10, pady=5, sticky="w")
                k_entry = ctk.CTkEntry(self.kinks_frame, placeholder_text="e.g., praise, domination")
                k_entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                self.kink_entries[name] = k_entry
        except FileNotFoundError:
            messagebox.showerror("Error", f"Critical file not found: {os.path.join(BASE_DIR, 'data', 'character_canon.json')}")

    def find_path(self, program_name, executable_name):
        if platform.system() != "Windows": return None
        search_paths = [ os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)"), os.path.join(os.getenv("LOCALAPPDATA")), os.path.expanduser("~") ]
        for path in search_paths:
            if not path: continue
            for root, dirs, files in os.walk(path):
                if program_name in dirs or executable_name in files:
                    for d in dirs:
                        if d == program_name: return os.path.join(root, d)
                    for f in files:
                        if f == executable_name: return root
        return None

    def auto_detect_paths(self):
        ollama_path = self.find_path("Ollama", "ollama.exe")
        if ollama_path: self.ollama_path_entry.insert(0, ollama_path)
        messagebox.showinfo("Auto-Detect", "Attempted to auto-detect AI engine paths. Please verify them.")

    def browse_directory(self, entry_widget):
        directory = filedialog.askdirectory()
        if directory: entry_widget.delete(0, "end"); entry_widget.insert(0, directory)

    def browse_file(self, entry_widget):
        filepath = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if filepath: entry_widget.delete(0, "end"); entry_widget.insert(0, filepath)

    def begin_setup(self):
        if not all([self.discord_token_entry.get(), self.pinecone_key_entry.get(), self.pinecone_env_entry.get(), self.master_id_entry.get()]):
            messagebox.showerror("Error", "All secret fields must be filled out.")
            return

        # Ensure data directories exist using absolute paths
        os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
        os.makedirs(os.path.join(BASE_DIR, "data", "voices"), exist_ok=True)

        with open(os.path.join(BASE_DIR, ".env"), "w") as f:
            f.write(f"DISCORD_TOKEN={self.discord_token_entry.get()}\n")
            f.write(f"PINECONE_API_KEY={self.pinecone_key_entry.get()}\n")
            f.write(f"PINECONE_ENVIRONMENT={self.pinecone_env_entry.get()}\n")
            f.write(f"MASTER_ID={self.master_id_entry.get()}\n")
            f.write(f"OLLAMA_PATH={self.ollama_path_entry.get()}\n")
            f.write(f"COMFYUI_PATH={self.comfyui_path_entry.get()}\n")
            for name, entry in self.voice_entries.items():
                f.write(f"VOICE_{name.upper()}={entry.get()}\n")

        kinks_data = {name: [k.strip() for k in entry.get().split(',')] for name, entry in self.kink_entries.items()}
        with open(os.path.join(BASE_DIR, "data", "character_kinks.json"), "w") as f:
            json.dump(kinks_data, f, indent=4)

        # Create the invisible VBS launcher
        self.create_vbs_launcher()

        # Pull the required Ollama model
        self.pull_ollama_model()

    def create_vbs_launcher(self):
        """Creates a VBScript to launch all necessary background services silently and robustly."""
        ollama_exe_path = os.path.abspath(os.path.join(self.ollama_path_entry.get(), 'ollama.exe'))
        comfyui_python_path = os.path.abspath(os.path.join(self.comfyui_path_entry.get(), 'python_embeded', 'python.exe'))
        comfyui_main_path = os.path.abspath(os.path.join(self.comfyui_path_entry.get(), 'main.py'))
        start_world_bat_path = os.path.abspath(os.path.join(BASE_DIR, 'start_world.bat'))

        vbs_script_content = f'''
Set WshShell = CreateObject("WScript.Shell")
WshShell.Environment("PROCESS")("OLLAMA_HOST") = "127.0.0.1"
WshShell.Run "cmd /c ""{ollama_exe_path}"" serve", 0, false
WshShell.Run "cmd /c ""{comfyui_python_path}"" ""{comfyui_main_path}"" --windows-standalone-build", 0, false
WshShell.Run "cmd /c ""{start_world_bat_path}""", 0, false
Set WshShell = Nothing
'''
        with open(os.path.join(BASE_DIR, "invisible_launcher.vbs"), "w") as f:
            f.write(vbs_script_content)

        if platform.system() == "Windows":
            startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            if os.path.isdir(startup_folder):
                import shutil
                shutil.copy(os.path.join(BASE_DIR, "invisible_launcher.vbs"), startup_folder)
                messagebox.showinfo("Success", "Configuration saved and auto-start enabled.")
            else:
                messagebox.showwarning("Warning", "Could not find Windows startup folder. You will need to start the world manually.")
        else:
            messagebox.showinfo("Success", "Configuration saved. Auto-start is only supported on Windows.")

    def pull_ollama_model(self):
        """Pulls the required Ollama model in a separate thread to avoid freezing the GUI."""
        model_name = "dolphin-2.2.1-mistral:7b-q4_K_M"

        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Downloading AI Model")
        progress_window.geometry("400x150")
        progress_window.transient(self)
        progress_window.grab_set()

        label = ctk.CTkLabel(progress_window, text=f"Performing first-time setup.\nDownloading required AI model:\n\n{model_name}\n\nThis may take several minutes and will happen in a separate window.\nPlease do not close it.", wraplength=380)
        label.pack(pady=20, padx=20)

        def do_pull():
            try:
                ollama_exe_path = os.path.abspath(os.path.join(self.ollama_path_entry.get(), "ollama.exe"))
                command = f'"{ollama_exe_path}" pull {model_name}'
                subprocess.run(command, check=True, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                messagebox.showinfo("Success", f"Successfully downloaded AI model: {model_name}")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to download AI model. Please run 'ollama pull {model_name}' manually.\nError: {e}")
            except FileNotFoundError:
                messagebox.showerror("Error", "Could not find ollama.exe. Please ensure the path is correct.")
            finally:
                progress_window.destroy()
                self.destroy()

        download_thread = threading.Thread(target=do_pull)
        download_thread.start()

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()