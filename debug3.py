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

    # Cuon xuong de tim nut
    for i in range(5):
        driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
        time.sleep(1.5)

    print('\n=== TAT CA BUTTONS VISIBLE ===')
    all_buttons = driver.find_elements(By.XPATH, "//button")
    review_candidates = []
    for idx, btn in enumerate(all_buttons):
        try:
            if btn.is_displayed():
                txt = (btn.text or '').strip()
                aria = btn.get_attribute('aria-label') or ''
                jsaction = btn.get_attribute('jsaction') or ''
                data_val = btn.get_attribute('data-value') or ''
                if txt or aria:
                    print(f'  [{idx}] text="{txt}" aria="{aria}" jsaction="{jsaction[:80]}" data-val="{data_val}"')
                    txt_lower = txt.lower()
                    aria_lower = aria.lower()
                    if ('review' in txt_lower or 'danh gia' in txt_lower or 'viết' in txt_lower
                        or 'write' in txt_lower or 'post' in txt_lower
                        or 'review' in aria_lower or 'danh gia' in aria_lower):
                        review_candidates.append((idx, btn, txt, aria))
        except:
            pass

    print(f'\n=== {len(review_candidates)} REVIEW CANDIDATES ===')
    for idx, btn, txt, aria in review_candidates:
        print(f'  [{idx}] text="{txt}" aria="{aria}"')

    # Thu click tung candidate
    clicked = False
    for idx, btn, txt, aria in review_candidates:
        try:
            print(f'\n--- Thu click: text="{txt}" aria="{aria}" ---')
            driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", btn)
            time.sleep(1)
            ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
            time.sleep(5)
            driver.save_screenshot(f'debug3_after_click_{idx}.png')
            print(f'  Da chup debug3_after_click_{idx}.png')

            # Kiem tra dialog moi
            dialogs = driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog')]")
            visible_dialogs = [d for d in dialogs if d.is_displayed()]
            print(f'  Visible dialogs: {len(visible_dialogs)}')
            for d in visible_dialogs:
                txt_preview = (d.text or '')[:300]
                print(f'    Dialog: aria="{d.get_attribute("aria-label")}" text={txt_preview}')

            # Kiem tra star
            stars = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'sao') or contains(@aria-label, 'star') or contains(@aria-label, 'Star')]")
            visible_stars = [s for s in stars if s.is_displayed()]
            print(f'  Visible star elements: {len(visible_stars)}')
            for s in visible_stars[:10]:
                print(f'    tag={s.tag_name} aria="{s.get_attribute("aria-label")}" class="{s.get_attribute("class")[:50]}"')

            # Kiem tra textarea
            textareas = driver.find_elements(By.XPATH, "//textarea | //*[@contenteditable='true'] | //*[@role='textbox']")
            visible_ta = [t for t in textareas if t.is_displayed()]
            print(f'  Visible textarea/textbox: {len(visible_ta)}')
            for t in visible_ta:
                print(f'    tag={t.tag_name} aria="{t.get_attribute("aria-label")}" placeholder="{t.get_attribute("placeholder")}"')

            if visible_stars and any(s.get_attribute('aria-label') and ('sao' in (s.get_attribute('aria-label') or '').lower() or 'star' in (s.get_attribute('aria-label') or '').lower()) for s in visible_stars):
                # Co the dang o popup review dung
                # Kiem tra co phai star input khong (khong phai display stars)
                for s in visible_stars:
                    cls = s.get_attribute('class') or ''
                    aria = s.get_attribute('aria-label') or ''
                    if 'kvMYJc' not in cls and 'ZkP5Je' not in cls and 'BHOKXe' not in cls:
                        print(f'  >>> DAY CO THE LA STAR INPUT: aria="{aria}" class="{cls[:60]}"')
                        clicked = True
                        break

            if clicked:
                break

            # Quay lai de test candidate tiep theo
            print('  Quay lai trang...')
            driver.get(url)
            time.sleep(6)
            for i in range(5):
                driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
                time.sleep(1)

        except Exception as e:
            print(f'  Loi: {e}')
            driver.get(url)
            time.sleep(6)
            for i in range(5):
                driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
                time.sleep(1)

    if not clicked:
        print('\n=== CHUA TIM THAY - THU CLICK TRUC TIEP "WRITE A REVIEW" ===')
        # Thu JavaScript click
        result = driver.execute_script("""
        var btns = document.querySelectorAll('button');
        var found = [];
        for (var i = 0; i < btns.length; i++) {
            var t = (btns[i].textContent || '').trim();
            var a = btns[i].getAttribute('aria-label') || '';
            var j = btns[i].getAttribute('jsaction') || '';
            if (t) found.push({text: t, aria: a, jsaction: j.substring(0,100), displayed: btns[i].offsetParent !== null});
        }
        return found;
        """)
        print(f'Tong {len(result)} buttons:')
        for r in result:
            if r.get('displayed'):
                print(f'  text="{r["text"]}" aria="{r["aria"]}" jsaction="{r["jsaction"]}"')

    print('\n=== XONG DEBUG 3 ===')

finally:
    time.sleep(5)
    driver.quit()
