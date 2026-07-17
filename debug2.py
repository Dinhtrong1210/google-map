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
    print('[1] Đã mở trang')
    time.sleep(8)

    driver.execute_script("window.scrollBy(0, 400);")
    time.sleep(2)

    all_buttons = driver.find_elements(By.XPATH, "//button")
    for btn in all_buttons:
        try:
            txt = (btn.text or '').strip()
            if txt and ('đánh giá' in txt.lower() or 'review' in txt.lower() or 'viết' in txt.lower()):
                if btn.is_displayed() and btn.is_enabled():
                    print(f'[2] Clicking: "{txt}"')
                    driver.execute_script("arguments[0].scrollIntoView({block:'center', behavior:'smooth'});", btn)
                    time.sleep(1)
                    ActionChains(driver).move_to_element(btn).pause(0.5).click().perform()
                    print('[3] Đã click')
                    break
        except:
            continue

    time.sleep(5)
    driver.save_screenshot('debug2_1_after_click.png')

    print('\n=== KIỂM TRA IFRAMES ===')
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    print(f'Tổng số iframes: {len(iframes)}')
    for idx, f in enumerate(iframes):
        try:
            print(f'  iframe {idx}: src={f.get_attribute("src")[:100] if f.get_attribute("src") else "N/A"} class={f.get_attribute("class")} displayed={f.is_displayed()}')
        except:
            pass

    print('\n=== KIỂM TRA SHADOW DOM ===')
    shadow_result = driver.execute_script("""
    function findAllInShadow(root, selector, results) {
        results = results || [];
        var found = root.querySelectorAll(selector);
        for (var i = 0; i < found.length; i++) results.push(found[i]);
        var all = root.querySelectorAll('*');
        for (var j = 0; j < all.length; j++) {
            if (all[j].shadowRoot) {
                findAllInShadow(all[j].shadowRoot, selector, results);
            }
        }
        return results;
    }
    var results = [];
    // Tìm sao trong shadow DOM
    var starResults = findAllInShadow(document, '[aria-label*="sao"], [aria-label*="star"], [class*="s2xyy"], [class*="lv4IMd"]');
    for (var k = 0; k < starResults.length; k++) {
        var el = starResults[k];
        results.push({
            tag: el.tagName,
            class: el.className,
            aria: el.getAttribute('aria-label'),
            displayed: el.offsetParent !== null,
            w: el.offsetWidth,
            h: el.offsetHeight
        });
    }
    // Tìm textarea trong shadow DOM
    var textResults = findAllInShadow(document, 'textarea, [contenteditable="true"], [role="textbox"]');
    for (var m = 0; m < textResults.length; m++) {
        var tel = textResults[m];
        results.push({
            tag: tel.tagName,
            class: tel.className,
            aria: tel.getAttribute('aria-label'),
            placeholder: tel.getAttribute('placeholder'),
            type: 'textarea',
            displayed: tel.offsetParent !== null
        });
    }
    // Tìm dialog trong shadow DOM
    var dialogResults = findAllInShadow(document, '[role="dialog"]');
    for (var n = 0; n < dialogResults.length; n++) {
        var dlg = dialogResults[n];
        results.push({
            tag: dlg.tagName,
            class: dlg.className,
            aria: dlg.getAttribute('aria-label'),
            text: (dlg.textContent || '').substring(0, 200),
            type: 'dialog',
            displayed: dlg.offsetParent !== null
        });
    }
    return results;
    """)
    print(f'Tổng elements tìm thấy trong shadow DOM: {len(shadow_result)}')
    for idx, item in enumerate(shadow_result):
        print(f'  [{idx}] {json.dumps(item, ensure_ascii=False)}')

    print('\n=== KIỂM TRA TỪNG IFRAME ===')
    for idx, iframe in enumerate(iframes):
        try:
            driver.switch_to.frame(iframe)
            print(f'\n--- iframe {idx} ---')
            iframe_stars = driver.execute_script("""
            var results = [];
            var els = document.querySelectorAll('[aria-label*="sao"], [aria-label*="star"], [class*="s2xyy"], [class*="lv4IMd"], textarea');
            for (var i = 0; i < els.length; i++) {
                results.push({
                    tag: els[i].tagName,
                    class: els[i].className,
                    aria: els[i].getAttribute('aria-label'),
                    placeholder: els[i].getAttribute('placeholder'),
                    w: els[i].offsetWidth,
                    h: els[i].offsetHeight
                });
            }
            return results;
            """)
            if iframe_stars:
                print(f'  Tìm thấy {len(iframe_stars)} elements:')
                for item in iframe_stars:
                    print(f'    {json.dumps(item, ensure_ascii=False)}')
            else:
                print(f'  Không tìm thấy star/textarea')
            driver.switch_to.default_content()
        except Exception as e:
            print(f'  Lỗi iframe {idx}: {e}')
            driver.switch_to.default_content()

    print('\n=== XONG DEBUG 2 ===')

finally:
    time.sleep(3)
    driver.quit()
