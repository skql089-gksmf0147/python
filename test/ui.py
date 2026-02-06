import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
import pytesseract

# Tesseract 경로 설정 (본인 경로 확인 필수)
pytesseract.pytesseract.tesseract_cmd = r'd:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_info():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if not file_path: return

    try:
        # 1. 이미지 읽기 및 OCR 실행 (숫자 위주 인식 모드 설정)
        img = Image.open(file_path)
        # --psm 6: 단일 텍스트 블록으로 인식 / --oem 3: 기본 엔진
        raw_text = pytesseract.image_to_string(img, lang='kor+eng', config='--psm 6 --oem 3')
        
        # 텍스트 정제 (공백 제거 후 대문자 변환)
        clean_text = raw_text.replace(" ", "").upper()
        log_display.delete(1.0, tk.END)
        log_display.insert(tk.END, "--- 인식된 원문 ---\n" + raw_text)

        # 2. 데이터 추출 (정규표현식 보강)
        data = {}
        
        # 제품중량: 숫자 뒤에 K가 붙거나 숫자만 있는 큼직한 부분 (2,500 형태)
        weight = re.search(r'([0-9,]{3,})\s*K?', clean_text)
        data["제품중량"] = weight.group(1) + " KG" if weight else "미검출"

        # 코일길이: 3자리 숫자 뒤에 M이 붙은 경우 (530 형태)
        length = re.search(r'(\d{3})\s*M', clean_text)
        data["코일길이"] = length.group(1) + " M" if length else "미검출"

        # 제품번호: FOG로 시작하는 문자열
        prod_no = re.search(r'FOG[A-Z0-9]+', clean_text)
        data["제품번호"] = prod_no.group(0) if prod_no else "미검출"

        # 제조일자: 날짜 형식
        date = re.search(r'(\d{4}[.\-]\d{2}[.\-]\d{2})', clean_text)
        data["제조일자"] = date.group(1) if date else "미검출"

        # 3. 결과 텍스트 구성 및 바탕화면 저장
        result_text = "=== 최종 추출 결과 ===\n"
        for k, v in data.items():
            result_text += f"{k}: {v}\n"

        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        save_path = os.path.join(desktop, "추출데이터.txt")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(result_text)

        messagebox.showinfo("완료", "바탕화면에 '추출데이터.txt'로 저장되었습니다.")

    except Exception as e:
        messagebox.showerror("오류", f"에러 발생: {e}")

# --- UI 구성 ---
root = tk.Tk()
root.title("KG 스틸 라벨 분석기 v3")
root.geometry("400x450")

btn = tk.Button(root, text="이미지 불러오기", command=extract_info, height=2, bg='#0078d7', fg='white')
btn.pack(fill=tk.X, padx=10, pady=10)

tk.Label(root, text="인식 로그 (데이터가 안 나오면 아래를 확인하세요):").pack()
log_display = scrolledtext.ScrolledText(root, height=15)
log_display.pack(padx=10, pady=10)

root.mainloop()