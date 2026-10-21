import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# 从环境变量读取多行 URL 列表
RAW_URLS = os.environ.get("STREAMLIT_APP_URLS", "")
STREAMLIT_URLS = [
    line.strip()
    for line in RAW_URLS.splitlines()
    if line.strip() and not line.strip().startswith("#")
]

if not STREAMLIT_URLS:
    print("❌ 未读取到任何 Streamlit 地址，请检查 Secret STREAMLIT_APP_URLS")
    sys.exit(1)

def wake_one(url: str, service: Service) -> bool:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # === 伪装成真实用户的浏览器 ===
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=service, options=options)
    
    # 隐藏 webdriver 属性，防止被 Streamlit 识别为机器人
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })

    try:
        print(f"\n===== 开始处理: {url} =====")
        driver.get(url)
        print("已打开页面")

        wait = WebDriverWait(driver, 15)
        button_xpath = "//button[contains(text(),'Yes, get this app back up')]"

        try:
            button = wait.until(EC.element_to_be_clickable((By.XPATH, button_xpath)))
            print("检测到唤醒按钮，正在尝试点击...")
            
            # 使用 JavaScript 点击，更强力，能突破某些遮罩层
            driver.execute_script("arguments[0].click();", button)
            print("已发送点击指令，等待应用启动...")

            # 给 60 秒的极限启动时间
            time.sleep(60) 
            
            # 检查是否还在唤醒页面
            try:
                driver.find_element(By.XPATH, button_xpath)
                print("❌ 唤醒失败：页面仍在显示唤醒按钮")
                return False
            except:
                print("✅ 唤醒成功：页面已跳转，应用应正在启动或已启动")
                return True

        except TimeoutException:
            print("✅ 未检测到唤醒按钮，应用当前处于清醒状态")
            return True

    except Exception as e:
        print(f"❌ 处理出错: {e}")
        return False
    finally:
        driver.quit()

def main():
    print(f"共读取到 {len(STREAMLIT_URLS)} 个 Streamlit 地址")
    service = Service(ChromeDriverManager().install())
    failed = []

    for url in STREAMLIT_URLS:
        ok = wake_one(url, service)
        if not ok:
            failed.append(url)

    print("\n===== 汇总 =====")
    print(f"总数: {len(STREAMLIT_URLS)}")
    print(f"成功: {len(STREAMLIT_URLS) - len(failed)}")
    print(f"失败: {len(failed)}")

    if failed:
        print("\n失败地址:")
        for url in failed:
            print(f"- {url}")
        sys.exit(1)

    print("全部地址处理完成 ✅")

if __name__ == "__main__":
    main()
