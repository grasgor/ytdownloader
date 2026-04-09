import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import shutil
import os
import sys

try:
    import yt_dlp
except ImportError:
    messagebox.showerror("Missing dependency", "yt-dlp not found. Please reinstall the app.")
    sys.exit(1)


WINGET_PACKAGES = [
    ("ffmpeg",  "Gyan.FFmpeg"),
    ("yt-dlp",  "yt-dlp.yt-dlp"),
]


def _missing_tools():
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("Gyan.FFmpeg")
    if not shutil.which("yt-dlp"):
        missing.append("yt-dlp.yt-dlp")
    return missing


def _install_via_winget(pkg_ids, status_cb):
    for pkg in pkg_ids:
        status_cb(f"Installing {pkg}…")
        result = subprocess.run(
            ["winget", "install", "--id", pkg, "-e", "--silent",
             "--accept-source-agreements", "--accept-package-agreements"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"winget failed for {pkg}:\n{result.stderr.strip()}")


def ensure_dependencies(root, on_ready):
    """Check for ffmpeg/yt-dlp; install via winget if missing, then call on_ready."""
    missing = _missing_tools()
    if not missing:
        on_ready()
        return

    names = " and ".join(p.split(".")[0] for p in missing)
    ok = messagebox.askyesno(
        "One-time setup",
        f"{names} need to be installed for the app to work.\n\n"
        "Click Yes to install automatically (requires internet).\n"
        "This only happens once.",
    )
    if not ok:
        root.destroy()
        return

    # Show install overlay centered on screen
    overlay = tk.Toplevel(root)
    overlay.title("Video Downloader — Setup")
    overlay.resizable(False, False)
    overlay.grab_set()
    overlay.configure(bg="#1e1e2e")
    W, H = 420, 160
    overlay.update_idletasks()
    sw = overlay.winfo_screenwidth()
    sh = overlay.winfo_screenheight()
    overlay.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    tk.Label(overlay, text="Setting up Video Downloader",
             font=("Segoe UI", 12, "bold"), bg="#1e1e2e", fg="#e2e8f0").pack(pady=(22, 4))
    lbl = tk.Label(overlay, text="Starting…", font=("Segoe UI", 9),
                   bg="#1e1e2e", fg="#94a3b8")
    lbl.pack(pady=(0, 10))
    bar = ttk.Progressbar(overlay, mode="indeterminate", length=340)
    bar.pack()
    bar.start(12)

    def status_cb(msg):
        root.after(0, lbl.config, {"text": msg})

    def worker():
        try:
            _install_via_winget(missing, status_cb)
            root.after(0, _install_done, overlay, on_ready, None)
        except Exception as e:
            root.after(0, _install_done, overlay, on_ready, str(e))

    threading.Thread(target=worker, daemon=True).start()


def _install_done(overlay, on_ready, error):
    overlay.destroy()
    if error:
        messagebox.showerror("Install failed", error)
    else:
        messagebox.showinfo("Ready!", "Setup complete. You're good to go!")
        on_ready()


RESOLUTIONS = [
    ("Best available",       "bestvideo+bestaudio/best"),
    ("1080p",                "bestvideo[height<=1080]+bestaudio/best"),
    ("720p",                 "bestvideo[height<=720]+bestaudio/best"),
    ("480p",                 "bestvideo[height<=480]+bestaudio/best"),
    ("360p",                 "bestvideo[height<=360]+bestaudio/best"),
    ("Audio only (mp3)",     "bestaudio/best"),
]

AUDIO_ONLY_LABEL = "Audio only (mp3)"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Downloader")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self._center_window(520, 340)
        self._build_ui()

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        PAD = 18
        BG   = "#1e1e2e"
        CARD = "#2a2a3e"
        ACC  = "#7c3aed"
        FG   = "#e2e8f0"
        SUB  = "#94a3b8"
        FONT = ("Segoe UI", 10)
        BOLD = ("Segoe UI", 10, "bold")

        # ── title ──────────────────────────────────────────────────────
        tk.Label(self, text="Video Downloader", font=("Segoe UI", 16, "bold"),
                 bg=BG, fg=FG).pack(pady=(PAD, 4))
        tk.Label(self, text="Paste a YouTube (or any site) link below",
                 font=FONT, bg=BG, fg=SUB).pack(pady=(0, PAD))

        frame = tk.Frame(self, bg=CARD, bd=0)
        frame.pack(fill="x", padx=PAD)
        frame.columnconfigure(1, weight=1)

        def row(r, label, widget_fn):
            tk.Label(frame, text=label, font=BOLD, bg=CARD, fg=FG,
                     anchor="w", width=12).grid(row=r, column=0, padx=(12,6), pady=8, sticky="w")
            w = widget_fn(frame)
            w.grid(row=r, column=1, padx=(0, 12), pady=8, sticky="ew")
            return w

        # URL
        self.url_var = tk.StringVar()
        url_entry = row(0, "Link", lambda p: tk.Entry(
            p, textvariable=self.url_var, font=FONT,
            bg="#12121f", fg=FG, insertbackground=FG,
            relief="flat", bd=4))

        # Paste button
        def paste():
            try:
                self.url_var.set(self.clipboard_get())
            except Exception:
                pass
        tk.Button(frame, text="Paste", font=FONT, bg=ACC, fg="white",
                  relief="flat", bd=0, padx=8, cursor="hand2",
                  command=paste).grid(row=0, column=2, padx=(0,12), pady=8)

        # Resolution
        self.res_var = tk.StringVar(value=RESOLUTIONS[0][0])
        res_labels = [r[0] for r in RESOLUTIONS]
        row(1, "Quality", lambda p: ttk.Combobox(
            p, textvariable=self.res_var, values=res_labels,
            state="readonly", font=FONT))

        # Save folder
        self.folder_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        folder_entry = row(2, "Save to", lambda p: tk.Entry(
            p, textvariable=self.folder_var, font=FONT,
            bg="#12121f", fg=FG, insertbackground=FG,
            relief="flat", bd=4))
        tk.Button(frame, text="Browse", font=FONT, bg="#334155", fg=FG,
                  relief="flat", bd=0, padx=8, cursor="hand2",
                  command=self._browse).grid(row=2, column=2, padx=(0,12), pady=8)

        # ── progress ───────────────────────────────────────────────────
        self.progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=PAD, pady=(PAD, 4))

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self.status_var, font=FONT,
                 bg=BG, fg=SUB).pack()

        # ── download button ────────────────────────────────────────────
        self.btn = tk.Button(self, text="Download", font=("Segoe UI", 11, "bold"),
                             bg=ACC, fg="white", relief="flat", bd=0,
                             padx=20, pady=8, cursor="hand2",
                             command=self._start)
        self.btn.pack(pady=PAD)

        # style combobox
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#12121f", background="#12121f",
                        foreground=FG, selectbackground=ACC)
        style.configure("TProgressbar", troughcolor=CARD, background=ACC)

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.folder_var.get())
        if d:
            self.folder_var.set(d)

    def _fmt_label_to_format(self, label):
        for lbl, fmt in RESOLUTIONS:
            if lbl == label:
                return fmt, lbl
        return RESOLUTIONS[0][1], RESOLUTIONS[0][0]

    def _start(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No link", "Please paste a video link first.")
            return
        folder = self.folder_var.get().strip()
        if not os.path.isdir(folder):
            messagebox.showwarning("Bad folder", "The save folder does not exist.")
            return
        self.btn.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Starting…")
        threading.Thread(target=self._download, args=(url, folder), daemon=True).start()

    def _download(self, url, folder):
        fmt_str, fmt_label = self._fmt_label_to_format(self.res_var.get())
        is_audio = fmt_label == AUDIO_ONLY_LABEL

        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done  = d.get("downloaded_bytes", 0)
                pct   = (done / total * 100) if total else 0
                speed = d.get("_speed_str", "")
                eta   = d.get("_eta_str", "")
                self.after(0, self._update_progress, pct,
                           f"Downloading… {speed}  ETA {eta}")
            elif d["status"] == "finished":
                self.after(0, self._update_progress, 99, "Processing…")

        opts = {
            "format": fmt_str,
            "merge_output_format": "mp4" if not is_audio else None,
            "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
        }
        if is_audio:
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.after(0, self._done, True, f"Saved to: {folder}")
        except Exception as e:
            self.after(0, self._done, False, str(e))

    def _update_progress(self, pct, msg):
        self.progress["value"] = pct
        self.status_var.set(msg)

    def _done(self, ok, msg):
        self.progress["value"] = 100 if ok else 0
        self.status_var.set(msg)
        self.btn.config(state="normal")
        if ok:
            messagebox.showinfo("Done!", f"Download complete!\n\n{msg}")
        else:
            messagebox.showerror("Error", f"Download failed:\n\n{msg}")


if __name__ == "__main__":
    _check_root = tk.Tk()
    _check_root.withdraw()

    def _launch():
        _check_root.destroy()
        App().mainloop()

    ensure_dependencies(_check_root, _launch)
    _check_root.mainloop()  # keeps event loop alive while winget runs
