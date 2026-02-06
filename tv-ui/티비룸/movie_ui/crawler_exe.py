import requests
from bs4 import BeautifulSoup
import json
import os
import re
import threading
import tkinter as tk
from tkinter import messagebox
import sys
import os

def get_base_dir():
    # EXE / py 실행 모두 대응
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ==============================
# 기본 설정
# ==============================
BASE_URL = "https://tvroom11.org"

CATEGORIES = {
    "movie": "/video?type=movie&country=1",
    "drama": "/video?type=drama&country=1",
    "variety": "/video?type=enter&country=1"
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ==============================
# 크롤링 함수
# ==============================
def crawl_category(path):
    url = BASE_URL + path
    result = []

    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.select("a[href^='/video/view']"):
            title_div = a.select_one("div.v-item-title")
            if not title_div:
                continue

            title = title_div.get_text(strip=True)
            title = re.sub(r"\s*\(\d{4}\)", "", title)  # 연도 제거
            link = BASE_URL + a["href"]

            result.append({
                "title": title,
                "url": link
            })

    except Exception as e:
        print(f"❌ 오류 발생 ({path}): {e}")

    return result


# ==============================
# 메인 작업
# ==============================
def run_automation():
    data = {}

    for key, path in CATEGORIES.items():
        update_status(f"⏳ {key} 크롤링 중...")
        data[key] = crawl_category(path)




    save_path = os.path.join(
    get_base_dir(),
    "media.json"
    )


    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return save_path


# ==============================
# GUI 상태 업데이트
# ==============================
def update_status(text, color="blue"):
    status_label.config(text=text, fg=color)
    root.update_idletasks()


def start_task():
    def task():
        try:
            save_path = run_automation()
            update_status("✅ 작업 완료", "green")
            messagebox.showinfo(
                "완료",
                f"🎉 작업이 모두 완료되었습니다!\n\n저장 위치:\n{save_path}"
            )
        except Exception as e:
            update_status("❌ 오류 발생", "red")
            messagebox.showerror("에러", str(e))

    threading.Thread(target=task, daemon=True).start()


# ==============================
# Tkinter UI
# ==============================
root = tk.Tk()
root.title("미디어 크롤링 자동화")
root.geometry("380x160")
root.resizable(False, False)

status_label = tk.Label(
    root,
    text="⏳ 작업 중...",
    font=("맑은 고딕", 14, "bold"),
    fg="blue"
)
status_label.pack(pady=45)

# 프로그램 실행 시 자동 시작
root.after(100, start_task)

root.mainloop()
