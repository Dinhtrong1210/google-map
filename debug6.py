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

    # Click "Write a review"
    btn = driver.find_element(By.XPATH, "//button[@data-value='Write a review']")
    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", btn)
    time.sleep(1)
    ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
    print('[2] Da click "Write a review"')
    time.sleep(5)

    # Switch vao iframe
    print('\n=== SWITCH VAO IFRAME ===')
    iframe = driver.find_element(By.NAME, "goog-reviews-write-widget")
    driver.switch_to.frame(iframe)
    print('[3] Da switch vao iframe')
    time.sleep(3)

    # Kiem tra element trong iframe
    print('\n=== ELEMENTS TRONG IFRAME ===')
    all_els = driver.find_elements(By.XPATH, "//*")
    print(f'Tong elements: {len(all_els)}')

    # Tim star
    stars = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'star') or contains(@aria-label, 'sao') or contains(@aria-label, 'Star')]")
    visible_stars = [s for s in stars if s.is_displayed()]
    print(f'Star elements: {len(visible_stars)}')
    for idx, s in enumerate(visible_stars[:15]):
        cls = (s.get_attribute('class') or '')[:60]
        aria = s.get_attribute('aria-label') or ''
        tag = s.tag_name
        print(f'  [{idx}] tag={tag} aria="{aria}" class="{cls}"')

    # Tim textarea
    textareas = driver.find_elements(By.XPATH, "//textarea | //*[@contenteditable='true'] | //*[@role='textbox']")
    visible_ta = [t for t in textareas if t.is_displayed()]
    print(f'Textarea/textbox: {len(visible_ta)}')
    for t in visible_ta:
        print(f'  tag={t.tag_name} aria="{t.get_attribute("aria-label")}" placeholder="{t.get_attribute("placeholder")}" class="{(t.get_attribute("class") or "")[:60]}"')

    # Tim button trong iframe
    buttons = driver.find_elements(By.XPATH, "//button")
    visible_btns = [b for b in buttons if b.is_displayed()]
    print(f'Buttons: {len(visible_btns)}')
    for b in visible_btns[:10]:
        txt = (b.text or '').strip()
        aria = b.get_attribute('aria-label') or ''
        print(f'  text="{txt}" aria="{aria}"')

    # Chup anh
    driver.save_screenshot('debug6_in_iframe.png')
    print('\n[4] Chup anh debug6_in_iframe.png')

    # Thu click 5 sao
    print('\n=== THU CHON 5 SAO ===')
    target = None
    for s in visible_stars:
        aria = (s.get_attribute('aria-label') or '').lower()
        if '5 star' in aria or '5 sao' in aria or aria == '5 stars':
            target = s
            print(f'  Tim thay 5 sao: aria="{s.get_attribute("aria-label")}" class="{s.get_attribute("class")}"')
            break

    if target:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
        time.sleep(0.5)
        target.click()
        print('[5] DA CLICK 5 SAO!')
        time.sleep(2)
        driver.save_screenshot('debug6_after_star.png')
    else:
        print('[5] KHONG TIM THAY 5 SAO!')
        # Thu tat ca star elements
        print('  Tat ca star visible:')
        for s in visible_stars:
            print(f'    aria="{s.get_attribute("aria-label")}" class="{s.get_attribute("class")}"')

    # Quay lai main
    driver.switch_to.default_content()
    print('\n[6] Quay lai main page')

    print('\n=== XONG DEBUG 6 ===')

finally:
    time.sleep(5)
    driver.quit()
