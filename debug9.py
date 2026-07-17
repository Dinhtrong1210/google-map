from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, json

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
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 2,
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
})

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
    url = 'https://www.google.com/maps/place/Ng%C3%A2n+H%C3%A0ng+N%C3%B4ng+Nghi%E1%BB%87p+V%C3%A0+Ph%C3%A1t+Tri%E1%BB%83n+N%C3%B4ng+Th%C3%B4n+Vi%E1%BB%87t+Nam/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139c7f0faea33f9:0x3e21bbd84998fef4!8m2!3d18.5380314!4d105.5879837!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F1hdzmfmw5?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D'
    driver.get(url)
    print(f'[NAV] Navigating...')
    time.sleep(10)
    print(f'[NAV] URL: {driver.current_url[:100]}')

    # Scroll
    for i in range(5):
        driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
        time.sleep(1.5)

    # List ALL buttons
    print('\n=== TAT CA BUTTONS ===')
    all_buttons = driver.find_elements(By.XPATH, "//button")
    found_write = False
    for idx, btn in enumerate(all_buttons):
        try:
            if btn.is_displayed():
                txt = (btn.text or '').strip()
                aria = btn.get_attribute('aria-label') or ''
                data = btn.get_attribute('data-value') or ''
                if txt or aria or data:
                    print(f'  [{idx}] text="{txt}" aria="{aria}" data="{data}"')
                    if 'write' in txt.lower() or 'review' in txt.lower() or 'danh gia' in txt.lower():
                        found_write = True
        except:
            pass

    if not found_write:
        print('\n!!! KHONG CO BUTTON WRITE A REVIEW !!!')
        print('\nPage title:', driver.title)
        print('Page URL:', driver.current_url[:200])

        # Check for consent dialog
        print('\n=== CONSENT / POPUP CHECK ===')
        dialogs = driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog') or contains(@class, 'consent') or contains(@class, 'modal')]")
        for d in dialogs:
            if d.is_displayed():
                print(f'  Dialog: text="{(d.text or "")[:200]}"')

        # Check body text
        body_text = driver.execute_script("return (document.body.innerText || '').substring(0, 1000);")
        print(f'\nBody text (1000 chars):\n{body_text}')

    driver.save_screenshot('debug9_after_login.png')
    print('\n[END] Chup anh debug9_after_login.png')

finally:
    time.sleep(3)
    driver.quit()
