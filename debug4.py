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

    for i in range(5):
        driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
        time.sleep(1.5)

    # ===== CLICK NUT "Write a review" DUNG =====
    print('\n=== CLICK NUT "Write a review" ===')
    btn = None

    # Uu tien 1: data-value
    try:
        btn = driver.find_element(By.XPATH, "//button[@data-value='Write a review']")
        print(f'[2] Tim thay theo data-value: text="{btn.text}" aria="{btn.get_attribute("aria-label")}"')
    except:
        pass

    # Uu tien 2: aria-label
    if not btn or not btn.is_displayed():
        try:
            btn = driver.find_element(By.XPATH, "//button[@aria-label='Write a review']")
            print(f'[2] Tim thay theo aria-label: text="{btn.text}"')
        except:
            pass

    # Uu tien 3: text chinh xac
    if not btn or not btn.is_displayed():
        all_buttons = driver.find_elements(By.XPATH, "//button")
        for b in all_buttons:
            txt = (b.text or '').strip()
            if txt == "Write a review" and b.is_displayed():
                btn = b
                print(f'[2] Tim thay theo text: "{txt}"')
                break

    if btn and btn.is_displayed():
        driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", btn)
        time.sleep(1)
        ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
        print('[3] DA CLICK NUT "Write a review"!')
        time.sleep(5)
    else:
        print('[2] KHONG TIM THAY NUT "Write a review"!')

    driver.save_screenshot('debug4_after_write_review.png')
    print('[4] Chup anh debug4_after_write_review.png')

    # ===== KIEM TRA POPUP =====
    print('\n=== KIEM TRA POPUP REVIEW ===')
    dialogs = driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog')]")
    visible_dialogs = [d for d in dialogs if d.is_displayed()]
    print(f'Visible dialogs: {len(visible_dialogs)}')
    for idx, d in enumerate(visible_dialogs):
        aria = d.get_attribute('aria-label') or ''
        text_preview = (d.text or '')[:300]
        print(f'  Dialog {idx}: aria="{aria}"')
        print(f'    Text: {text_preview}')

    # Kiem tra star INPUT (khong phai display stars)
    print('\n=== KIEM TRA STAR INPUTS ===')
    star_els = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'star') or contains(@aria-label, 'sao') or contains(@aria-label, 'Star') or contains(@aria-label, 'Stars')]")
    visible_stars = [s for s in star_els if s.is_displayed()]
    print(f'Visible star elements: {len(visible_stars)}')
    for idx, s in enumerate(visible_stars[:20]):
        cls = s.get_attribute('class') or ''
        aria = s.get_attribute('aria-label') or ''
        tag = s.tag_name
        is_input = 'kvMYJc' in cls or 's2xyy' in cls or 'lv4IMd' in cls
        print(f'  [{idx}] tag={tag} aria="{aria}" class="{cls[:60]}" INPUT={is_input}')

    # Kiem tra textarea
    print('\n=== KIEM TRA TEXTAREA ===')
    textareas = driver.find_elements(By.XPATH, "//textarea | //*[@contenteditable='true'] | //*[@role='textbox']")
    visible_ta = [t for t in textareas if t.is_displayed()]
    print(f'Visible textarea/textbox: {len(visible_ta)}')
    for t in visible_ta:
        print(f'  tag={t.tag_name} aria="{t.get_attribute("aria-label")}" placeholder="{t.get_attribute("placeholder")}" class="{(t.get_attribute("class") or "")[:60]}"')

    print('\n=== XONG DEBUG 4 ===')

finally:
    time.sleep(5)
    driver.quit()
