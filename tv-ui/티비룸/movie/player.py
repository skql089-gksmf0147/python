import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException


# ==================================================
# ▶ WebDriver 세션 생존 체크
# ==================================================
def is_driver_alive(driver):
    try:
        _ = driver.current_url
        return True
    except WebDriverException:
        return False


# ==================================================
# ▶ 재생 + 전체화면 (안정판)
# ==================================================
def play_video_and_fullscreen(driver):
    try:
        time.sleep(3)

        iframe = None
        for f in driver.find_elements(By.TAG_NAME, "iframe"):
            if "player" in (f.get_attribute("src") or ""):
                iframe = f
                break

        if not iframe:
            print("❌ 플레이어 iframe 없음")
            return False

        # iframe 포커스 확보 (사용자 제스처)
        driver.execute_script("arguments[0].scrollIntoView(true);", iframe)
        ActionChains(driver).move_to_element(iframe).click().perform()

        driver.switch_to.frame(iframe)
        print("✅ 플레이어 iframe 진입")

        wait = WebDriverWait(driver, 20)
        video = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))

        # 재생 (자동재생 우회)
        driver.execute_script("""
            arguments[0].muted = true;
            arguments[0].play();
        """, video)

        time.sleep(1)

        # 전체화면 (버튼 우선)
        try:
            fs_btn = driver.find_element(By.CSS_SELECTOR, ".dplayer-full-icon")
            fs_btn.click()
        except:
            driver.execute_script("""
                if (window.dp) {
                    dp.play();
                    dp.fullScreen.request('browser');
                }
            """)

        time.sleep(1)
        driver.execute_script("arguments[0].muted = false;", video)

        print("✅ 재생 + 전체화면 완료")
        driver.switch_to.default_content()
        return True

    except Exception as e:
        print("❌ 재생 실패:", e)
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False


# ==================================================
# ▶ active 회차 대기
# ==================================================
def wait_active_episode(driver):
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a.episode-item.episode-item-active")
        )
    )
    print("✅ active 회차 확인")

# ==================================================
# ▶ 1 회부터 시작
# ==================================================

def click_first_episode(driver):
    episodes = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a.episode-item")
        )
    )

    first_ep = episodes[-1]   # 🔥 항상 1회
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", first_ep
    )
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", first_ep)
    print("✅ 1회부터 시작")

# ==================================================
# ▶ 다음 회차 (정방향)
# ==================================================
def click_next_episode(driver):
    try:
        next_ep = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(@class,'episode-item-active')]/preceding-sibling::a[1]"
            ))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", next_ep
        )
        time.sleep(0.5)

        driver.execute_script("arguments[0].click();", next_ep)
        print("➡️ 다음 회차 이동")
        return True

    except:
        print("🏁 다음 회차 없음 (마지막 회차)")
        return False


# ==================================================
# ▶ 메인
# ==================================================
if __name__ == "__main__":
    url = sys.argv[1]

    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--autoplay-policy=no-user-gesture-required")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        # 1️⃣ 1회부터 시작
        click_first_episode(driver)
        time.sleep(3)

        if not play_video_and_fullscreen(driver):
            raise RuntimeError("초기 재생 실패")

        # ==================================================
        # ▶ 자동 다음 회차 루프 (안정판)
        # ==================================================
        while True:
            time.sleep(5)

            if not is_driver_alive(driver):
                print("❌ WebDriver 세션 종료 감지")
                break

            iframe = None
            for f in driver.find_elements(By.TAG_NAME, "iframe"):
                if "player" in (f.get_attribute("src") or ""):
                    iframe = f
                    break

            if not iframe:
                print("⚠️ iframe 없음, 대기")
                continue

            driver.switch_to.frame(iframe)

            ended = driver.execute_script("""
                const v = document.querySelector('video');
                return v ? v.ended : false;
            """)

            driver.switch_to.default_content()

            if ended:
                print("🏁 영상 종료")

                if not click_next_episode(driver):
                    print("✅ 모든 회차 재생 완료")
                    break

                time.sleep(4)
                play_video_and_fullscreen(driver)

    finally:
        print("🧹 드라이버 종료")
        try:
            driver.quit()
        except:
            pass
