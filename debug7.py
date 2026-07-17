from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time, json

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
    time.sleep(8)

    # Scroll EXACTLY like the bot does
    for i in range(5):
        driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
        time.sleep(1.5)

    # Click Write a review
    btn = driver.find_element(By.XPATH, "//button[@data-value='Write a review']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", btn)
    time.sleep(1)
    ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
    print('[2] Da click "Write a review"')
    time.sleep(5)

    # Switch to iframe
    print('\n=== SWITCH IFRAME ===')
    try:
        iframe = driver.find_element(By.NAME, "goog-reviews-write-widget")
        print(f'  Found iframe: src={iframe.get_attribute("src")[:100]}')
        driver.switch_to.frame(iframe)
        print('  Switched OK!')
        time.sleep(3)

        # Check what we see
        print('\n=== SAU KHI SWITCH - KIEM TRA TOAN BO ===')
        all_els = driver.find_elements(By.XPATH, "//*")
        print(f'Total elements: {len(all_els)}')

        # Check current URL
        print(f'Current URL: {driver.current_url[:100]}')

        # Find stars
        stars = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'star') or contains(@aria-label, 'sao') or contains(@aria-label, 'Star') or contains(@aria-label, 'Five') or contains(@aria-label, 'Four') or contains(@aria-label, 'Three') or contains(@aria-label, 'Two') or contains(@aria-label, 'One')]")
        print(f'\nStars with aria: {len(stars)}')
        for s in stars:
            print(f'  tag={s.tag_name} aria="{s.get_attribute("aria-label")}" class="{(s.get_attribute("class") or "")[:60]}" displayed={s.is_displayed()}')

        # Find ALL visible elements with text
        all_visible = driver.find_elements(By.XPATH, "//*")
        print(f'\nAll visible elements: {len(all_visible)}')
        for el in all_visible[:30]:
            try:
                if el.is_displayed() and el.tag_name in ['BUTTON', 'TEXTAREA', 'INPUT', 'DIV', 'SPAN']:
                    txt = (el.text or '')[:50].strip()
                    aria = el.get_attribute('aria-label') or ''
                    cls = (el.get_attribute('class') or '')[:40]
                    if txt or aria:
                        print(f'  tag={el.tag_name} text="{txt}" aria="{aria}" cls="{cls}"')
            except:
                pass

        # Try CSS selectors
        print('\n=== CSS SELECTORS ===')
        try:
            s2xyy = driver.find_elements(By.CSS_SELECTOR, '.s2xyy')
            print(f'.s2xyy: {len(s2xyy)}')
            for s in s2xyy:
                print(f'  aria="{s.get_attribute("aria-label")}" displayed={s.is_displayed()} size={s.size}')
        except Exception as e:
            print(f'  CSS error: {e}')

        try:
            lv4IMd = driver.find_elements(By.CSS_SELECTOR, '.lv4IMd')
            print(f'.lv4IMd: {len(lv4IMd)}')
            for s in lv4IMd:
                print(f'  aria="{s.get_attribute("aria-label")}" displayed={s.is_displayed()} size={s.size}')
        except Exception as e:
            print(f'  CSS error: {e}')

        # Check HTML of body
        html = driver.execute_script("return document.body ? document.body.innerHTML.substring(0, 2000) : 'NO BODY';")
        print(f'\nBody HTML (2000 chars):\n{html}')

    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    print('\n=== XONG DEBUG 7 ===')

finally:
    time.sleep(5)
    driver.quit()
