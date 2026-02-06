import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import pyperclip
import os
import threading

class UltimateDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Single Downloader")
        self.root.geometry("500x320")
        self.root.resizable(False, False)

        # --- 1. 링크 입력 섹션 ---
        tk.Label(root, text="유튜브 영상 링크", font=("Malgun Gothic", 10, "bold")).pack(pady=(20, 5))
        
        input_frame = tk.Frame(root)
        input_frame.pack(fill="x", padx=40)

        # 입력창 설정
        self.url_entry = tk.Entry(input_frame, font=("Arial", 11), fg="#333333")
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        # [핵심 UX 1] 클릭 시 전체 선택 이벤트 바인딩
        self.url_entry.bind("<FocusIn>", self.select_all)
        self.url_entry.bind("<Button-1>", self.select_all)

        # [핵심 UX 2] 붙여넣기 버튼 추가
        self.paste_btn = tk.Button(input_frame, text="붙여넣기", command=self.paste_from_clipboard, bg="#eeeeee")
        self.paste_btn.pack(side="right", padx=(5, 0))

        # 프로그램 시작 시 클립보드 자동 확인
        self.auto_check_clipboard()

        # --- 2. 포맷 선택 (MP3/MP4) ---
        self.format_var = tk.StringVar(value="mp3")
        radio_frame = tk.Frame(root)
        radio_frame.pack(pady=20)
        
        tk.Radiobutton(radio_frame, text="MP3 (음원 추출)", variable=self.format_var, value="mp3", font=("Malgun Gothic", 9)).pack(side="left", padx=20)
        tk.Radiobutton(radio_frame, text="MP4 (영상 다운)", variable=self.format_var, value="mp4", font=("Malgun Gothic", 9)).pack(side="left", padx=20)

        # --- 3. 진행바 ---
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100, length=420)
        self.progress_bar.pack(pady=5)
        
        self.status_label = tk.Label(root, text="대기 중...", fg="gray")
        self.status_label.pack()

        # --- 4. 다운로드 버튼 ---
        self.download_btn = tk.Button(root, text="다운로드 시작", command=self.start_download, 
                                     bg="#237BFF", fg="white", font=("Malgun Gothic", 12, "bold"), 
                                     height=2, width=25, cursor="hand2")
        self.download_btn.pack(pady=20)

    # [UX 로직] 클릭 시 전체 선택
    def select_all(self, event=None):
        self.url_entry.select_range(0, tk.END)
        self.url_entry.icursor(tk.END)

    # [UX 로직] 클립보드 내용을 입력창에 붙여넣기
    def paste_from_clipboard(self):
        text = pyperclip.paste().strip()
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, text)
        self.status_label.config(text="클립보드에서 링크를 가져왔습니다.", fg="green")

    def auto_check_clipboard(self):
        clip = pyperclip.paste().strip()
        if "youtu" in clip:
            self.url_entry.insert(0, clip)
            self.url_entry.focus_set()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p_str = d.get('_percent_str', '0%').replace('%','')
                p_float = float(''.join(c for c in p_str if c.isdigit() or c == '.'))
                self.progress_var.set(p_float)
                self.status_label.config(text=f"진행 중: {p_float:.1f}%", fg="#cc0000")
                self.root.update_idletasks()
            except: pass
        elif d['status'] == 'finished':
            self.status_label.config(text="저장 중... 잠시만 기다려주세요.", fg="blue")

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("입력 오류", "유튜브 링크를 입력하거나 붙여넣어 주세요.")
            return
        
        self.download_btn.config(state="disabled", text="처리 중...")
        threading.Thread(target=self.download_process, args=(url,), daemon=True).start()

    def download_process(self, url):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        save_format = self.format_var.get()

        ydl_opts = {
            'progress_hooks': [self.progress_hook],
            'outtmpl': f'{desktop}/%(title)s.%(ext)s',
            'noplaylist': True,
        }

        if save_format == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'})

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("완료", "바탕화면에 저장이 성공적으로 끝났습니다!")
        except Exception as e:
            messagebox.showerror("오류", "다운로드에 실패했습니다. 링크를 다시 확인해주세요.")
        finally:
            self.progress_var.set(0)
            self.status_label.config(text="대기 중...", fg="gray")
            self.download_btn.config(state="normal", text="다운로드")

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateDownloader(root)
    root.mainloop()