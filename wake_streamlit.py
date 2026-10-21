import os
import sys
import time  # 新增：用于强制等待

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
    """访问单个 Streamlit 地址，必要时点击唤醒按钮。返回是否成功。"""
    options = Options()
    # 无头模式，静默运行，不显示浏览器界面
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"\n===== 开始处理: {url} =====")
        driver.get(url)
        print("已打开页面")

        wait = WebDriverWait(driver, 15)

        try:
            # 尝试定位“唤醒”按钮
            button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Yes, get this app back up')]")
                )
            )
            print("检测到唤醒按钮，正在点击...")
            button.click()

            try:
                # 等待按钮消失
                wait.until(
                    EC.invisibility_of_element_located(
                        (By.XPATH, "//button[contains(text(),'Yes, get this app back up')]")
                    )
                )
                print("✅ 唤醒按钮已消失，应用应正在恢复")
                
                # === 新增等待逻辑 ===
                print("等待 30 秒，确保服务器完成启动...")
                time.sleep(30) 
                # ====================
                
                return True
            except TimeoutException:
                print("❌ 按钮已点击但未消失，可能唤醒失败")
                return False

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
        # 有失败时让 GitHub Actions 标红，便于发现
        sys.exit(1)

    print("全部地址处理完成 ✅")


if __name__ == "__main__":
    main()
