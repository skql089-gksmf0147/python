import customtkinter as ctk
import json
import os
import sys
import threading
import subprocess
from tkinter import messagebox

# ==============================
# UI 기본 설정
# ==============================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_TITLE = ("NanumGothic", 45, "bold")
FONT_BUTTON = ("NanumGothic", 30, "bold")
FONT_EPISODE = ("NanumGothic", 24)

# ==============================
# 전역 상태
# ==============================
current_frame = None
current_buttons = []
current_index = 0
current_scroll = None
frame_stack = []

# ==============================
# exe / python 공용 경로
# ==============================
def resource_path(relative):
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative)

# ==============================
# media.json 로드
# ==============================
def load_media_list():
    path = resource_path("media.json")

    if not os.path.exists(path):
        messagebox.showerror("오류", f"media.json 없음\n{path}")
        return {"movie": [], "drama": [], "variety": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        return {
            "movie": raw.get("movie", []),
            "drama": raw.get("drama", []),
            "variety": raw.get("variety", [])
        }
    except Exception as e:
        messagebox.showerror("JSON 오류", str(e))
        return {"movie": [], "drama": [], "variety": []}

# ==============================
# 키보드 네비게이션
# ==============================
def highlight():
    if not current_buttons:
        return

    for i, btn in enumerate(current_buttons):
        btn.configure(
            fg_color="#FF5722" if i == current_index else "#333333",
            text_color="white" if i == current_index else "#CCCCCC"
        )

   
   #⭐ 완전 안정적인 최종 스크롤 함수 (추천)

    scroll_to_current()

def scroll_to_current():
    if not current_scroll or not current_buttons:
        return

    btn = current_buttons[current_index]
    canvas = current_scroll._parent_canvas
    canvas.update_idletasks()

    # 전체 스크롤 영역
    scroll_region = canvas.bbox("all")
    if not scroll_region:
        return

    total_height = scroll_region[3]
    view_height = canvas.winfo_height()

    btn_y = btn.winfo_y()
    btn_h = btn.winfo_height()

    # 현재 보이는 영역
    view_top = canvas.canvasy(0)
    view_bottom = view_top + view_height

    TOP_MARGIN = 60
    BOTTOM_MARGIN = 60

    # 🔼 위로 넘어갈 때
    if btn_y < view_top + TOP_MARGIN:
        new_top = btn_y - TOP_MARGIN

    # 🔽 아래로 넘어갈 때
    elif btn_y + btn_h > view_bottom - BOTTOM_MARGIN:
        new_top = btn_y + btn_h - view_height + BOTTOM_MARGIN

    else:
        return  # 화면 안 → 스크롤 안 함

    # 🚫 범위 초과 방지
    new_top = max(0, min(new_top, total_height - view_height))

    # ✅ 비율 기반 이동 (페이지 경계에서도 안정적)
    canvas.yview_moveto(new_top / total_height)



def on_key(event):
    global current_index

    if not current_buttons:
        return

    if event.keysym == "Up":
        current_index = max(0, current_index - 1)

    elif event.keysym == "Down":
        current_index = min(len(current_buttons) - 1, current_index + 1)

    elif event.keysym in ("Return", "space"):
        current_buttons[current_index].invoke()

    elif event.keysym == "Escape":
        go_back()

    highlight()

def show_frame(frame, buttons, scroll=None):
    global current_frame, current_buttons, current_index, current_scroll

    if current_frame:
        frame_stack.append((current_frame, current_buttons, current_scroll))

    current_frame = frame
    current_buttons = buttons
    current_scroll = scroll
    current_index = 0

    frame.tkraise()
    highlight()

def go_back():
    global current_frame, current_buttons, current_scroll, current_index

    if not frame_stack:
        return

    frame, buttons, scroll = frame_stack.pop()

    current_frame = frame
    current_buttons = buttons
    current_scroll = scroll
    current_index = 0

    frame.tkraise()
    highlight()

# ==============================
# 영상 실행
# ==============================
def watch_video(url):
    def run():
        try:
            if getattr(sys, "frozen", False):
                subprocess.Popen([resource_path("player.exe"), url])
            else:
                subprocess.Popen([sys.executable, resource_path("player.py"), url])
        except Exception as e:
            messagebox.showerror("재생 오류", str(e))

    threading.Thread(target=run, daemon=True).start()

# ==============================
# 리스트 페이지 생성
# ==============================
def create_list_page(frame, title, items):
    for w in frame.winfo_children():
        w.destroy()

    ctk.CTkLabel(frame, text=title, font=FONT_TITLE, text_color="#FF5722").pack(pady=40)

    scroll = ctk.CTkScrollableFrame(frame, width=900, height=550)
    scroll.pack(expand=True, fill="both", padx=50)

    buttons = []

    for item in items:
        btn = ctk.CTkButton(
            scroll,
            text=item.get("title", "제목 없음"),
            height=80,
            font=FONT_EPISODE,
            fg_color="#333333",
            anchor="w",
            command=lambda u=item["url"]: watch_video(u)
        )
        btn.pack(fill="x", pady=5)
        buttons.append(btn)

    back_btn = ctk.CTkButton(
        frame,
        text="⬅ 뒤로가기 (ESC)",
        height=70,
        width=400,
        font=FONT_BUTTON,
        fg_color="#444444",
        command=go_back
    )
    back_btn.pack(pady=30)
    buttons.append(back_btn)

    return buttons, scroll

# ==============================
# 앱 초기화
# ==============================
app = ctk.CTk()
app.title("티비룸")
app.geometry("1100x900")

main_frame = ctk.CTkFrame(app)
movie_frame = ctk.CTkFrame(app)
drama_frame = ctk.CTkFrame(app)
variety_frame = ctk.CTkFrame(app)

for f in (main_frame, movie_frame, drama_frame, variety_frame):
    f.place(relwidth=1, relheight=1)

data = load_media_list()

movie_btns, movie_scr = create_list_page(movie_frame, "🎬 영화", data["movie"])
drama_btns, drama_scr = create_list_page(drama_frame, "📺 드라마", data["drama"])
variety_btns, variety_scr = create_list_page(variety_frame, "🎉 예능", data["variety"])

# ==============================
# 메인 메뉴
# ==============================
main_buttons = []

ctk.CTkLabel(main_frame, text="티비룸", font=FONT_TITLE).pack(pady=60)

menu = [
    ("🎬 영화", lambda: show_frame(movie_frame, movie_btns, movie_scr)),
    ("📺 드라마", lambda: show_frame(drama_frame, drama_btns, drama_scr)),
    ("🎉 예능", lambda: show_frame(variety_frame, variety_btns, variety_scr))
]

for text, cmd in menu:
    b = ctk.CTkButton(
        main_frame,
        text=text,
        height=100,
        width=800,
        font=FONT_BUTTON,
        command=cmd
    )
    b.pack(pady=20)
    main_buttons.append(b)

show_frame(main_frame, main_buttons)

# ==============================
# 키 바인딩 & 포커스
# ==============================
for k in ("<Up>", "<Down>", "<Return>", "<space>", "<Escape>"):
    app.bind(k, on_key)

app.after(100, app.focus_force)

app.mainloop()
