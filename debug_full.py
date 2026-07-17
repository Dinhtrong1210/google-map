from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
wait = WebDriverWait(driver, 30)

try:
    url = 'https://www.google.com/maps/place/Ng%C3%A2n+H%C3%A0ng+N%C3%B4ng+Nghi%E1%BB%87p+V%C3%A0+Ph%C3%A1t+Tri%E1%BB%83n+N%C3%B4ng+Th%C3%B4n+Vi%E1%BB%87t+Nam/@18.5380314,105.2831131,11z/data=!4m10!1m2!2m1!1zTmfDom4gaMOgbmcgTsO0bmcgbmdoaeG7h3AgdsOgIFBow6F0IHRyaeG7g24gTsO0bmcgdGjDtG4gVmnhu4d0IE5hbQ!3m6!1s0x3139c7f0faea33f9:0x3e21bbd84998fef4!8m2!3d18.5380314!4d105.5879837!15sCkNOZ8OibiBow6BuZyBOw7RuZyBuZ2hp4buHcCB2w6AgUGjDoXQgdHJp4buDbiBOw7RuZyB0aMO0biBWaeG7h3QgTmFtIgOIAQGSAQRiYW5r4AEA!16s%2Fg%2F1hdzmfmw5?entry=ttu&g_ep=EgoyMDI2MDcxNC4wIKXMDSoASAFQAw%3D%3D'
    driver.get(url)
    print('[1] Đã mở trang Google Maps')
    time.sleep(8)

    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(2)

    found_btn = False
    all_buttons = driver.find_elements(By.XPATH, "//button")
    for btn in all_buttons:
        try:
            txt = (btn.text or '').strip()
            if txt and ('đánh giá' in txt.lower() or 'review' in txt.lower() or 'viết' in txt.lower()):
                if btn.is_displayed() and btn.is_enabled():
                    print(f'[2] Tìm thấy button: "{txt}" aria="{btn.get_attribute("aria-label")}" jsaction="{btn.get_attribute("jsaction")}"')
                    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", btn)
                    time.sleep(1)
                    ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
                    print('[3] Đã click button review')
                    found_btn = True
                    time.sleep(5)
                    break
        except:
            continue

    if not found_btn:
        print('[2] KHÔNG TÌM THẤY button review!')
        print('All visible buttons:')
        for btn in all_buttons:
            try:
                if btn.is_displayed():
                    t = (btn.text or '').strip()
                    if t:
                        print(f'  - "{t}" aria="{btn.get_attribute("aria-label")}"')
            except:
                pass
        driver.save_screenshot('debug_no_review_button.png')
        print('[!] Lưu debug_no_review_button.png')

    driver.save_screenshot('debug_full_1_after_click.png')
    print('[4] Đã chụp ảnh debug_full_1_after_click.png')

    print('\n=== KIỂM TRA DIALOG ===')
    dialogs = driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog')]")
    print(f'Tìm thấy {len(dialogs)} dialog')
    for idx, d in enumerate(dialogs):
        try:
            if d.is_displayed():
                txt = (d.text or '')[:500]
                print(f'  Dialog {idx}: tag={d.tag_name} aria="{d.get_attribute("aria-label")}" text_preview={txt[:200]}')
        except:
            pass

    print('\n=== TẤT CẢ ELEMENTS VỚI STAR/RATING ===')
    star_els = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'star') or contains(@aria-label, 'sao') or contains(@aria-label, 'rating') or contains(@aria-label, 'Star') or contains(@aria-label, 'Stars')]")
    print(f'Tìm thấy {len(star_els)} elements star/rating')
    for idx, el in enumerate(star_els[:30]):
        try:
            if el.is_displayed():
                print(f'  [{idx}] tag={el.tag_name} role={el.get_attribute("role")} aria="{el.get_attribute("aria-label")}" title="{el.get_attribute("title")}" data-value="{el.get_attribute("data-value")}" class="{el.get_attribute("class")}" size={el.size}')
        except:
            pass

    print('\n=== TẤT CẢ ELEMENTS VỚI data-value ===')
    dv_els = driver.find_elements(By.XPATH, "//*[@data-value]")
    print(f'Tìm thấy {len(dv_els)} elements data-value')
    for idx, el in enumerate(dv_els[:20]):
        try:
            if el.is_displayed():
                print(f'  [{idx}] tag={el.tag_name} role={el.get_attribute("role")} aria="{el.get_attribute("aria-label")}" data-value="{el.get_attribute("data-value")}" class="{el.get_attribute("class")}"')
        except:
            pass

    print('\n=== TẤT CẢ TEXTAREA / CONTENTEDITABLE ===')
    text_els = driver.find_elements(By.XPATH, "//textarea | //*[@contenteditable='true'] | //*[@role='textbox']")
    print(f'Tìm thấy {len(text_els)} textarea/contenteditable')
    for idx, el in enumerate(text_els[:15]):
        try:
            if el.is_displayed():
                print(f'  [{idx}] tag={el.tag_name} role={el.get_attribute("role")} aria="{el.get_attribute("aria-label")}" placeholder="{el.get_attribute("placeholder")}" contenteditable="{el.get_attribute("contenteditable")}" class="{el.get_attribute("class")}" size={el.size}')
        except:
            pass

    print('\n=== HTML CỦA DIALOG (nếu có) ===')
    for d in dialogs:
        try:
            if d.is_displayed():
                html = driver.execute_script("return arguments[0].innerHTML.substring(0, 3000);", d)
                print(f'Dialog HTML (3000 chars):\n{html}')
                break
        except:
            pass

    print('\n=== XONG DEBUG ===')

finally:
    time.sleep(3)
    driver.quit()
