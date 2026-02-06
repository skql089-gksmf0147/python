import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

def select_folder():
    folder = filedialog.askdirectory(title="백업할 폴더 선택")
    if folder:
        folder_path.set(folder)

def backup_drivers():
    path = folder_path.get()
    if not path:
        messagebox.showwarning("경고", "먼저 백업할 폴더를 선택하세요.")
        return

    if not os.path.exists(path):
        os.makedirs(path)

    try:
        messagebox.showinfo("시작", "드라이버 백업을 시작합니다.\n완료까지 시간이 걸릴 수 있습니다.")
        subprocess.run(f'pnputil /export-driver * "{path}"', shell=True, check=True)
        messagebox.showinfo("완료", f"✅ 드라이버 백업이 완료되었습니다!\n\n경로: {path}")
    except subprocess.CalledProcessError:
        messagebox.showerror("오류", "드라이버 백업 중 문제가 발생했습니다.\n관리자 권한으로 실행했는지 확인하세요.")

def restore_drivers():
    path = folder_path.get()
    if not path:
        messagebox.showwarning("경고", "복원할 드라이버 폴더를 선택하세요.")
        return

    if not os.path.exists(path):
        messagebox.showerror("오류", "해당 경로가 존재하지 않습니다.")
        return

    try:
        messagebox.showinfo("시작", "드라이버 복원을 시작합니다.\n완료까지 시간이 걸릴 수 있습니다.")
        subprocess.run(f'pnputil /add-driver "{path}\\*.inf" /subdirs /install', shell=True, check=True)
        messagebox.showinfo("완료", "✅ 드라이버 복원이 완료되었습니다!")
    except subprocess.CalledProcessError:
        messagebox.showerror("오류", "복원 중 오류가 발생했습니다.\n관리자 권한으로 실행했는지 확인하세요.")

# GUI 설정
root = tk.Tk()
root.title("드라이버 백업 및 복원 도구")
root.geometry("420x250")
root.resizable(False, False)

folder_path = tk.StringVar()

tk.Label(root, text="🧩 드라이버 백업 및 복원", font=("맑은 고딕", 14, "bold")).pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Entry(frame, textvariable=folder_path, width=40).grid(row=0, column=0, padx=5)
tk.Button(frame, text="폴더 선택", command=select_folder).grid(row=0, column=1, padx=5)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=20)

tk.Button(btn_frame, text="드라이버 백업", width=15, bg="#4CAF50", fg="white",
          font=("맑은 고딕", 10, "bold"), command=backup_drivers).grid(row=0, column=0, padx=10)

tk.Button(btn_frame, text="드라이버 복원", width=15, bg="#2196F3", fg="white",
          font=("맑은 고딕", 10, "bold"), command=restore_drivers).grid(row=0, column=1, padx=10)

tk.Label(root, text="⚠️ 관리자 권한으로 실행해야 정상 작동합니다.", fg="gray").pack(pady=5)

root.mainloop()
