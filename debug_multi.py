from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os

options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')
options.add_argument('--disable-popup-blocking')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
options.add_argument('--user-data-dir=C:/Users/TRONG/AppData/Local/Temp/chrome_profile_test')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 30)

try:
    # LOGIN
    driver.get("https://accounts.google.com")
    time.sleep(5)
    email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
    email_input.send_keys("ngotuanpro88@gmail.com")
    time.sleep(1)
    driver.find_element(By.ID, "identifierNext").click()
    time.sleep(3)
    pass_input = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
    pass_input.send_keys("Dungmedia24@")
    time.sleep(1)
    driver.find_element(By.ID, "passwordNext").click()
    time.sleep(8)
    print(f'[LOGIN] URL: {driver.current_url[:100]}')

    # NAVIGATE
    url = 'https://www.google.com/maps/place/Ng%C3%A2n+H%C3%A0ng+N%C3%B4ng+Nghi%E1%BB%87p+V%C3%A0+Ph%C3%A1t+Tri%E1%BB%83n+N%C3%B4ng+Th%C3%B4n+Vi%E1%BB%87t+Nam+@+Chi+Nh%C3%A1nh+H%C3%A0+T%C4%A9nh/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139b4caf4daf5ad:0x376339de9864bb0a!8m2!3d18.451453!4d105.7777702!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F1hf68qftt?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D'
    driver.get(url)
    time.sleep(12)

    # Scroll
    for i in range(5):
        driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
        time.sleep(1.5)

    # Check all buttons
    print('\n=== BUTTONS with write/review ===')
    all_buttons = driver.find_elements(By.XPATH, "//button")
    for btn in all_buttons:
        try:
            if btn.is_displayed():
                txt = (btn.text or '').strip()
                aria = btn.get_attribute('aria-label') or ''
                data = btn.get_attribute('data-value') or ''
                if txt or aria or data:
                    combined = (txt + aria + data).lower()
                    if any(w in combined for w in ['review', 'danh gia', 'danh gia', 'vit', 'write', 'post']):
                        print(f'  text="{txt}" aria="{aria}" data="{data}"')
        except:
            pass

    # Check page title and URL
    print(f'\nTitle: {driver.title}')
    print(f'URL: {driver.current_url[:200]}')

    # Check if already reviewed
    body = driver.execute_script("return document.body.innerText.substring(0, 2000);")
    if 'da danh gia' in body.lower() or 'you reviewed' in body.lower() or 'sua danh gia' in body.lower() or 'edit review' in body.lower():
        print('\n>>> TAI KHOAN DA REVIEW DIA DIEM NAY ROI!')
    if 'vie bai danh gia' in body.lower() or 'write a review' in body.lower():
        print('\n>>> CO NUT WRITE A REVIEW!')

    # Print first 500 chars of body
    print(f'\nBody preview:\n{body[:500]}')

    driver.save_screenshot('debug_multi.png')

finally:
    time.sleep(3)
    driver.quit()
