import yt_dlp
import os
import sys

def scarica_video(url: str, cartella: str = "downloads", solo_audio: bool = False, qualita: str = "best"):
    """
    Scarica un video (o solo audio) da YouTube.

    Args:
        url:        URL del video o della playlist
        cartella:   Cartella di destinazione (default: ./downloads)
        solo_audio: Se True, scarica solo l'audio in formato MP3
        qualita:    Qualità video: 'best', '1080', '720', '480', '360'
    """
    os.makedirs(cartella, exist_ok=True)

    if solo_audio:
        formato = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        if qualita == "best":
            formato = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            # Es: qualita="720" → scarica il video più vicino a 720p
            formato = f"bestvideo[height<={qualita}][ext=mp4]+bestaudio[ext=m4a]/best[height<={qualita}][ext=mp4]/best"
        postprocessors = []

    opzioni = {
        "format": formato,
        "outtmpl": os.path.join(cartella, "%(title)s.%(ext)s"),
        "postprocessors": postprocessors,
        "noplaylist": False,          # metti True per scaricare solo il video anche se l'URL è una playlist
        "progress_hooks": [_progresso],
        "quiet": False,
        "no_warnings": False,
    }

    print(f"\n{'='*50}")
    print(f"URL:      {url}")
    print(f"Cartella: {os.path.abspath(cartella)}")
    print(f"Tipo:     {'Solo audio (MP3)' if solo_audio else f'Video ({qualita})'}")
    print(f"{'='*50}\n")

    with yt_dlp.YoutubeDL(opzioni) as ydl:
        ydl.download([url])

    print("\nDownload completato!")


def _progresso(d: dict):
    """Callback per mostrare il progresso del download."""
    if d["status"] == "downloading":
        scaricato = d.get("_downloaded_bytes_str", "?")
        totale    = d.get("_total_bytes_str") or d.get("_total_bytes_estimate_str", "?")
        velocita  = d.get("_speed_str", "?")
        eta       = d.get("_eta_str", "?")
        print(f"\r  {scaricato} / {totale}  |  {velocita}  |  ETA: {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\n  File salvato: {d['filename']}")


def main():
    # ------------------------------------------------------------------ #
    #  Modifica qui per uso veloce senza riga di comando                  #
    # ------------------------------------------------------------------ #
    DEFAULT_URL      = ""          # incolla qui l'URL se non vuoi usare la CLI
    DEFAULT_CARTELLA = "downloads"
    DEFAULT_AUDIO    = False       # True = solo MP3
    DEFAULT_QUALITA  = "best"      # oppure: "1080", "720", "480", "360"
    # ------------------------------------------------------------------ #

    args = sys.argv[1:]

    if args:
        url       = args[0]
        cartella  = args[1] if len(args) > 1 else DEFAULT_CARTELLA
        solo_audio = "--audio" in args or "-a" in args
        qualita   = next((a for a in args if a.isdigit()), DEFAULT_QUALITA)
    elif DEFAULT_URL:
        url        = DEFAULT_URL
        cartella   = DEFAULT_CARTELLA
        solo_audio = DEFAULT_AUDIO
        qualita    = DEFAULT_QUALITA
    else:
        print("Uso:")
        print("  python youtube_downloader.py <URL> [cartella] [--audio] [qualità]")
        print()
        print("Esempi:")
        print("  python youtube_downloader.py https://youtu.be/xxxxxxxxxxx")
        print("  python youtube_downloader.py https://youtu.be/xxxxxxxxxxx video 720")
        print("  python youtube_downloader.py https://youtu.be/xxxxxxxxxxx musica --audio")
        sys.exit(0)

    scarica_video(url, cartella, solo_audio, qualita)


if __name__ == "__main__":
    main()