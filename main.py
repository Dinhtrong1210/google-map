"""
Google Maps Review Bot - Desktop App
Login + Sidebar + API integration
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter import font as tkfont
import threading
import os
import json
import time
import random
import urllib.request
import urllib.error
from datetime import datetime
from review_bot import GoogleMapsReviewBot

VERSION = "2.0.0"
CONFIG_FILE = "tool_config.json"

SERVER_URL = "http://localhost:5000"

COLORS = {
    'bg':       '#0f0f1a',
    'bg2':      '#1a1a2e',
    'bg3':      '#252542',
    'bg4':      '#30305a',
    'fg':       '#e8e8f0',
    'dim':      '#7878a0',
    'accent':   '#00d4ff',
    'success':  '#00e676',
    'error':    '#ff4757',
    'warning':  '#ffc107',
    'star':     '#ffd700',
    'sidebar':  '#0a1228',
    'active':   '#112240',
    'log_bg':   '#050510',
    'log_fg':   '#00ff88',
    'border':   '#1e3a5f',
}


def api_call(endpoint, method='GET', data=None, token=None, server_url=None):
    try:
        url = f"{server_url or SERVER_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-Auth-Token'] = token

        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except:
            return {'error': f'HTTP {e.code}'}
    except Exception as e:
        return {'error': str(e)}


class ReviewBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Google Maps Review Bot v{VERSION}")
        self.root.geometry("1050x720")
        self.root.minsize(950, 650)
        self.root.configure(bg=COLORS['bg'])

        self._setup_fonts()

        self.token = None
        self.user_info = None
        self.bots = []
        self.is_running = False
        self._stop_event = threading.Event()
        self.current_page = 'home'
        self.server_url = SERVER_URL

        self._load_config()
        self._show_login_screen()

    def _setup_fonts(self):
        self.fonts = {
            'title':    tkfont.Font(family="Segoe UI", size=16, weight="bold"),
            'heading':  tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            'body':     tkfont.Font(family="Segoe UI", size=10),
            'small':    tkfont.Font(family="Segoe UI", size=9),
            'tiny':     tkfont.Font(family="Segoe UI", size=8),
            'log':      tkfont.Font(family="Consolas", size=9),
            'stat_num': tkfont.Font(family="Consolas", size=24, weight="bold"),
            'stat_sm':  tkfont.Font(family="Consolas", size=16, weight="bold"),
            'sidebar':  tkfont.Font(family="Segoe UI", size=11),
            'sidebar_active': tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            'btn':      tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            'big':      tkfont.Font(family="Segoe UI", size=20, weight="bold"),
        }

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    cfg = json.load(f)
                self.server_url = cfg.get('server_url', SERVER_URL)
                self.token = cfg.get('token')
        except:
            pass

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'server_url': self.server_url, 'token': self.token}, f)
        except:
            pass

    def _clear_window(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ==================== LOGIN SCREEN ====================

    def _show_login_screen(self):
        self._clear_window()

        container = tk.Frame(self.root, bg=COLORS['bg'])
        container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(container, text="GOOGLE MAPS", font=self.fonts['big'],
                 fg=COLORS['accent'], bg=COLORS['bg']).pack()
        tk.Label(container, text="REVIEW BOT", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(pady=(0, 4))
        tk.Label(container, text=f"v{VERSION}", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg']).pack(pady=(0, 24))

        form = tk.Frame(container, bg=COLORS['bg'], width=360)
        form.pack()

        tk.Label(form, text="Server URL", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg'], anchor=tk.W).pack(fill=tk.X)
        self.login_server = tk.Entry(form, bg=COLORS['bg3'], fg=COLORS['fg'],
                                     insertbackground=COLORS['fg'], font=self.fonts['body'],
                                     relief=tk.FLAT)
        self.login_server.pack(fill=tk.X, ipady=6, pady=(2, 10))
        self.login_server.insert(0, self.server_url)

        tk.Label(form, text="Username hoac Email", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg'], anchor=tk.W).pack(fill=tk.X)
        self.login_user = tk.Entry(form, bg=COLORS['bg3'], fg=COLORS['fg'],
                                   insertbackground=COLORS['fg'], font=self.fonts['body'],
                                   relief=tk.FLAT)
        self.login_user.pack(fill=tk.X, ipady=6, pady=(2, 10))

        tk.Label(form, text="Mat khau", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg'], anchor=tk.W).pack(fill=tk.X)
        self.login_pass = tk.Entry(form, bg=COLORS['bg3'], fg=COLORS['fg'],
                                   insertbackground=COLORS['fg'], font=self.fonts['body'],
                                   show='*', relief=tk.FLAT)
        self.login_pass.pack(fill=tk.X, ipady=6, pady=(2, 16))

        self.login_status = tk.Label(form, text="", font=self.fonts['small'],
                                     fg=COLORS['error'], bg=COLORS['bg'])
        self.login_status.pack(pady=(0, 8))

        tk.Button(form, text="DANG NHAP", command=self._do_login,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                  relief=tk.FLAT, cursor="hand2", width=30).pack(ipady=4)

        tk.Label(form, text="Chua co tai khoan? Dang ky tai web admin",
                 font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['bg']).pack(pady=(12, 0))

        self.login_pass.bind('<Return>', lambda e: self._do_login())
        self.login_user.focus_set()

    def _do_login(self):
        server = self.login_server.get().strip()
        username = self.login_user.get().strip()
        password = self.login_pass.get().strip()

        if not username or not password:
            self.login_status.config(text="Nhap day du thong tin!")
            return

        self.server_url = server
        self.login_status.config(text="Dang ket noi...", fg=COLORS['warning'])
        self.root.update()

        resp = api_call('/api/tool/login', 'POST', {'username': username, 'password': password}, server_url=self.server_url)

        if 'error' in resp:
            self.login_status.config(text=resp['error'], fg=COLORS['error'])
            return

        self.token = resp.get('token')
        self.user_info = resp.get('user')
        self._save_config()
        self._show_main_ui()

    # ==================== MAIN UI ====================

    def _show_main_ui(self):
        self._clear_window()

        sidebar = tk.Frame(self.root, bg=COLORS['sidebar'], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="REVIEW BOT", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['sidebar']).pack(pady=(16, 2), padx=16, anchor=tk.W)
        tk.Label(sidebar, text=self.user_info.get('username', ''),
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['sidebar']).pack(padx=16, anchor=tk.W)

        sep = tk.Frame(sidebar, bg=COLORS['border'], height=1)
        sep.pack(fill=tk.X, padx=12, pady=12)

        self.sidebar_btns = {}
        menu_items = [
            ('home', '🏠  Home'),
            ('history', '📋  Lich su'),
            ('account', '👤  Tai khoan'),
            ('stats', '📊  Thong ke'),
        ]

        for key, label in menu_items:
            btn = tk.Label(sidebar, text=label, font=self.fonts['sidebar'],
                           fg=COLORS['dim'], bg=COLORS['sidebar'],
                           cursor="hand2", anchor=tk.W, padx=16, pady=10)
            btn.pack(fill=tk.X)
            btn.bind('<Button-1>', lambda e, k=key: self._navigate(k))
            self.sidebar_btns[key] = btn

        sep2 = tk.Frame(sidebar, bg=COLORS['border'], height=1)
        sep2.pack(fill=tk.X, padx=12, pady=12)

        self.sidebar_balance = tk.Label(sidebar, text="", font=self.fonts['small'],
                                         fg=COLORS['success'], bg=COLORS['sidebar'], anchor=tk.W, padx=16)
        self.sidebar_balance.pack(fill=tk.X)

        bottom = tk.Frame(sidebar, bg=COLORS['sidebar'])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)
        tk.Label(bottom, text="Dang xuat", font=self.fonts['tiny'],
                 fg=COLORS['error'], bg=COLORS['sidebar'], cursor="hand2"
                 ).pack(anchor=tk.W)
        bottom.winfo_children()[-1].bind('<Button-1>', lambda e: self._logout())

        self.main_area = tk.Frame(self.root, bg=COLORS['bg'])
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._update_sidebar_balance()
        self._navigate('home')

    def _update_sidebar_balance(self):
        if self.user_info:
            bal = self.user_info.get('balance', 0)
            remaining = bal // 12000
            self.sidebar_balance.config(text=f"Vi: {bal:,}d\nCon lai: {remaining} danh gia")

    def _navigate(self, page):
        self.current_page = page
        for key, btn in self.sidebar_btns.items():
            if key == page:
                btn.config(bg=COLORS['active'], fg=COLORS['accent'], font=self.fonts['sidebar_active'])
            else:
                btn.config(bg=COLORS['sidebar'], fg=COLORS['dim'], font=self.fonts['sidebar'])

        for w in self.main_area.winfo_children():
            w.destroy()

        if page == 'home':
            self._build_home_page()
        elif page == 'history':
            self._build_history_page()
        elif page == 'account':
            self._build_account_page()
        elif page == 'stats':
            self._build_stats_page()

    def _logout(self):
        if messagebox.askyesno("Xac nhan", "Dang xuat?"):
            self.token = None
            self.user_info = None
            self._save_config()
            self._show_login_screen()

    # ==================== HOME PAGE ====================

    def _build_home_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Chay danh gia", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W)
        tk.Label(page, text=f"Vi: {self.user_info.get('balance', 0):,}d | Con lai: {self.user_info.get('balance', 0) // 12000} danh gia",
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(2, 12))

        sec1 = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec1.pack(fill=tk.X, pady=(0, 10))
        inner1 = tk.Frame(sec1, bg=COLORS['bg2'], padx=14, pady=10)
        inner1.pack(fill=tk.X)

        tk.Label(inner1, text="Link Google Maps:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)
        self.url_entry = tk.Entry(inner1, bg=COLORS['bg3'], fg=COLORS['fg'],
                                  insertbackground=COLORS['fg'], font=self.fonts['body'], relief=tk.FLAT)
        self.url_entry.pack(fill=tk.X, ipady=5, pady=(2, 8))

        row_opt = tk.Frame(inner1, bg=COLORS['bg2'])
        row_opt.pack(fill=tk.X, pady=(0, 4))

        tk.Label(row_opt, text="Sao:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.star_var = tk.IntVar(value=5)
        for s in range(1, 6):
            tk.Radiobutton(row_opt, text=f"{'*'*s}", variable=self.star_var, value=s,
                           bg=COLORS['bg2'], fg=COLORS['star'], selectcolor=COLORS['bg3'],
                           activebackground=COLORS['bg2']).pack(side=tk.LEFT, padx=3)

        tk.Label(row_opt, text="  Chrome:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT, padx=(12, 0))
        self.chrome_count = tk.IntVar(value=1)
        tk.Spinbox(row_opt, from_=1, to=10, textvariable=self.chrome_count, width=3,
                   bg=COLORS['bg3'], fg=COLORS['fg'], font=self.fonts['body'],
                   buttonbackground=COLORS['bg4'], relief=tk.FLAT).pack(side=tk.LEFT, padx=4)

        sec2 = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec2.pack(fill=tk.X, pady=(0, 10))
        inner2 = tk.Frame(sec2, bg=COLORS['bg2'], padx=14, pady=10)
        inner2.pack(fill=tk.X)

        tk.Label(inner2, text="Noi dung binh luan (moi dong = 1 danh gia):", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)
        self.comment_text = scrolledtext.ScrolledText(inner2, height=4, bg=COLORS['bg3'],
                                                       fg=COLORS['fg'], insertbackground=COLORS['fg'],
                                                       font=self.fonts['body'], relief=tk.FLAT, wrap=tk.WORD)
        self.comment_text.pack(fill=tk.X, pady=(2, 4))

        self.comment_hint = tk.Label(inner2, text="0 dong", font=self.fonts['tiny'],
                                     fg=COLORS['dim'], bg=COLORS['bg2'])
        self.comment_hint.pack(anchor=tk.W)
        self.comment_text.bind('<KeyRelease>', self._update_comment_hint)

        btn_row = tk.Frame(page, bg=COLORS['bg'])
        btn_row.pack(fill=tk.X, pady=(0, 10))

        self.btn_start = tk.Button(btn_row, text=">> BAT DAU DANH GIA <<",
                                    command=self._start_review, bg=COLORS['success'], fg='#000',
                                    font=self.fonts['btn'], relief=tk.FLAT, padx=20, pady=6, cursor="hand2")
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = tk.Button(btn_row, text="DUNG", command=self._stop_review,
                                   bg=COLORS['error'], fg='white', font=self.fonts['btn'],
                                   relief=tk.FLAT, padx=16, pady=6, cursor="hand2", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(btn_row, text="Xoa Chrome", command=self._kill_chrome,
                  bg=COLORS['warning'], fg='#000', font=self.fonts['small'],
                  relief=tk.FLAT, padx=8, pady=6, cursor="hand2").pack(side=tk.RIGHT)

        log_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_inner = tk.Frame(log_frame, bg=COLORS['bg2'], padx=4, pady=4)
        log_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_inner, text="  LOG", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)
        self.log_text = scrolledtext.ScrolledText(log_inner, bg=COLORS['log_bg'], fg=COLORS['log_fg'],
                                                   insertbackground=COLORS['log_fg'], font=self.fonts['log'],
                                                   relief=tk.FLAT, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.log("San sang! Nhap thong tin va bat dau danh gia.")

    def _update_comment_hint(self, event=None):
        raw = self.comment_text.get('1.0', tk.END).strip()
        lines = [l for l in raw.split('\n') if l.strip()] if raw else []
        self.comment_hint.config(text=f"{len(lines)} dong | Moi Chrome lay 1 dong ngau nhien")

    def _log(self, msg, is_error=False):
        def _do():
            tag = "[ERR] " if is_error else ""
            self.log_text.insert(tk.END, f"{tag}{msg}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _do)

    def _refresh_balance(self):
        resp = api_call('/api/tool/refresh', 'GET', token=self.token, server_url=self.server_url)
        if 'error' not in resp:
            self.user_info['balance'] = resp.get('balance', 0)
            self.user_info['total_reviews'] = resp.get('total_reviews', 0)
            self._update_sidebar_balance()

    def _start_review(self):
        url = self.url_entry.get().strip()
        raw = self.comment_text.get('1.0', tk.END).strip()
        comment_lines = [l.strip() for l in raw.split('\n') if l.strip()] if raw else []
        chrome_count = self.chrome_count.get()
        stars = self.star_var.get()

        if not url:
            messagebox.showerror("Loi", "Nhap Link Google Maps!")
            return
        if not comment_lines:
            messagebox.showerror("Loi", "Nhap it nhat 1 noi dung binh luan!")
            return
        for i, line in enumerate(comment_lines):
            if len(line) < 5:
                messagebox.showerror("Loi", f"Dong {i+1} qua ngan:\n{line}")
                return

        self._refresh_balance()
        balance = self.user_info.get('balance', 0)
        needed = 12000
        if balance < needed:
            messagebox.showerror("Loi", f"So du khong du!\nHien tai: {balance:,}d\nCan: {needed:,}d\n\nVui long nap them tai web.")
            return

        if not messagebox.askyesno("Xac nhan", f"Chay {chrome_count} Chrome voi {len(comment_lines)} noi dung?\nSo du: {balance:,}d"):
            return

        self.log_text.delete('1.0', tk.END)
        self._log(f"BAT DAU: {chrome_count} Chrome | {len(comment_lines)} noi dung")
        self._stop_event.clear()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        thread = threading.Thread(target=self._run_review,
                                  args=(url, comment_lines, stars, chrome_count))
        thread.daemon = True
        thread.start()

    def _run_review(self, url, comment_lines, stars, chrome_count):
        try:
            self.bots = []
            shuffled = comment_lines[:]
            random.shuffle(shuffled)
            idx = 0

            resp = api_call('/api/tool/profile', 'GET', token=self.token, server_url=self.server_url)
            if 'error' in resp:
                self._log(f"Loi kiem tra tai khoan: {resp['error']}", True)
                return

            email = resp.get('email', '')
            profile_dir = os.path.join(os.getcwd(), 'profiles',
                                       email.replace('@', '_at_').replace('.', '_'))
            os.makedirs(profile_dir, exist_ok=True)

            self._log(f"Tai khoan: {resp.get('username')} | So du: {resp.get('balance'):,}d")

            for j in range(chrome_count):
                if self._stop_event.is_set():
                    break

                comment = shuffled[idx % len(shuffled)]
                idx += 1

                self._log(f"\n--- Chrome {j+1}/{chrome_count} ---")
                self._log(f"  Noi dung: {comment[:60]}...")

                def run_one(c_idx, c_comment):
                    bot = None
                    try:
                        self._refresh_balance()
                        if self.user_info.get('balance', 0) < 12000:
                            self._log("So du khong du! Dung.", True)
                            return

                        deduct_resp = api_call('/api/tool/deduct', 'POST',
                                               {'place_url': url, 'comment': c_comment, 'stars': stars},
                                               token=self.token, server_url=self.server_url)
                        if 'error' in deduct_resp:
                            self._log(f"Loi tru tien: {deduct_resp['error']}", True)
                            return

                        self.user_info['balance'] = deduct_resp.get('balance', 0)
                        self._update_sidebar_balance()
                        self._log(f"  Da tru 12,000d | Con lai: {deduct_resp.get('balance', 0):,}d")

                        bot = GoogleMapsReviewBot(
                            headless=False,
                            user_data_dir=profile_dir,
                            debug_port=9222 + c_idx
                        )
                        bot.set_status_callback(self._log)
                        self.bots.append(bot)

                        if not bot.start_browser():
                            self._log("Loi Chrome!", True)
                            return
                        if not bot.login_google(email, self.user_info.get('password', '')):
                            self._log("Loi dang nhap!", True)
                            return
                        if not bot.navigate_to_place(url):
                            self._log("Loi dia diem!", True)
                            return
                        if not bot.click_write_review_button():
                            self._log("Loi nut review!", True)
                            return
                        if not bot.select_star_rating(stars):
                            self._log("Loi chon sao!", True)
                            return
                        if not bot.write_comment(c_comment):
                            self._log("Loi viet binh luan!", True)
                            return
                        if not bot.submit_review():
                            self._log("Loi gui danh gia!", True)
                            return

                        self._log(f"  HOAN THANH!")

                    except Exception as e:
                        self._log(f"  Loi: {e}", True)
                    finally:
                        if bot:
                            try:
                                bot.close_browser()
                            except:
                                pass

                t = threading.Thread(target=run_one, args=(j, comment))
                t.start()
                time.sleep(3)

            self._log("\n" + "=" * 40)
            self._log("HOAN TAT TAT CA!")
            self._refresh_balance()

        except Exception as e:
            self._log(f"Loi chinh: {e}", True)
        finally:
            self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def _stop_review(self):
        if messagebox.askyesno("Xac nhan", "Dung tat ca?"):
            self._stop_event.set()
            for bot in self.bots:
                try:
                    bot.close_browser()
                except:
                    pass
            self.bots = []
            self._kill_chrome()
            self._log("Da dung!")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

    def _kill_chrome(self):
        os.system('taskkill /f /im chrome.exe 2>nul')

    # ==================== HISTORY PAGE ====================

    def _build_history_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Lich su danh gia", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 12))

        resp = api_call('/api/tool/history', 'GET', token=self.token, server_url=self.server_url)

        if 'error' in resp:
            tk.Label(page, text=f"Loi: {resp['error']}", fg=COLORS['error'], bg=COLORS['bg']).pack()
            return

        reviews = resp.get('reviews', [])
        transactions = resp.get('transactions', [])

        sec = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        sec_inner = tk.Frame(sec, bg=COLORS['bg2'], padx=10, pady=10)
        sec_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(sec_inner, text="Danh gia gan day", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 6))

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Hist.Treeview", background=COLORS['bg3'], foreground=COLORS['fg'],
                        fieldbackground=COLORS['bg3'], font=self.fonts['small'], rowheight=24)
        style.configure("Hist.Treeview.Heading", background=COLORS['bg4'], foreground=COLORS['fg'],
                        font=self.fonts['small'])

        cols = ("time", "url", "stars", "cost", "status")
        tree = ttk.Treeview(sec_inner, columns=cols, show="headings", style="Hist.Treeview", height=12)
        tree.heading("time", text="Thoi gian")
        tree.heading("url", text="Dia diem")
        tree.heading("stars", text="Sao")
        tree.heading("cost", text="Chi phi")
        tree.heading("status", text="Trang thai")
        tree.column("time", width=140)
        tree.column("url", width=300)
        tree.column("stars", width=60)
        tree.column("cost", width=90)
        tree.column("status", width=80)

        for r in reviews:
            tree.insert("", tk.END, values=(
                r.get('created_at', ''),
                r.get('place_url', '')[:50],
                '⭐' * r.get('stars', 5),
                f"{r.get('cost', 0):,}d",
                r.get('status', '')
            ))

        tree.pack(fill=tk.BOTH, expand=True)

        if not reviews:
            tk.Label(sec_inner, text="Chua co danh gia nao", font=self.fonts['small'],
                     fg=COLORS['dim'], bg=COLORS['bg2']).pack(pady=20)

    # ==================== ACCOUNT PAGE ====================

    def _build_account_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Thong tin tai khoan", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 16))

        resp = api_call('/api/tool/profile', 'GET', token=self.token, server_url=self.server_url)
        if 'error' in resp:
            tk.Label(page, text=f"Loi: {resp['error']}", fg=COLORS['error'], bg=COLORS['bg']).pack()
            return

        info_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        info_frame.pack(fill=tk.X, pady=(0, 12))
        info_inner = tk.Frame(info_frame, bg=COLORS['bg2'], padx=20, pady=16)
        info_inner.pack(fill=tk.X)

        fields = [
            ("Username", resp.get('username', '')),
            ("Email", resp.get('email', '')),
            ("Ho ten", resp.get('fullname', '')),
            ("Vai tro", resp.get('role', '')),
            ("Ngay tao", resp.get('created_at', '')),
            ("Tong danh gia", str(resp.get('total_reviews', 0))),
        ]

        for label, value in fields:
            row = tk.Frame(info_inner, bg=COLORS['bg2'])
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}:", font=self.fonts['small'], fg=COLORS['dim'],
                     bg=COLORS['bg2'], width=14, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=self.fonts['body'], fg=COLORS['fg'],
                     bg=COLORS['bg2'], anchor=tk.W).pack(side=tk.LEFT)

        wallet_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['accent'], highlightthickness=1)
        wallet_frame.pack(fill=tk.X, pady=(0, 12))
        wallet_inner = tk.Frame(wallet_frame, bg=COLORS['bg2'], padx=20, pady=16)
        wallet_inner.pack(fill=tk.X)

        tk.Label(wallet_inner, text="So du vi", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(anchor=tk.W)
        tk.Label(wallet_inner, text=f"{resp.get('balance', 0):,}d", font=self.fonts['big'],
                 fg=COLORS['accent'], bg=COLORS['bg2']).pack(anchor=tk.W)
        tk.Label(wallet_inner, text=f"Con lai: {resp.get('balance', 0) // 12000} danh gia (12,000d/danh gia)",
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['bg2']).pack(anchor=tk.W, pady=(4, 0))

        tk.Button(page, text="Nap tien tai web", command=lambda: os.system(f"start {self.server_url}"),
                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                  relief=tk.FLAT, padx=16, pady=6, cursor="hand2").pack(anchor=tk.W, pady=(8, 0))

    # ==================== STATS PAGE ====================

    def _build_stats_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Thong ke", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 16))

        resp = api_call('/api/tool/refresh', 'GET', token=self.token, server_url=self.server_url)
        if 'error' in resp:
            tk.Label(page, text=f"Loi: {resp['error']}", fg=COLORS['error'], bg=COLORS['bg']).pack()
            return

        stats = [
            ("So du vi", f"{resp.get('balance', 0):,}d", COLORS['accent']),
            ("Danh gia con lai", str(resp.get('reviews_remaining', 0)), COLORS['success']),
            ("Tong da danh gia", str(resp.get('total_reviews', 0)), COLORS['warning']),
            ("Gia / danh gia", f"{resp.get('review_price', 12000):,}d", COLORS['dim']),
        ]

        grid = tk.Frame(page, bg=COLORS['bg'])
        grid.pack(fill=tk.X, pady=(0, 16))

        for i, (label, value, color) in enumerate(stats):
            card = tk.Frame(grid, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky='nsew')
            grid.columnconfigure(i % 2, weight=1)

            inner = tk.Frame(card, bg=COLORS['bg2'], padx=16, pady=16)
            inner.pack(fill=tk.BOTH, expand=True)
            tk.Label(inner, text=label, font=self.fonts['small'], fg=COLORS['dim'],
                     bg=COLORS['bg2']).pack(anchor=tk.W)
            tk.Label(inner, text=value, font=self.fonts['stat_sm'], fg=color,
                     bg=COLORS['bg2']).pack(anchor=tk.W, pady=(4, 0))

        hist_resp = api_call('/api/tool/history', 'GET', token=self.token, server_url=self.server_url)
        if 'error' not in hist_resp:
            reviews = hist_resp.get('reviews', [])
            if reviews:
                sec = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
                sec.pack(fill=tk.BOTH, expand=True)
                sec_inner = tk.Frame(sec, bg=COLORS['bg2'], padx=14, pady=10)
                sec_inner.pack(fill=tk.BOTH, expand=True)

                tk.Label(sec_inner, text="Danh gia gan day", font=self.fonts['heading'],
                         fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 6))

                for r in reviews[:10]:
                    row = tk.Frame(sec_inner, bg=COLORS['bg3'], padx=10, pady=6)
                    row.pack(fill=tk.X, pady=2)
                    tk.Label(row, text=r.get('created_at', '')[:16], font=self.fonts['tiny'],
                             fg=COLORS['dim'], bg=COLORS['bg3'], width=16, anchor=tk.W).pack(side=tk.LEFT)
                    tk.Label(row, text=r.get('place_url', '')[:40], font=self.fonts['small'],
                             fg=COLORS['fg'], bg=COLORS['bg3'], anchor=tk.W).pack(side=tk.LEFT, padx=8)
                    tk.Label(row, text=f"{'⭐'*r.get('stars',5)} {r.get('cost',0):,}d",
                             font=self.fonts['small'], fg=COLORS['accent'], bg=COLORS['bg3']).pack(side=tk.RIGHT)


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewBotApp(root)
    root.mainloop()
