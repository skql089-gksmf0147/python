import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import pyperclip


# -------------------------------
# 실행 위치 기준 경로 (PyInstaller 대응)
# -------------------------------
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg.exe")

# -------------------------------
# 기본 저장 폴더: 바탕화면
# -------------------------------
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")


class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("520x300")
        self.root.resizable(False, False)

        self.url_var = tk.StringVar()
        self.format_var = tk.StringVar(value="mp3")
        self.progress_var = tk.DoubleVar(value=0)
        self.percent_var = tk.StringVar(value="0%")

        self.build_ui()

    # -------------------------------
    # UI
    # -------------------------------
    def build_ui(self):
        pad = {"padx": 10, "pady": 6}

        ttk.Label(self.root, text="YouTube URL").pack(anchor="w", **pad)

        url_frame = ttk.Frame(self.root)
        url_frame.pack(fill="x", **pad)

        ttk.Entry(url_frame, textvariable=self.url_var).pack(
            side="left", fill="x", expand=True
        )

        ttk.Button(
            url_frame, text="📋 붙여넣기", width=10, command=self.paste_clipboard
        ).pack(side="right", padx=5)

        format_frame = ttk.Frame(self.root)
        format_frame.pack(anchor="w", **pad)

        ttk.Radiobutton(
            format_frame, text="MP3 (기본)", variable=self.format_var, value="mp3"
        ).pack(side="left", padx=5)

        ttk.Radiobutton(
            format_frame, text="MP4", variable=self.format_var, value="mp4"
        ).pack(side="left", padx=5)

        ttk.Label(self.root, text=f"저장 위치: {DESKTOP}").pack(anchor="w", **pad)

        # 진행바
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill="x", **pad)

        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(side="left", fill="x", expand=True)

        ttk.Label(progress_frame, textvariable=self.percent_var, width=6).pack(
            side="right", padx=5
        )

        ttk.Button(
            self.root, text="⬇ 다운로드", command=self.start_download
        ).pack(pady=15)

    # -------------------------------
    # 클립보드
    # -------------------------------
    def paste_clipboard(self):
        try:
            self.url_var.set(pyperclip.paste())
        except:
            messagebox.showerror("오류", "클립보드 접근 실패")

    # -------------------------------
    # 다운로드 시작
    # -------------------------------
    def start_download(self):
        url = self.url_var.get().strip()

        if not url:
            messagebox.showwarning("경고", "URL을 입력하세요")
            return

        self.progress_var.set(0)
        self.percent_var.set("0%")

        threading.Thread(target=self.download, args=(url,), daemon=True).start()

    # -------------------------------
    # 진행률 콜백
    # -------------------------------
    def progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes")

            if total and downloaded:
                percent = downloaded / total * 100
                self.root.after(0, self.update_progress, percent)

        elif d["status"] == "finished":
            self.root.after(0, self.update_progress, 100)

    def update_progress(self, percent):
        self.progress_var.set(percent)
        self.percent_var.set(f"{int(percent)}%")

    # -------------------------------
    # 실제 다운로드
    # -------------------------------
    def download(self, url):
        try:
            common_opts = {
                "outtmpl": os.path.join(DESKTOP, "%(title)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "ffmpeg_location": FFMPEG_PATH,
                "progress_hooks": [self.progress_hook],
            }

            if self.format_var.get() == "mp3":
                ydl_opts = {
                    **common_opts,
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            else:
                ydl_opts = {
                    **common_opts,
                    "format": "best[ext=mp4]/best",
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.root.after(
                0, lambda: messagebox.showinfo("완료", "다운로드 완료!")
            )

        except Exception as e:
            self.root.after(
                0, lambda: messagebox.showerror("오류", str(e))
            )


# -------------------------------
# 실행
# -------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
