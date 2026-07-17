from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time, random, os, json


class GoogleMapsReviewBot:
    def __init__(self, headless=False, user_data_dir=None, debug_port=9222):
        self.options = Options()
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('--disable-notifications')
        self.options.add_argument('--disable-popup-blocking')
        self.options.add_argument('--disable-application-cache')
        self.options.add_argument('--disable-setuid-sandbox')
        self.options.add_argument(f'--remote-debugging-port={debug_port}')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
        if user_data_dir:
            self.options.add_argument(f'--user-data-dir={user_data_dir}')
        self.options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        if headless:
            self.options.add_argument('--headless')
        self.driver = None
        self.wait = None
        self.status_callback = None

    def set_status_callback(self, callback):
        self.status_callback = callback

    def log_status(self, message, is_error=False):
        if self.status_callback:
            self.status_callback(message, is_error)
        print(message)

    def start_browser(self):
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            self.wait = WebDriverWait(self.driver, 30)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.log_status("Chrome da khoi dong thanh cong!")
            self.log_status(f"Chrome version: {self.driver.capabilities['browserVersion']}")
            return True
        except Exception as e:
            self.log_status(f"Loi khoi dong Chrome: {e}", True)
            return False

    def login_google(self, email, password):
        self.log_status(f"Dang kiem tra tai khoan: {email}")
        try:
            self.driver.get("https://myaccount.google.com")
            time.sleep(random.uniform(3, 5))
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            if "accounts.google.com" not in current_url or "signin" not in current_url:
                if email.lower() in page_source:
                    self.log_status(f"Da dang nhap tai khoan: {email} (profile cu)")
                    return True
                else:
                    self.log_status(f"Da dang nhap tai khoan khac, dang nhap lai: {email}")

            self.log_status(f"Dang dang nhap: {email}")
            self.driver.get("https://accounts.google.com")
            time.sleep(random.uniform(3, 5))
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            self._human_typing(email_input, email)
            time.sleep(random.uniform(1, 2))
            self.driver.find_element(By.ID, "identifierNext").click()
            time.sleep(random.uniform(2, 4))
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            self._human_typing(password_input, password)
            time.sleep(random.uniform(1, 2))
            self.driver.find_element(By.ID, "passwordNext").click()
            time.sleep(random.uniform(5, 8))
            current_url = self.driver.current_url

            if "challenge" in current_url or "twofactor" in current_url:
                self.log_status("Can xac minh 2FA!", True)
                return False
            if "accounts.google.com" not in current_url or "signin" not in current_url:
                self.log_status("Dang nhap thanh cong!")
                return True
            try:
                self.driver.find_element(By.XPATH, "//span[contains(text(), 'Tao tai khoan')]")
                self.log_status("Van o trang dang nhap!", True)
                return False
            except:
                pass
            self.log_status("Dang nhap thanh cong!")
            return True
        except Exception as e:
            self.log_status(f"Loi dang nhap: {e}", True)
            return False

    def navigate_to_place(self, place_url):
        self.log_status("📍 Đang mở địa điểm...")
        try:
            self.driver.get(place_url)
            time.sleep(random.uniform(5, 8))
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1, [role='heading'], .section-hero-header-title"))
                )
            except:
                pass

            search_results = self.driver.find_elements(By.CSS_SELECTOR, ".Nv2PK, .bfdHYd, [data-result-index]")
            if search_results and len(search_results) > 1:
                self.log_status(f"🔍 Phát hiện {len(search_results)} kết quả, đang chọn địa điểm đầu tiên...")
                time.sleep(random.uniform(2, 3))
                try:
                    first_result = search_results[0]
                    links = first_result.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                    if links:
                        self.driver.execute_script("arguments[0].click();", links[0])
                    else:
                        self.driver.execute_script("arguments[0].click();", first_result)
                    time.sleep(random.uniform(5, 8))
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".section-hero-header-title, h1, [role='heading']"))
                        )
                    except:
                        pass
                    self.log_status("✅ Đã chọn địa điểm từ kết quả tìm kiếm!")
                except Exception as e:
                    self.log_status(f"⚠️ Không thể chọn từ kết quả: {e}", True)

            current_url = self.driver.current_url
            if '/maps/place/' in current_url:
                self.log_status("✅ Đã load trang địa điểm!")
                return True

            time.sleep(random.uniform(3, 5))
            current_url = self.driver.current_url
            if '/maps/place/' in current_url:
                self.log_status("✅ Đã load trang địa điểm!")
                return True

            try:
                heading = self.driver.find_element(By.CSS_SELECTOR, "h1, .section-hero-header-title, [data-attrid='title']")
                if heading.is_displayed():
                    self.log_status("✅ Đã load trang địa điểm!")
                    return True
            except:
                pass

            self.log_status("✅ Đã load trang địa điểm!")
            return True

        except Exception as e:
            self.log_status(f"❌ Lỗi điều hướng: {e}", True)
            return False

    def _switch_to_review_iframe(self):
        try:
            iframe = self.driver.find_element(By.NAME, "goog-reviews-write-widget")
            self.driver.switch_to.frame(iframe)
            time.sleep(1)
            return True
        except:
            return False

    def _switch_to_main(self):
        try:
            self.driver.switch_to.default_content()
        except:
            pass

    def click_write_review_button(self):
        self.log_status("Dang tim nut 'Write a review'...")
        try:
            self.log_status("⏳ Đợi trang load đầy đủ...")
            time.sleep(random.uniform(5, 8))

            self.log_status("Đang tìm tab 'Reviews'...")
            try:
                reviews_tab = self.driver.find_elements(By.XPATH,
                    "//button[contains(@data-tab, 'review') or contains(@aria-label, 'review') or contains(@aria-label, 'đánh giá')]"
                )
                for tab in reviews_tab:
                    try:
                        if tab.is_displayed() and tab.is_enabled():
                            tab_text = (tab.text or '').strip().lower()
                            if 'review' in tab_text or 'đánh giá' in tab_text:
                                self.log_status(f"✅ Tìm thấy tab Reviews: '{tab.text}'")
                                self.driver.execute_script("arguments[0].click();", tab)
                                time.sleep(random.uniform(2, 3))
                                break
                    except:
                        continue

                all_buttons = self.driver.find_elements(By.XPATH, "//button")
                for btn in all_buttons:
                    try:
                        btn_text = (btn.text or '').strip().lower()
                        if ('review' in btn_text and len(btn_text) < 15) or ('đánh giá' in btn_text):
                            if btn.is_displayed() and btn.is_enabled():
                                self.log_status(f"✅ Tìm thấy tab Reviews (text): '{btn.text}'")
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(random.uniform(2, 3))
                                break
                    except:
                        continue
            except:
                pass

            self.log_status("📜 Đang cuộn xuống để tìm nút...")

            for i in range(5):
                self.driver.execute_script(f"window.scrollBy(0, {300 + i * 200});")
                time.sleep(random.uniform(1, 2))

            try:
                self.driver.save_screenshot("debug_before_click.png")
                self.log_status("📸 Đã chụp ảnh debug_before_click.png")
            except:
                pass

            for attempt in range(3):
                self.log_status(f"🔍 Attempt {attempt+1}/3: Tìm nút 'Write a review'...")

                try:
                    btn = self.driver.find_element(By.XPATH, "//button[@data-value='Write a review' or @data-value='Viết bài đánh giá']")
                    if btn.is_displayed() and btn.is_enabled():
                        self.log_status(f"✅ Tìm thấy button (data-value): '{btn.text}'")
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                        time.sleep(random.uniform(1, 2))
                        ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                        self.log_status("✅ Đã click nút 'Write a review'!")
                        time.sleep(random.uniform(3, 5))
                        return True
                except:
                    pass

                try:
                    btn = self.driver.find_element(By.XPATH, "//button[@aria-label='Write a review' or @aria-label='Viết bài đánh giá']")
                    if btn.is_displayed() and btn.is_enabled():
                        self.log_status(f"✅ Tìm thấy button (aria-label): '{btn.text}'")
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                        time.sleep(random.uniform(1, 2))
                        ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                        self.log_status("✅ Đã click nút 'Write a review'!")
                        time.sleep(random.uniform(3, 5))
                        return True
                except:
                    pass

                all_buttons = self.driver.find_elements(By.XPATH, "//button")
                for btn in all_buttons:
                    try:
                        btn_text = (btn.text or '').strip()
                        if (btn_text == "Write a review" or btn_text == "Viết bài đánh giá") and btn.is_displayed() and btn.is_enabled():
                            self.log_status(f"✅ Tìm thấy button (text): '{btn_text}'")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", btn)
                            time.sleep(random.uniform(1, 2))
                            ActionChains(self.driver).move_to_element(btn).pause(0.5).click().perform()
                            self.log_status("✅ Đã click nút 'Write a review'!")
                            time.sleep(random.uniform(3, 5))
                            return True
                    except:
                        continue

                role_btns = self.driver.find_elements(By.XPATH, "//*[contains(@role, 'button')]")
                for el in role_btns:
                    try:
                        txt = (el.text or '').strip()
                        aria = (el.get_attribute('aria-label') or '').strip()
                        if ("write a review" in txt.lower() or "viết đánh giá" in txt.lower()
                            or "write a review" in aria.lower() or "viết đánh giá" in aria.lower()):
                            if el.is_displayed():
                                self.log_status(f"✅ Tìm thấy role=button: '{txt}' aria='{aria}'")
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", el)
                                time.sleep(random.uniform(1, 2))
                                ActionChains(self.driver).move_to_element(el).pause(0.5).click().perform()
                                self.log_status("✅ Đã click nút 'Write a review'!")
                                time.sleep(random.uniform(3, 5))
                                return True
                    except:
                        continue

                if attempt < 2:
                    self.log_status(f"⏳ Chưa tìm thấy, scroll thêm... (attempt {attempt+1})")
                    for i in range(3):
                        self.driver.execute_script(f"window.scrollBy(0, {200 + i * 150});")
                        time.sleep(random.uniform(1, 2))

            self.log_status("❌ KHÔNG TÌM THẤY NÚT 'Write a review'!", True)
            self.log_status("💡 Gợi ý:", True)
            self.log_status("1. Kiểm tra file debug_before_click.png", True)
            self.log_status("2. Đảm bảo bạn đã đăng nhập đúng tài khoản", True)
            self.log_status("3. Địa điểm này có cho phép đánh giá không?", True)

            return False

        except Exception as e:
            self.log_status(f"❌ Lỗi click nút đánh giá: {e}", True)
            return False

    def _click_element(self, element):
        try:
            if not element.is_displayed() or not element.is_enabled():
                return False
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();", element)
            time.sleep(0.4)
            element.click()
            return True
        except:
            return False

    def _get_review_dialog(self):
        try:
            candidates = self.driver.find_elements(By.XPATH, "//*[contains(@role, 'dialog')]")
            for dialog in candidates:
                if not dialog.is_displayed():
                    continue
                text = (dialog.text or '').strip().lower()
                aria = (dialog.get_attribute('aria-label') or '').lower()
                cls = (dialog.get_attribute('class') or '').lower()
                if ('review' in text or 'danh gia' in text or 'dang' in text or 'review' in aria
                    or 'hfYJnf' in cls or 'HPTfYd' in cls or dialog.get_attribute('role') == 'dialog'):
                    return dialog
        except:
            pass
        return None

    STAR_ARIA_MAP = {
        1: ["mot sao", "1 star", "1 Star", "One star"],
        2: ["hai sao", "2 star", "2 Star", "Two stars"],
        3: ["ba sao", "3 star", "3 Star", "Three stars"],
        4: ["bon sao", "4 star", "4 Star", "Four stars"],
        5: ["nam sao", "5 star", "5 Star", "Five stars"]
    }

    def select_star_rating(self, stars=5):
        self.log_status(f"Dang chon {stars} sao...")
        try:
            time.sleep(random.uniform(2, 4))
            self._switch_to_review_iframe()
            time.sleep(3)

            target_arias = self.STAR_ARIA_MAP.get(stars, [f"{stars} sao"])

            for aria in target_arias:
                for selector in [f"//div[contains(@aria-label, '{aria}')]", f"//*[contains(@aria-label, '{aria}')]"]:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            if not elem.is_displayed():
                                continue
                            cls = (elem.get_attribute('class') or '')
                            if any(x in cls for x in ['ZkP5Je', 'BHOKXe', 'ceNzKf', 'YTkVxc']):
                                continue
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", elem)
                                self.log_status(f"Da chon {stars} sao")
                                time.sleep(random.uniform(1, 2))
                                self._switch_to_main()
                                return True
                            except:
                                continue
                    except:
                        continue

            try:
                container = self.driver.find_element(By.XPATH, "//div[contains(@class, 'lv4IMd')]")
                if container.is_displayed():
                    stars_in_container = container.find_elements(By.XPATH, ".//div[contains(@class, 's2xyy')]")
                    if len(stars_in_container) >= stars:
                        target = stars_in_container[stars - 1]
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", target)
                        self.log_status(f"Da chon {stars} sao (container)")
                        time.sleep(random.uniform(1, 2))
                        self._switch_to_main()
                        return True
            except:
                pass

            try:
                result = self.driver.execute_script(f"""
                (function() {{
                    var targetArias = {json.dumps(target_arias)};
                    var allDivs = document.querySelectorAll('div[class*="s2xyy"], div[aria-label*="star"], div[aria-label*="Star"], div[aria-label*="sao"]');
                    for (var i = 0; i < allDivs.length; i++) {{
                        var el = allDivs[i];
                        var aria = (el.getAttribute('aria-label') || '');
                        for (var j = 0; j < targetArias.length; j++) {{
                            if (aria.toLowerCase() === targetArias[j].toLowerCase()) {{
                                el.scrollIntoView({{block: 'center'}});
                                el.click();
                                return true;
                            }}
                        }}
                    }}
                    return false;
                }})();
                """)
                if result:
                    self.log_status(f"Da chon {stars} sao (JS)")
                    time.sleep(random.uniform(1, 2))
                    self._switch_to_main()
                    return True
            except:
                pass

            self.log_status("KHONG THE CHON SAO!", True)
            self._switch_to_main()
            return False
        except Exception as e:
            self._switch_to_main()
            self.log_status(f"Loi chon sao: {e}", True)
            return False

    def _set_comment_value(self, element, value):
        try:
            element.clear()
        except:
            pass
        try:
            element.send_keys(value)
            return True
        except:
            try:
                self.driver.execute_script("""
                if (arguments[0].tagName.toLowerCase() === 'textarea' || arguments[0].tagName.toLowerCase() === 'input') {
                    arguments[0].value = arguments[1];
                } else {
                    arguments[0].textContent = arguments[1];
                    arguments[0].innerText = arguments[1];
                }
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """, element, value)
                return True
            except:
                return False

    def _find_comment_box(self):
        time.sleep(random.uniform(2, 4))
        self._switch_to_review_iframe()

        candidate_selectors = [
            "//textarea[@aria-label='Nhap bai danh gia']",
            "//textarea[contains(@aria-label, 'Nhap bai danh gia')]",
            "//textarea[contains(@aria-label, 'Enter review')]",
            "//textarea[contains(@aria-label, 'review') or contains(@aria-label, 'danh gia')]",
            "//textarea[contains(@placeholder, 'Mo ta') or contains(@placeholder, 'trai nghiem')]",
            "//textarea[contains(@class, 'VfPpkd-fmcmS')]",
            "//textarea",
            "//div[@role='textbox']",
            "//*[@contenteditable='true']",
        ]

        for selector in candidate_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for item in elements:
                    try:
                        if not item.is_displayed() or not item.is_enabled():
                            continue
                        tag = (item.tag_name or '').lower()
                        role = (item.get_attribute('role') or '').lower()
                        if tag == 'textarea' or role == 'textbox' or item.get_attribute('contenteditable') == 'true':
                            self.log_status(f"Tim thay o binh luan: tag={tag}")
                            return item
                    except:
                        continue
            except:
                continue

        try:
            elem = self.driver.execute_script("""
            (function() {
                var candidates = document.querySelectorAll('textarea');
                for (var i = 0; i < candidates.length; i++) {
                    var el = candidates[i];
                    var style = window.getComputedStyle(el);
                    var rect = el.getBoundingClientRect();
                    if (style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 50 && rect.height > 20) {
                        return el;
                    }
                }
                return null;
            })();
            """)
            if elem:
                self.log_status("Tim thay textarea qua JavaScript")
                return elem
        except:
            pass
        return None

    def write_comment(self, comment):
        self.log_status("Dang viet binh luan...")
        try:
            comment_box = self._find_comment_box()
            if comment_box:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'}); arguments[0].focus();",
                    comment_box
                )
                time.sleep(random.uniform(0.5, 1))
                try:
                    comment_box.click()
                    time.sleep(0.3)
                except:
                    pass
                if self._set_comment_value(comment_box, comment):
                    self.log_status("Da nhap binh luan!")
                    time.sleep(random.uniform(1, 2))
                else:
                    self.log_status("Khong the nhap binh luan", True)
                    return False
            else:
                self.log_status("Khong tim thay o nhap binh luan", True)
                return False
            self._switch_to_main()
            return True
        except Exception as e:
            self._switch_to_main()
            self.log_status(f"Loi viet binh luan: {e}", True)
            return False

    def submit_review(self):
        self.log_status("📤 Đang gửi đánh giá...")
        try:
            self._switch_to_review_iframe()

            submit_selectors = [
                "//button[contains(@aria-label, 'Đăng') and not(contains(@aria-label, 'Đăng công khai'))]",
                "//button[contains(@aria-label, 'Đăng')]",
                "//button[.//span[contains(text(), 'Đăng')]]",
                "//button[.//span[text()='Post']]",
                "//button[text()='Post']",
                "//button[contains(text(), 'Đăng')]",
                "//button[contains(text(), 'Post')]",
                "//button[contains(@aria-label, 'Post')]",
                "//button[contains(@jsaction, 'submit')]",
            ]

            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for btn in elements:
                        try:
                            if not btn.is_displayed() or not btn.is_enabled():
                                continue
                            btn_text = (btn.text or '').strip().lower()
                            aria = (btn.get_attribute('aria-label') or '').lower()
                            if 'dang cong khai' in aria or 'post publicly' in aria:
                                continue
                            if btn_text in ['đăng', 'post'] or 'submit' in aria or 'post' in aria or 'đăng' in aria:
                                self.log_status(f"✅ Tìm thấy nút gửi: text='{btn.text}' aria='{btn.get_attribute('aria-label')}'")
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block:'center', behavior:'smooth'});",
                                    btn
                                )
                                time.sleep(0.5)
                                ActionChains(self.driver).move_to_element(btn).pause(0.3).click().perform()
                                self.log_status("✅ Đã gửi đánh giá!")
                                time.sleep(random.uniform(3, 5))
                                self._switch_to_main()
                                return True
                        except:
                            continue
                except:
                    continue

            self.log_status("🔍 Fallback: Ctrl+Enter...")
            try:
                textarea = self.driver.find_element(By.XPATH, "//textarea[contains(@aria-label, 'Nhập bài đánh giá')]")
                textarea.send_keys(Keys.CONTROL + Keys.ENTER)
                self.log_status("✅ Đã gửi đánh giá bằng Ctrl+Enter!")
                time.sleep(random.uniform(3, 5))
                self._switch_to_main()
                return True
            except:
                pass

            self._switch_to_main()
            self.log_status("❌ Không thể gửi đánh giá", True)
            return False

        except Exception as e:
            self._switch_to_main()
            self.log_status(f"❌ Lỗi gửi đánh giá: {e}", True)
            return False

    def _human_typing(self, element, text):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.03, 0.12))

    def close_browser(self):
        try:
            if self.driver:
                self.driver.quit()
                self.log_status("Da dong Chrome!")
        except:
            pass

    def run_review(self, email, password, place_url, comment, stars=5):
        try:
            if not self.start_browser():
                return False
            if not self.login_google(email, password):
                return False
            if not self.navigate_to_place(place_url):
                return False
            if not self.click_write_review_button():
                return False
            if not self.select_star_rating(stars):
                return False
            if not self.write_comment(comment):
                return False
            if not self.submit_review():
                return False
            self.log_status("HOAN THANH DANH GIA!")
            return True
        except Exception as e:
            self.log_status(f"Loi: {e}", True)
            return False


def save_config(data):
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Loi luu config: {e}")
        return False


def load_config():
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Loi doc config: {e}")
        return None
