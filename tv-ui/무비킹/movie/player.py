import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

def play_video_and_fullscreen(driver, wait):
    """더 강력한 대기 및 강제 재생/전체화면 로직"""
    try:
        # 1. iframe이 완전히 로드될 때까지 충분히 대기
        time.sleep(3) 
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        target_iframe = None
        for f in iframes:
            src = f.get_attribute("src") or ""
            if "player" in src:
                target_iframe = f; break
        
        if target_iframe:
            driver.switch_to.frame(target_iframe)
            print("✅ 플레이어 iframe 진입")
            
            # 2. 비디오 태그가 나타날 때까지 대기
            video = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            
            # 3. 강제 재생 (JS + 직접 클릭 병행)
            # 많은 사이트가 직접적인 클릭이 있어야 재생을 허용합니다.
            driver.execute_script("arguments[0].muted = true; arguments[0].play();", video)
            ActionChains(driver).move_to_element(video).click().perform()
            
            # 4. 전체화면 (DPlayer API 강제 호출)
            print("⛶ 전체화면 전환 시도 중...")
            time.sleep(1)
            # 버튼 클릭보다 더 확실한 API 직접 명령
            driver.execute_script("""
                if(window.dp) {
                    dp.play();
                    dp.fullScreen.request('browser');
                } else {
                    document.querySelector('.dplayer-full-icon').click();
                }
            """)
            
            # 5. 소리 켜기
            time.sleep(1)
            driver.execute_script("arguments[0].muted = false;", video)
            
            print("✅ 전체화면 및 재생 시작 완료")
            driver.switch_to.default_content() 
    except Exception as e:
        print(f"⚠️ 재생 실행 중 오류: {e}")
        driver.switch_to.default_content()

# --- 메인 실행 ---
url = sys.argv[1] if len(sys.argv) > 1 else ""
options = Options()
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_argument("--autoplay-policy=no-user-gesture-required") # 자동재생 제한 완화 옵션

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)
driver.get(url)

# ==================================================
# 1️⃣ [수정 완료] 1회를 정확하게 찾아서 재시도하며 클릭하기
# ==================================================

def click_play_button(driver):
    # --- 설정 값 ---
    max_retries = 3
    wait_time = 30  
    
    # 찾고자 하는 1회 버튼의 XPath (정확도 향상)
    target_xpath = (
        "//a[contains(@class, 'eps_a') and ("
        "normalize-space(text())='제1회' or "
        "normalize-space(text())='1회' or "
        "normalize-space(text())='제01회' or "
        "normalize-space(text())='본편' or "
        "contains(text(), '제01회 ')" 
        ")]"
    )

    for i in range(max_retries):
        try:
            print(f"🔎 {i+1}회차 버튼 찾는 중...")
            wait = WebDriverWait(driver, wait_time)
            
            # 1. XPath를 사용하여 실제 1회 버튼이 나타날 때까지 대기
            play_btn = wait.until(EC.presence_of_element_located((By.XPATH, target_xpath)))
            
            # 2. 화면 중앙으로 스크롤하여 안정화
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", play_btn)
            time.sleep(1.5) 
            
            # 3. 클릭 시도 (일반 클릭 -> 실패 시 자바스크립트 클릭)
            try:
                play_btn.click()
            except:
                driver.execute_script("arguments[0].click();", play_btn)
                
            print("✅ 1회 버튼 클릭 성공!")
            return True
            
        except (StaleElementReferenceException, TimeoutException):
            print(f"⚠️ {i+1}회차 실패: 버튼을 못 찾았거나 페이지 변화 발생. 재시도합니다.")
            driver.refresh() 
            time.sleep(3) # 새로고침 후 충분한 대기 시간
            continue
            
    print("❌ 3회 시도 모두 실패했습니다.")
    return False

# --- 실제 호출 부분 ---
# click_play_button(driver)

# 2️⃣ 재생 및 전체화면 실행
play_video_and_fullscreen(driver, wait)

# 3️⃣ 자동 다음 회차 루프
while True:
    try:
        # 종료 감시 로직 (기존과 동일)
        time.sleep(5)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for f in iframes:
            if "player" in (f.get_attribute("src") or ""):
                driver.switch_to.frame(f)
                is_ended = driver.execute_script("return document.querySelector('video') ? document.querySelector('video').ended : false;")
                driver.switch_to.default_content()
                if is_ended:
                    print("🏁 영상 종료! 다음 회차 이동.")
                    next_ep = driver.find_element(By.XPATH, "//div[contains(@class, 'active')]/preceding-sibling::div[1]//a")
                    driver.execute_script("arguments[0].click();", next_ep)
                    time.sleep(5)
                    play_video_and_fullscreen(driver, wait)
                break
    except:
        continue