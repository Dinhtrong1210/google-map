from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time, os, json, random

options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-infobars')
options.add_argument('--disable-notifications')
options.add_argument('--disable-popup-blocking')
options.add_argument('--user-data-dir=C:/Users/TRONG/AppData/Local/Google/Chrome/User Data')
options.add_argument('--profile-directory=Default')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 30)

a = 'https://www.google.com/maps/place/Ng%C3%A2n+H%C3%A0ng+N%C3%B4ng+Nghi%E1%BB%87p+V%C3%A0+Ph%C3%A1t+Tri%E1%BB%83n+N%C3%B4ng+Th%C3%B4n+Vi%E1%BB%87t+Nam/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139c7f0faea33f9:0x3e21bbd84998fef4!8m2!3d18.5380314!4d105.5879837!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F1hdzmfmw5?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D'
driver.get(a)

for i in range(10):
    time.sleep(2)
    print('loop', i, driver.current_url)
    # try click review button by text if visible
    buttons = driver.find_elements(By.XPATH, '//button')
    found = []
    for b in buttons:
        try:
            if b.is_displayed():
                t=(b.text or '').strip()
                if 'đánh giá' in t.lower() or 'review' in t.lower() or 'viết bài' in t.lower():
                    found.append((t,b.get_attribute('aria-label') or '',b.get_attribute('jsaction') or ''))
        except Exception:
            pass
    print('buttons found', found[:20])
    if found:
        for t, aria, js in found[:5]:
            print('CLICKING', t, aria, js)
            try:
                b = None
                for bb in buttons:
                    try:
                        if bb.is_displayed() and (bb.text or '').strip() == t:
                            b=bb
                            break
                    except Exception:
                        pass
                if b:
                    driver.execute_script('arguments[0].scrollIntoView({block:"center"}); arguments[0].click();', b)
                    time.sleep(4)
                    print('clicked button')
                    break
            except Exception as e:
                print('click err', e)
        break

# dump popup candidates
candidates = driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog') or contains(@aria-label, 'review') or contains(@aria-label, 'đánh giá') or contains(@aria-label, 'rating') or contains(@aria-label, 'write')]")
print('candidate count', len(candidates))
for idx, c in enumerate(candidates[:15]):
    try:
        if c.is_displayed():
            print('candidate', idx, 'tag', c.tag_name, 'role', c.get_attribute('role'), 'aria', c.get_attribute('aria-label'), 'text', (c.text or '')[:400])
    except Exception as e:
        print('cand err', e)

# Print all elements with aria-label or title matching star/rating
for sel in [
    "//*[contains(@aria-label, 'star') or contains(@aria-label, 'sao') or contains(@aria-label, 'rating') or contains(@aria-label, 'review') or contains(@aria-label, 'đánh')]",
    "//*[@role='button' or @role='radio' or @role='img']"
]:
    els = driver.find_elements(By.XPATH, sel)
    print('selector', sel, 'count', len(els))
    for i, el in enumerate(els[:40]):
        try:
            if el.is_displayed():
                print(i, 'tag', el.tag_name, 'role', el.get_attribute('role'), 'aria', el.get_attribute('aria-label'), 'title', el.get_attribute('title'), 'data', el.get_attribute('data-value'), el.get_attribute('aria-valuenow'))
        except Exception as e:
            pass

# save screenshot
try:
    driver.save_screenshot('debug_page.png')
    print('saved debug_page.png')
except Exception as e:
    print('screenshot err', e)

time.sleep(10)
driver.quit()
