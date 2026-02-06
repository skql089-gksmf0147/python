import customtkinter as ctk
import json
import os
import subprocess
import sys
import threading
from tkinter import messagebox
import logging
import requests
from bs4 import BeautifulSoup

# --- 전역 설정 및 로그 ---
log_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "app.log")
logging.basicConfig(
    filename=log_path, level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s", encoding="utf-8"
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 폰트 설정
FONT_TITLE = ("NanumGothic", 45, "bold")
FONT_BUTTON = ("NanumGothic", 30, "bold")
FONT_EPISODE = ("NanumGothic", 24)

class UltraMediaCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ULTRA 미디어 센터")
        self.geometry("1100x900")

        # 상태 관리
        self.current_buttons = []
        self.current_index = 0
        self.current_frame = None
        self.current_scroll = None
        self.frame_stack = []
        self.data = self.load_data()

        # 프레임 생성
        self.frames = {}
        for name in ("main", "movie", "drama", "variety"):
            f = ctk.CTkFrame(self, fg_color="#1A1A1A")
            f.place(x=0, y=0, relwidth=1, relheight=1)
            self.frames[name] = f

        self.setup_main_menu()
        self.setup_content_pages()
        
        # 키 바인딩
        self.bind("<Up>", self.on_key)
        self.bind("<Down>", self.on_key)
        self.bind("<Return>", self.on_key)
        self.bind("<space>", self.on_key)
        self.bind("<Escape>", lambda e: self.go_back())

        self.show_frame("main", self.main_buttons)

    # --- 경로 및 데이터 로직 ---
    def get_data_path(self):
        """EXE 옆에 media.json을 저장/로드하기 위한 경로"""
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), "media.json")
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "media.json")

    def load_data(self):
        path = self.get_data_path()
        if not os.path.exists(path):
            return {"movie": [], "drama": [], "variety": []}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"데이터 로딩 실패: {e}")
            return {"movie": [], "drama": [], "variety": []}

    # --- 크롤러 엔진 (내부 통합) ---
    def run_crawler_logic(self):
        # 실제 사이트 주소와 카테고리 경로를 정확히 입력하세요
        BASE_URL = "https://mvking6.org" # 여기에 실제 베이스 URL 입력
        CATEGORIES = {
            "movie": "/video?type=movie&country=1",
            "drama": "/video?type=drama&country=1",
            "variety": "/video?type=enter&country=1"
        }
        HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        new_data = {}
        try:
            for key, path in CATEGORIES.items():
                url = BASE_URL + path
                res = requests.get(url, headers=HEADERS, timeout=15)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "html.parser")
                
                result = []
                for a in soup.select("a[href^='/video/view']"):
                    title = a.get_text(strip=True)
                    link = BASE_URL + a["href"]
                    if title and len(title) > 1:
                        result.append({"title": title, "url": link})
                new_data[key] = result

            save_path = self.get_data_path()
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"크롤링 중 에러 발생: {e}")
            return False

    def update_data_event(self):
        """데이터 갱신 버튼 클릭 시 실행"""
        def task():
            success = self.run_crawler_logic()
            if success:
                self.after(0, lambda: self.finish_update("✅ 데이터 갱신 완료!"))
            else:
                self.after(0, lambda: self.finish_update("❌ 갱신 실패! 로그를 확인하세요."))

        threading.Thread(target=task, daemon=True).start()

    def finish_update(self, msg):
        self.data = self.load_data()
        self.setup_content_pages() # 리스트 페이지 재구성
        self.show_frame("main", self.main_buttons)
        messagebox.showinfo("알림", msg)

    # --- UI 구성 로직 ---
    def setup_main_menu(self):
        frame = self.frames["main"]
        ctk.CTkLabel(frame, text="원하시는 콘텐츠를 선택하세요", font=FONT_TITLE, text_color="white").pack(pady=60)
        
        self.main_buttons = []
        menu_items = [
            ("🎬 한국 영화", lambda: self.show_frame("movie", self.movie_btns, self.movie_scr)),
            ("📺 TV 드라마", lambda: self.show_frame("drama", self.drama_btns, self.drama_scr)),
            ("🎉 인기 예능", lambda: self.show_frame("variety", self.variety_btns, self.variety_scr)),
            ("🔄 데이터 갱신", self.update_data_event)
        ]

        for text, cmd in menu_items:
            btn = ctk.CTkButton(frame, text=text, width=800, height=100, font=FONT_BUTTON, 
                                corner_radius=20, fg_color="#333333", hover_color="#FF5722", command=cmd)
            btn.pack(pady=20)
            self.main_buttons.append(btn)

    def setup_content_pages(self):
        self.movie_btns, self.movie_scr = self.create_list_page("movie", "🎬 한국 영화", self.data["movie"])
        self.drama_btns, self.drama_scr = self.create_list_page("drama", "📺 TV 드라마", self.data["drama"])
        self.variety_btns, self.variety_scr = self.create_list_page("variety", "🎉 인기 예능", self.data["variety"])

    def create_list_page(self, name, title, items):
        frame = self.frames[name]
        for widget in frame.winfo_children(): widget.destroy()

        ctk.CTkLabel(frame, text=title, font=FONT_TITLE, text_color="#FF5722").pack(pady=(40, 20))
        scroll = ctk.CTkScrollableFrame(frame, width=950, height=550, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=50, pady=10)

        buttons = []
        for item in items:
            btn = ctk.CTkButton(
                scroll, text=item["title"], height=80, font=FONT_EPISODE,
                anchor="w", fg_color="#333333", command=lambda u=item["url"]: self.watch_video(u)
            )
            btn.pack(fill="x", pady=5, padx=10)
            buttons.append(btn)

        back = ctk.CTkButton(frame, text="⬅ 뒤로가기 (ESC)", width=400, height=70, 
                             font=FONT_BUTTON, fg_color="#444444", command=self.go_back)
        back.pack(pady=30)
        buttons.append(back)
        return buttons, scroll

    # --- 제어 로직 ---
    def show_frame(self, name, buttons, scroll=None):
        if self.current_frame:
            self.frame_stack.append((self.current_frame, self.current_buttons, self.current_scroll))
        
        self.current_frame = self.frames[name]
        self.current_buttons = buttons
        self.current_scroll = scroll
        self.current_index = 0
        self.current_frame.tkraise()
        self.highlight()

    def go_back(self):
        if self.frame_stack:
            frame, buttons, scroll = self.frame_stack.pop()
            self.current_frame, self.current_buttons, self.current_scroll = frame, buttons, scroll
            self.current_index = 0
            frame.tkraise()
            self.highlight()

    def highlight(self):
        if not self.current_buttons: return
        for i, btn in enumerate(self.current_buttons):
            if i == self.current_index:
                btn.configure(fg_color="#FF5722", text_color="white")
                self.ensure_visible(btn)
            else:
                btn.configure(fg_color="#333333", text_color="#CCCCCC")

    def ensure_visible(self, btn):
        if not self.current_scroll: return
        try:
            self.update_idletasks()
            canvas = self.current_scroll._parent_canvas
            total_h = canvas.bbox("all")[3]
            canvas_h = canvas.winfo_height()
            if total_h > canvas_h:
                cur_top, cur_bottom = canvas.yview()
                btn_top = btn.winfo_y() / total_h
                btn_bottom = (btn.winfo_y() + btn.winfo_height()) / total_h
                if btn_top < cur_top: canvas.yview_moveto(btn_top)
                elif btn_bottom > cur_bottom: canvas.yview_moveto(btn_bottom - (canvas_h/total_h))
        except: pass

    def on_key(self, event):
        if not self.current_buttons: return
        if event.keysym == "Up": self.current_index = max(0, self.current_index - 1)
        elif event.keysym == "Down": self.current_index = min(len(self.current_buttons)-1, self.current_index+1)
        elif event.keysym in ("Return", "space"): self.current_buttons[self.current_index].invoke()
        self.highlight()

    def watch_video(self, url):
        def run():
            try:
                base = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
                player = os.path.join(base, "player.exe" if getattr(sys, 'frozen', False) else "player.py")
                cmd = [player, url, "1"] if getattr(sys, 'frozen', False) else [sys.executable, player, url, "1"]
                subprocess.Popen(cmd)
            except Exception as e: logging.error(f"재생 에러: {e}")
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app = UltraMediaCenter()
    app.mainloop()