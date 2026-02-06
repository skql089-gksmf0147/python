import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://mvking6.org"

CATEGORIES = {
    "movie": "/video?type=movie&country=1",
    "drama": "/video?type=drama&country=1",
    "variety": "/video?type=enter&country=1"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def crawl_category(path):
    url = BASE_URL + path
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        result = []

        # mvking6 구조에 맞는 셀렉터 (일반적인 리스트 a 태그 추출)
        for a in soup.select("a[href^='/video/view']"):
            title = a.get_text(strip=True)
            link = BASE_URL + a["href"]
            if title and len(title) > 1:
                result.append({"title": title, "url": link})
        return result
    except Exception as e:
        print(f"오류 발생 ({path}): {e}")
        return []

def main():
    data = {}
    for key, path in CATEGORIES.items():
        print(f"[+] 크롤링 시작: {key}...")
        data[key] = crawl_category(path)

    # UI 경로와 맞추기 위해 현재 파일 위치 기준 저장
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {save_path} 갱신 완료")

if __name__ == "__main__":
    main()