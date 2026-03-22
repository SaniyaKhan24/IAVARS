from typing import Optional


def download_video(url: str, output_folder: str) -> Optional[int]:
    """Download a single video and return yt-dlp exit code when available."""
    try:
        import yt_dlp
    except ImportError as exc:
        raise ImportError(
            "yt_dlp is required for video downloads. Install it with: pip install yt-dlp"
        ) from exc

    ydl_opts = {
        "outtmpl": f"{output_folder}/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([url])


# Backward-compatible alias.
video = download_video
