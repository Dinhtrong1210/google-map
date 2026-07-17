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

    # Cho load tung buoc
    for wait_sec in [3, 5, 8, 10]:
        time.sleep(wait_sec)
        print(f'\n=== SAU {3+5+8+10 if wait_sec==10 else wait_sec}s wait ===')

        dialogs = driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog')]")
        visible_dialogs = [d for d in dialogs if d.is_displayed()]
        print(f'Visible dialogs: {len(visible_dialogs)}')

        for idx, d in enumerate(visible_dialogs):
            html_len = len(d.get_attribute('innerHTML') or '')
            text_len = len(d.text or '')
            print(f'  Dialog {idx}: html_len={html_len} text_len={text_len}')
            if html_len > 0 and html_len < 5000:
                html = d.get_attribute('innerHTML')
                print(f'  HTML preview:\n{html[:2000]}')

        # Kiem tra tat ca element moi xuat hien
        all_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'hfYJnf') or contains(@class, 'HPTfYd') or contains(@class, 'review')]")
        visible_divs = [d for d in all_divs if d.is_displayed()]
        print(f'Review-related divs: {len(visible_divs)}')
        for d in visible_divs[:5]:
            cls = (d.get_attribute('class') or '')[:80]
            text = (d.text or '')[:100]
            print(f'  class="{cls}" text="{text}"')

        # Kiem tra textarea moi
        textareas = driver.find_elements(By.XPATH, "//textarea | //*[@contenteditable='true'] | //*[@role='textbox']")
        visible_ta = [t for t in textareas if t.is_displayed()]
        print(f'Visible textarea/textbox: {len(visible_ta)}')
        for t in visible_ta:
            print(f'  tag={t.tag_name} aria="{t.get_attribute("aria-label")}" placeholder="{t.get_attribute("placeholder")}"')

        driver.save_screenshot(f'debug5_wait_{wait_sec}s.png')
        print(f'Chup anh debug5_wait_{wait_sec}s.png')

        if visible_ta:
            print('>>> TIM THAY TEXTAREA - popup da load!')
            break

    # ===== KIEM TRA TAT CA ELEMENTS SAU KHI POPUP MO =====
    print('\n=== TAT CA ELEMENTS TRONG POPUP ===')
    result = driver.execute_script("""
    function findAll(root, results, depth) {
        results = results || [];
        depth = depth || 0;
        if (depth > 10) return results;
        var children = root.children;
        for (var i = 0; i < children.length; i++) {
            var el = children[i];
            var tag = el.tagName;
            var cls = (el.className || '').toString().substring(0, 60);
            var aria = el.getAttribute('aria-label') || '';
            var role = el.getAttribute('role') || '';
            var text = (el.textContent || '').substring(0, 50);
            var w = el.offsetWidth;
            var h = el.offsetHeight;
            if (w > 0 && h > 0 && (aria || role || tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'BUTTON')) {
                results.push({
                    tag: tag,
                    cls: cls,
                    aria: aria,
                    role: role,
                    text: text.trim().substring(0, 30),
                    w: w,
                    h: h,
                    depth: depth
                });
            }
            if (el.shadowRoot) {
                findAll(el.shadowRoot, results, depth + 1);
            }
            findAll(el, results, depth + 1);
        }
        return results;
    }

    // Chi lay elements trong dialog
    var dialogs = document.querySelectorAll('[role="dialog"]');
    var allResults = [];
    for (var d = 0; d < dialogs.length; d++) {
        if (dialogs[d].offsetParent !== null) {
            findAll(dialogs[d], allResults, 0);
        }
    }
    return allResults;
    """)
    print(f'Found {len(result)} elements in visible dialog:')
    for item in result[:50]:
        print(f'  tag={item["tag"]} cls="{item["cls"]}" aria="{item["aria"]}" role="{item["role"]}" text="{item["text"]}" w={item["w"]} h={item["h"]} depth={item["depth"]}')

    print('\n=== XONG DEBUG 5 ===')

finally:
    time.sleep(5)
    driver.quit()
