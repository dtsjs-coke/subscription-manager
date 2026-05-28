import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def wake_up():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = "https://subscription-manager.streamlit.app/"
    print(f"🚀 Visiting {url}...")
    
    try:
        driver.get(url)
        # 페이지가 로드될 시간을 충분히 줌 (Streamlit 초기화 대기)
        time.sleep(15)
        
        # 스크린샷 저장 (디버깅용 - Artifact로 확인 가능)
        driver.save_screenshot("streamlit_status.png")
        
        # "Yes, get this app back up!" 버튼 찾기
        # 여러가지 방식의 텍스트 매칭 시도
        wait = WebDriverWait(driver, 10)
        try:
            button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Yes, get this app back up!')]")))
            button.click()
            print("✨ Clicked the 'Wake Up' button! App is restarting.")
            time.sleep(10)
        except Exception:
            print("ℹ️ App was already awake or the button was not found.")
            
    except Exception as e:
        print(f"❌ Error during wake up process: {e}")
    finally:
        driver.quit()
        print("🏁 Done.")

if __name__ == "__main__":
    wake_up()
