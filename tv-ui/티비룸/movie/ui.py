import customtkinter as ctk
import json
import os
import subprocess
import sys
import threading
from tkinter import messagebox

# 설정: 테마 및 초기화
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 전역 상태
current_buttons = []
current_index = 0
current_frame = None
current_scroll = None
frame_stack = []
data = {"movie": [], "drama": [], "variety": []}

# 폰트 설정
FONT_TITLE = ("NanumGothic", 45, "bold")
FONT_BUTTON = ("NanumGothic", 30, "bold")
FONT_EPISODE = ("NanumGothic", 24)

# ==================================================
# 유틸리티 로직
# ==================================================
def resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def load_data():
    path = resource_path("media.json")
    if not os.path.exists(path):
        return {"movie": [], "drama": [], "variety": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def watch_video(url):
    def run_player():
        try:
            subprocess.Popen([sys.executable, "player.py", url, "1"])
        except Exception as e:
            print(f"실행 에러: {e}")
    threading.Thread(target=run_player, daemon=True).start()

# ==================================================
# 핵심: 하이라이트 및 자동 스크롤 추적
# ==================================================
def highlight():
    global current_index, current_buttons, current_scroll
    if not current_buttons: return
    
    # 1. 시각적 강조
    target_btn = None
    for i, btn in enumerate(current_buttons):
        if i == current_index:
            btn.configure(fg_color="#FF5722", text_color="white")
            target_btn = btn
        else:
            btn.configure(fg_color="#333333", text_color="#CCCCCC")

    # 2. 스크롤 추적 (스크롤 프레임이 있는 리스트 화면에서만 작동)
    if current_scroll and target_btn:
        try:
            app.update_idletasks()
            # CTkScrollableFrame의 내부 캔버스와 프레임 가져오기
            canvas = current_scroll._parent_canvas
            # 버전에 따라 다른 내부 프레임 속성 대응
            inner_frame = getattr(current_scroll, "_scrollable_label", None) or current_scroll._parent_canvas.find_all()[0]
            
            # 버튼 위치 정보
            button_y = target_btn.winfo_y()
            button_h = target_btn.winfo_height()
            
            # 스크롤 영역 정보
            canvas_h = canvas.winfo_height()
            total_h = canvas.bbox("all")[3] # 전체 콘텐츠 높이
            
            if total_h > canvas_h:
                # 현재 뷰포트의 상단/하단 비율
                cur_top, cur_bottom = canvas.yview()
                
                # 버튼의 상대적 비율 위치
                btn_top_rel = button_y / total_h
                btn_bottom_rel = (button_y + button_h) / total_h
                
                # 화면 밖으로 나갔을 때 이동
                if btn_top_rel < cur_top:
                    canvas.yview_moveto(btn_top_rel)
                elif btn_bottom_rel > cur_bottom:
                    # 화면 하단에 맞추기 (버튼 위치에서 화면 크기만큼 뺌)
                    canvas.yview_moveto(btn_bottom_rel - (canvas_h / total_h))
        except Exception as e:
            print(f"스크롤 에러 무시: {e}")

# ==================================================
# 이벤트 및 프레임 제어
# ==================================================
def on_key(event):
    global current_index, current_buttons
    if not current_buttons: return
    
    if event.keysym == "Up":
        current_index = max(0, current_index - 1)
        highlight()
    elif event.keysym == "Down":
        current_index = min(len(current_buttons) - 1, current_index + 1)
        highlight()
    elif event.keysym in ("Return", "space"):
        current_buttons[current_index].invoke()
    elif event.keysym == "Escape":
        go_back()

def show_frame(frame, buttons, scroll=None):
    global current_buttons, current_index, current_frame, current_scroll
    if current_frame:
        frame_stack.append((current_frame, current_buttons, current_scroll))
    current_frame, current_buttons, current_scroll = frame, buttons, scroll
    current_index = 0
    frame.tkraise()
    highlight()

def go_back():
    global current_frame, current_buttons, current_scroll, current_index
    if frame_stack:
        frame, buttons, scroll = frame_stack.pop()
        current_frame, current_buttons, current_scroll = frame, buttons, scroll
        current_index = 0
        frame.tkraise()
        highlight()

def create_list_page(frame, title, items):
    for widget in frame.winfo_children():
        widget.destroy()

    ctk.CTkLabel(frame, text=title, font=FONT_TITLE, text_color="#FF5722").pack(pady=(40, 20))
    scroll = ctk.CTkScrollableFrame(frame, width=950, height=550, fg_color="transparent")
    scroll.pack(expand=True, fill="both", padx=50, pady=10)

    buttons = []
    for item in items:
        btn = ctk.CTkButton(
            scroll, text=item["title"], height=80, font=FONT_EPISODE,
            anchor="w", fg_color="#333333", command=lambda u=item["url"]: watch_video(u)
        )
        btn.pack(fill="x", pady=5, padx=10)
        buttons.append(btn)

    back = ctk.CTkButton(frame, text="⬅ 뒤로가기 (ESC)", width=400, height=70, 
                         font=FONT_BUTTON, fg_color="#444444", command=go_back)
    back.pack(pady=30)
    buttons.append(back)
    return buttons, scroll

# ==================================================
# 메인 윈도우 구성
# ==================================================
app = ctk.CTk()
app.title("티비룸")
app.geometry("1100x900")

main_frame = ctk.CTkFrame(app, fg_color="#1A1A1A")
movie_frame = ctk.CTkFrame(app, fg_color="#1A1A1A")
drama_frame = ctk.CTkFrame(app, fg_color="#1A1A1A")
variety_frame = ctk.CTkFrame(app, fg_color="#1A1A1A")
for f in (main_frame, movie_frame, drama_frame, variety_frame):
    f.place(x=0, y=0, relwidth=1, relheight=1)

def setup_content_pages():
    global movie_btns, movie_scr, drama_btns, drama_scr, variety_btns, variety_scr
    movie_btns, movie_scr = create_list_page(movie_frame, "🎬 영화", data["movie"])
    drama_btns, drama_scr = create_list_page(drama_frame, "📺 드라마", data["drama"])
    variety_btns, variety_scr = create_list_page(variety_frame, "🎉 예능", data["variety"])

data = load_data()
setup_content_pages()

# 메인 메뉴
main_buttons = []
ctk.CTkLabel(main_frame, text="티비룸", font=FONT_TITLE, text_color="white").pack(pady=60)
menu_items = [
    ("🎬 영화", lambda: show_frame(movie_frame, movie_btns, movie_scr)),
    ("📺 드라마", lambda: show_frame(drama_frame, drama_btns, drama_scr)),
    ("🎉 예능", lambda: show_frame(variety_frame, variety_btns, variety_scr)),
    ("🔄 데이터 갱신", lambda: threading.Thread(target=lambda: subprocess.run([sys.executable, "crawler.py"]), daemon=True).start())
]

for text, cmd in menu_items:
    btn = ctk.CTkButton(main_frame, text=text, width=800, height=100, font=FONT_BUTTON, 
                        corner_radius=20, fg_color="#333333", hover_color="#FF5722", command=cmd)
    btn.pack(pady=20)
    main_buttons.append(btn)

app.bind("<Up>", on_key)
app.bind("<Down>", on_key)
app.bind("<Return>", on_key)
app.bind("<space>", on_key)
app.bind("<Escape>", on_key)

show_frame(main_frame, main_buttons)
app.mainloop()