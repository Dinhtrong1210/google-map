from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')
options.add_argument('--user-data-dir=C:/Users/TRONG/AppData/Local/Google/Chrome/User Data')
options.add_argument('--profile-directory=Default')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    url = 'https://www.google.com/maps/place/Ng%C3%A2n+H%C3%A0ng+N%C3%B4ng+Nghi%E1%BB%87p+V%C3%A0+Ph%C3%A1t+Tri%E1%BB%83n+N%C3%B4ng+Th%C3%B4n+Vi%E1%BB%87t+Nam/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139c7f0faea33f9:0x3e21bbd84998fef4!8m2!3d18.5380314!4d105.5879837!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F1hdzmfmw5?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D'

    driver.get(url)
    print('[1] Da mo trang')
    time.sleep(10)

    # Scroll like bot
    for i in range(5):
        driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
        time.sleep(1.5)

    print('\n=== TAT CA BUTTONS VISIBLE ===')
    all_buttons = driver.find_elements(By.XPATH, "//button")
    for idx, btn in enumerate(all_buttons):
        try:
            if btn.is_displayed():
                txt = (btn.text or '').strip()
                aria = btn.get_attribute('aria-label') or ''
                data = btn.get_attribute('data-value') or ''
                jsaction = (btn.get_attribute('jsaction') or '')[:80]
                if txt or aria or data:
                    print(f'  [{idx}] text="{txt}" aria="{aria}" data="{data}" jsaction="{jsaction}"')
        except:
            pass

    # Also check links / divs with role=button
    print('\n=== LINKS / DIVS voi role=button ===')
    role_btns = driver.find_elements(By.XPATH, "//*[contains(@role, 'button')]")
    for idx, el in enumerate(role_btns):
        try:
            if el.is_displayed():
                txt = (el.text or '').strip()
                aria = el.get_attribute('aria-label') or ''
                tag = el.tag_name
                if txt or aria:
                    print(f'  [{idx}] tag={tag} text="{txt}" aria="{aria}"')
        except:
            pass

    driver.save_screenshot('debug8_buttons.png')
    print('\n[2] Chup anh debug8_buttons.png')
    print('\n=== XONG ===')

finally:
    time.sleep(3)
    driver.quit()
