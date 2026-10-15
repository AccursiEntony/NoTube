
import os
import queue
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import yt_dlp


class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("760x640")
        self.root.minsize(620, 520)

        self.messages = queue.Queue()
        self.downloading = False

        self.output_dir = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        self.mode = tk.StringVar(value="video")
        self.quality = tk.StringVar(value="1080p")
        self.audio_format = tk.StringVar(value="mp3")
        self.playlist = tk.BooleanVar(value=False)

        self._build_ui()
        self.root.after(100, self._process_messages)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main, text="YouTube Downloader", font=("TkDefaultFont", 16, "bold")
        ).pack(anchor="w")

        ttk.Label(
            main,
            text="Inserisci uno o più URL, uno per riga.",
        ).pack(anchor="w", pady=(4, 8))

        self.urls = ScrolledText(main, height=5, wrap="word")
        self.urls.pack(fill="x", pady=(0, 12))

        # Modalità
        options = ttk.LabelFrame(main, text="Impostazioni download", padding=10)
        options.pack(fill="x", pady=(0, 10))

        ttk.Label(options, text="Modalità:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )

        mode_frame = ttk.Frame(options)
        mode_frame.grid(row=0, column=1, sticky="w")

        ttk.Radiobutton(
            mode_frame, text="Video", variable=self.mode,
            value="video", command=self._update_options
        ).pack(side="left", padx=(0, 12))

        ttk.Radiobutton(
            mode_frame, text="Audio", variable=self.mode,
            value="audio", command=self._update_options
        ).pack(side="left")

        ttk.Label(options, text="Qualità video:").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=5
        )

        self.quality_combo = ttk.Combobox(
            options,
            textvariable=self.quality,
            values=["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"],
            state="readonly",
            width=14,
        )
        self.quality_combo.grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(options, text="Formato audio:").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=5
        )

        self.audio_combo = ttk.Combobox(
            options,
            textvariable=self.audio_format,
            values=["mp3", "m4a", "wav", "flac"],
            state="readonly",
            width=14,
        )
        self.audio_combo.grid(row=2, column=1, sticky="w", pady=5)

        ttk.Checkbutton(
            options,
            text="Scarica la playlist intera, se presente",
            variable=self.playlist,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 2))

        options.columnconfigure(1, weight=1)

        # Cartella
        folder_frame = ttk.LabelFrame(
            main, text="Cartella di destinazione", padding=10
        )
        folder_frame.pack(fill="x", pady=(0, 10))

        ttk.Entry(
            folder_frame, textvariable=self.output_dir
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(
            folder_frame, text="Sfoglia...", command=self._choose_folder
        ).pack(side="right")

        # Avanzamento
        progress_frame = ttk.Frame(main)
        progress_frame.pack(fill="x", pady=(0, 8))

        self.status = tk.StringVar(value="Pronto")
        ttk.Label(progress_frame, textvariable=self.status).pack(anchor="w")

        self.progress = ttk.Progressbar(
            progress_frame, mode="determinate", maximum=100
        )
        self.progress.pack(fill="x", pady=(4, 0))

        # Pulsanti
        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(0, 10))

        self.start_button = ttk.Button(
            buttons, text="Avvia download", command=self._start_download
        )
        self.start_button.pack(side="left")

        ttk.Button(
            buttons, text="Pulisci log", command=self._clear_log
        ).pack(side="left", padx=8)

        # Log
        ttk.Label(main, text="Log attività:").pack(anchor="w")

        self.log = ScrolledText(main, height=12, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, pady=(4, 0))

        self._update_options()

    def _update_options(self):
        video_mode = self.mode.get() == "video"

        self.quality_combo.configure(
            state="readonly" if video_mode else "disabled"
        )
        self.audio_combo.configure(
            state="disabled" if video_mode else "readonly"
        )

    def _choose_folder(self):
        folder = filedialog.askdirectory(
            initialdir=self.output_dir.get() or os.path.expanduser("~")
        )
        if folder:
            self.output_dir.set(folder)

    def _write_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        if self.downloading:
            return
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.progress["value"] = 0
        self.status.set("Pronto")

    def _start_download(self):
        if self.downloading:
            return

        raw_text = self.urls.get("1.0", "end").strip()
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if not urls:
            messagebox.showwarning(
                "URL mancanti", "Inserisci almeno un URL YouTube."
            )
            return

        output_dir = self.output_dir.get().strip()

        if not output_dir:
            messagebox.showwarning(
                "Cartella mancante", "Seleziona una cartella di destinazione."
            )
            return

        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(
                "Errore cartella",
                f"Impossibile creare o usare la cartella:\n{exc}",
            )
            return

        if self.mode.get() == "audio" and not shutil.which("ffmpeg"):
            messagebox.showerror(
                "FFmpeg non trovato",
                "Per convertire l'audio installa FFmpeg e aggiungilo al PATH.",
            )
            return

        if self.mode.get() == "video" and not shutil.which("ffmpeg"):
            proceed = messagebox.askyesno(
                "FFmpeg non trovato",
                "FFmpeg non è disponibile nel PATH. Alcuni video potrebbero "
                "non essere uniti correttamente.\n\nVuoi continuare?"
            )
            if not proceed:
                return

        settings = {
            "urls": urls,
            "output_dir": output_dir,
            "mode": self.mode.get(),
            "quality": self.quality.get(),
            "audio_format": self.audio_format.get(),
            "playlist": self.playlist.get(),
        }

        self.downloading = True
        self.start_button.configure(state="disabled")
        self.progress["value"] = 0
        self.status.set("Avvio download...")
        self._write_log("-" * 45)
        self._write_log(f"URL da elaborare: {len(urls)}")
        self._write_log(f"Destinazione: {output_dir}")

        threading.Thread(
            target=self._download_worker,
            args=(settings,),
            daemon=True,
        ).start()

    def _download_worker(self, settings):
        urls = settings["urls"]
        total_urls = len(urls)

        for index, url in enumerate(urls, start=1):
            self.messages.put(("log", f"\n[{index}/{total_urls}] {url}"))

            def progress_hook(data, item_index=index):
                if data.get("status") == "downloading":
                    downloaded = data.get("downloaded_bytes", 0)
                    total = data.get("total_bytes") or data.get(
                        "total_bytes_estimate"
                    )

                    if total:
                        percent = downloaded / total * 100
                        self.messages.put(
                            ("progress", percent, item_index, total_urls)
                        )

                elif data.get("status") == "finished":
                    self.messages.put(
                        ("log", "Download completato; elaborazione file...")
                    )

            opts = {
                "outtmpl": os.path.join(
                    settings["output_dir"], "%(title)s.%(ext)s"
                ),
                "noplaylist": not settings["playlist"],
                "ignoreerrors": False,
                "progress_hooks": [progress_hook],
                "quiet": True,
                "no_warnings": False,
                "windowsfilenames": os.name == "nt",
            }

            if settings["mode"] == "audio":
                opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": settings["audio_format"],
                    }],
                })
            else:
                quality = settings["quality"]

                if quality == "Best":
                    opts["format"] = "bestvideo*+bestaudio/best"
                else:
                    height = int(quality.rstrip("p"))
                    opts["format"] = (
                        f"bestvideo[height<={height}]+bestaudio/"
                        f"best[height<={height}]"
                    )

                opts["merge_output_format"] = "mp4"

            try:
                with yt_dlp.YoutubeDL(opts) as downloader:
                    downloader.download([url])

                self.messages.put(("log", "Operazione terminata."))
            except Exception as exc:
                self.messages.put(("log", f"ERRORE: {exc}"))

        self.messages.put(("done",))

    def _process_messages(self):
        try:
            while True:
                message = self.messages.get_nowait()
                kind = message[0]

                if kind == "log":
                    self._write_log(message[1])

                elif kind == "progress":
                    percent, index, total = message[1:]
                    overall = ((index - 1) + percent / 100) / total * 100
                    self.progress["value"] = overall
                    self.status.set(
                        f"Download {index}/{total}: {percent:.1f}%"
                    )

                elif kind == "done":
                    self.downloading = False
                    self.start_button.configure(state="normal")
                    self.progress["value"] = 100
                    self.status.set("Operazioni terminate")
                    self._write_log("\nTutte le operazioni sono terminate.")

        except queue.Empty:
            pass

        self.root.after(100, self._process_messages)


def main():
    root = tk.Tk()
    YouTubeDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
