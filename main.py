"""
Google Maps Review Bot - Desktop App
Login + Sidebar + API integration + Google Accounts Management
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

VERSION = "4.0.0"
CONFIG_FILE = "tool_config.json"
PROFILES_DIR = os.path.join(os.getcwd(), "profiles")

SERVER_URL = "https://phamhuudungmedia.vn"

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


def email_to_profile_name(email):
    return email.replace('@', '_at_').replace('.', '_')


class ReviewBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Google Maps Review Bot v{VERSION}")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)
        self.root.configure(bg=COLORS['bg'])
        icon_path = os.path.join(os.getcwd(), "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self._setup_fonts()

        self.token = None
        self.user_info = None
        self.bots = []
        self.is_running = False
        self._stop_event = threading.Event()
        self.current_page = 'home'
        self.server_url = SERVER_URL

        self.google_accounts = []
        self.google_accounts_status = {}
        self.review_count = 0
        self._is_reviewing = False

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
                self.google_accounts = cfg.get('google_accounts', [])
                self.google_accounts_status = cfg.get('google_accounts_status', {})
                self.review_count = cfg.get('review_count', 0)
        except:
            pass
        self._check_all_profile_sessions()

    def _save_config(self):
        try:
            data = {
                'server_url': self.server_url,
                'token': self.token,
                'google_accounts': self.google_accounts,
                'google_accounts_status': self.google_accounts_status,
                'review_count': self.review_count,
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _async_api_call(self, endpoint, method='GET', data=None, on_done=None):
        """Chay api_call() o thread nen, roi goi on_done(resp) tren main thread qua root.after()."""
        def worker():
            resp = api_call(endpoint, method, data, token=self.token, server_url=self.server_url)
            if on_done:
                try:
                    self.root.after(0, lambda: on_done(resp))
                except RuntimeError:
                    pass  # window da bi dong
        threading.Thread(target=worker, daemon=True).start()

    def _check_profile_session(self, email):
        profile_name = email_to_profile_name(email)
        profile_path = os.path.join(PROFILES_DIR, profile_name)
        if not os.path.exists(profile_path):
            return False
        cookies_file = os.path.join(profile_path, "Default", "Cookies")
        if os.path.exists(cookies_file):
            try:
                if os.path.getsize(cookies_file) > 100:
                    return True
            except:
                pass
        return False

    def _check_all_profile_sessions(self):
        for acc in self.google_accounts:
            email = acc.get('email', '')
            if email:
                self.google_accounts_status[email] = self._check_profile_session(email)

    def _get_profile_status_text(self, email):
        if self.google_accounts_status.get(email, False):
            return "Da dang nhap", COLORS['success']
        return "Chua dang nhap", COLORS['dim']

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

        self.login_btn = tk.Button(form, text="DANG NHAP", command=self._do_login,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                  relief=tk.FLAT, cursor="hand2", width=30)
        self.login_btn.pack(ipady=4)

        tk.Label(form, text="Chua co tai khoan? Dang ky tai web admin",
                 font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['bg']).pack(pady=(12, 0))

        self.login_pass.bind('<Return>', lambda e: self._do_login())
        self.login_user.focus_set()

    def _do_login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get().strip()

        if not username or not password:
            self.login_status.config(text="Nhap day du thong tin!")
            return

        self.server_url = SERVER_URL
        self.login_status.config(text="Dang ket noi...", fg=COLORS['warning'])
        self.login_btn.config(state=tk.DISABLED)

        def on_done(resp):
            if not hasattr(self, 'login_btn') or not self.login_btn.winfo_exists():
                return  # man hinh login da bi thay the (VD: dong app)
            self.login_btn.config(state=tk.NORMAL)

            if 'error' in resp:
                self.login_status.config(text=resp['error'], fg=COLORS['error'])
                return

            self.token = resp.get('token')
            self.user_info = resp.get('user')
            self._save_config()
            self._show_main_ui()

        self._async_api_call('/api/tool/login', 'POST',
                              {'username': username, 'password': password}, on_done=on_done)

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
            ('home', '🏠  Danh gia'),
            ('google_accounts', '📧  Tai khoan GG'),
            ('history', '📋  Lich su'),
            ('deposit', '💰  Nap xu'),
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

        self.sidebar_stats = tk.Label(sidebar, text="", font=self.fonts['small'],
                                       fg=COLORS['accent'], bg=COLORS['sidebar'], anchor=tk.W, padx=16)
        self.sidebar_stats.pack(fill=tk.X)

        bottom = tk.Frame(sidebar, bg=COLORS['sidebar'])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=12)
        tk.Label(bottom, text="Dang xuat", font=self.fonts['tiny'],
                 fg=COLORS['error'], bg=COLORS['sidebar'], cursor="hand2"
                 ).pack(anchor=tk.W)
        bottom.winfo_children()[-1].bind('<Button-1>', lambda e: self._logout())

        self.main_area = tk.Frame(self.root, bg=COLORS['bg'])
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._update_sidebar_stats()
        self._navigate('home')

    def _update_sidebar_stats(self):
        acc_count = len(self.google_accounts)
        logged_in = sum(1 for v in self.google_accounts_status.values() if v)
        xu = (self.user_info or {}).get('xu', 0)
        self.sidebar_stats.config(
            text=f"Xu: {xu:,} \U0001FA99\nGG accounts: {acc_count} ({logged_in} active)\nDa danh gia: {self.review_count}")

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
        elif page == 'google_accounts':
            self._build_google_accounts_page()
        elif page == 'history':
            self._build_history_page()
        elif page == 'deposit':
            self._build_deposit_page()
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
        tk.Label(page, text=f"Da danh gia: {self.review_count} | Tai khoan GG: {len(self.google_accounts)}",
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

        tk.Label(row_opt, text="  So luong:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT, padx=(12, 0))
        self.target_count = tk.IntVar(value=5)
        tk.Spinbox(row_opt, from_=1, to=500, textvariable=self.target_count, width=5,
                   bg=COLORS['bg3'], fg=COLORS['fg'], font=self.fonts['body'],
                   buttonbackground=COLORS['bg4'], relief=tk.FLAT).pack(side=tk.LEFT, padx=4)

        sec_accounts = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec_accounts.pack(fill=tk.X, pady=(0, 10))
        inner_acc = tk.Frame(sec_accounts, bg=COLORS['bg2'], padx=14, pady=10)
        inner_acc.pack(fill=tk.X)

        acc_header = tk.Frame(inner_acc, bg=COLORS['bg2'])
        acc_header.pack(fill=tk.X)
        tk.Label(acc_header, text="Tai khoan Google:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(side=tk.LEFT)

        count_text = f"({len(self.google_accounts)} tai khoan)"
        self.acc_count_label = tk.Label(acc_header, text=count_text, font=self.fonts['small'],
                                         fg=COLORS['accent'], bg=COLORS['bg2'])
        self.acc_count_label.pack(side=tk.LEFT, padx=(6, 0))

        add_acc_row = tk.Frame(inner_acc, bg=COLORS['bg2'])
        add_acc_row.pack(fill=tk.X, pady=(8, 4))

        tk.Label(add_acc_row, text="Email:", font=self.fonts['tiny'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.quick_email = tk.Entry(add_acc_row, bg=COLORS['bg3'], fg=COLORS['fg'],
                                    insertbackground=COLORS['fg'], font=self.fonts['small'],
                                    relief=tk.FLAT, width=24)
        self.quick_email.pack(side=tk.LEFT, padx=(4, 8), ipady=3)

        tk.Label(add_acc_row, text="MK:", font=self.fonts['tiny'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.quick_pass = tk.Entry(add_acc_row, bg=COLORS['bg3'], fg=COLORS['fg'],
                                   insertbackground=COLORS['fg'], font=self.fonts['small'],
                                   relief=tk.FLAT, width=18, show='*')
        self.quick_pass.pack(side=tk.LEFT, padx=(4, 8), ipady=3)

        tk.Button(add_acc_row, text="+ Them", command=self._quick_add_account,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['tiny'],
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(0, 4))

        self.account_list_frame = tk.Frame(inner_acc, bg=COLORS['bg2'])
        self.account_list_frame.pack(fill=tk.X, pady=(4, 0))
        self._refresh_home_account_list()

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

        save_btn_row = tk.Frame(page, bg=COLORS['bg'])
        save_btn_row.pack(fill=tk.X, pady=(0, 8))

        tk.Button(save_btn_row, text="💾  Luu cau hinh", command=self._save_home_config,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(save_btn_row, text="📂  Tai cau hinh", command=self._load_home_config,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

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
        self._log("San sang! Nhap thong tin va bat dau danh gia.")

    def _refresh_home_account_list(self):
        for w in self.account_list_frame.winfo_children():
            w.destroy()

        if not self.google_accounts:
            tk.Label(self.account_list_frame, text="Chua co tai khoan nao. Them o tren hoac vao trang 'Tai khoan GG'.",
                     font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['bg2']).pack(anchor=tk.W)
            return

        for i, acc in enumerate(self.google_accounts):
            row = tk.Frame(self.account_list_frame, bg=COLORS['bg3'], padx=6, pady=3)
            row.pack(fill=tk.X, pady=1)

            email = acc.get('email', '')
            logged_in, color = self._get_profile_status_text(email)
            status_char = "●" if self.google_accounts_status.get(email, False) else "○"

            tk.Label(row, text=f"{status_char}", font=self.fonts['small'], fg=color,
                     bg=COLORS['bg3'], width=2).pack(side=tk.LEFT)
            tk.Label(row, text=email, font=self.fonts['small'], fg=COLORS['fg'],
                     bg=COLORS['bg3'], anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(row, text=logged_in, font=self.fonts['tiny'], fg=color,
                     bg=COLORS['bg3']).pack(side=tk.LEFT, padx=(0, 8))

            del_btn = tk.Label(row, text="[Xoa]", font=self.fonts['tiny'], fg=COLORS['error'],
                               bg=COLORS['bg3'], cursor="hand2")
            del_btn.pack(side=tk.RIGHT)
            del_btn.bind('<Button-1>', lambda e, idx=i: self._remove_account(idx))

        if self.acc_count_label:
            self.acc_count_label.config(text=f"({len(self.google_accounts)} tai khoan)")

    def _quick_add_account(self):
        email = self.quick_email.get().strip()
        password = self.quick_pass.get().strip()
        if not email or not password:
            messagebox.showwarning("Canh bao", "Nhap day du email va mat khau!")
            return

        for acc in self.google_accounts:
            if acc.get('email', '').lower() == email.lower():
                messagebox.showwarning("Canh bao", "Tai khoan nay da ton tai!")
                return

        self.google_accounts.append({'email': email, 'password': password})
        self.google_accounts_status[email] = self._check_profile_session(email)
        self._save_config()
        self._refresh_home_account_list()
        self.quick_email.delete(0, tk.END)
        self.quick_pass.delete(0, tk.END)
        self._log(f"Da them tai khoan: {email}")

    def _remove_account(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            if messagebox.askyesno("Xac nhan", f"Xoa tai khoan {email}?"):
                self.google_accounts.pop(index)
                self.google_accounts_status.pop(email, None)
                self._save_config()
                self._refresh_home_account_list()
                self._log(f"Da xoa tai khoan: {email}")

    def _save_home_config(self):
        try:
            data = {
                'google_accounts': self.google_accounts,
                'google_accounts_status': self.google_accounts_status,
                'last_url': self.url_entry.get().strip() if hasattr(self, 'url_entry') else '',
                'last_stars': self.star_var.get() if hasattr(self, 'star_var') else 5,
                'last_chrome_count': self.chrome_count.get() if hasattr(self, 'chrome_count') else 1,
                'last_target_count': self.target_count.get() if hasattr(self, 'target_count') else 5,
                'last_comments': self.comment_text.get('1.0', tk.END).strip() if hasattr(self, 'comment_text') else '',
                'review_count': self.review_count,
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._log("Da luu cau hinh!")
            messagebox.showinfo("Thanh cong", "Da luu cau hinh!")
        except Exception as e:
            self._log(f"Loi luu cau hinh: {e}", True)
            messagebox.showerror("Loi", f"Khong the luu: {e}")

    def _load_home_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    cfg = json.load(f)
                self.google_accounts = cfg.get('google_accounts', [])
                self.review_count = cfg.get('review_count', 0)
                self._check_all_profile_sessions()

                if hasattr(self, 'url_entry'):
                    self.url_entry.delete(0, tk.END)
                    self.url_entry.insert(0, cfg.get('last_url', ''))
                if hasattr(self, 'star_var'):
                    self.star_var.set(cfg.get('last_stars', 5))
                if hasattr(self, 'chrome_count'):
                    self.chrome_count.set(cfg.get('last_chrome_count', 1))
                if hasattr(self, 'target_count'):
                    self.target_count.set(cfg.get('last_target_count', 5))
                if hasattr(self, 'comment_text'):
                    self.comment_text.delete('1.0', tk.END)
                    self.comment_text.insert('1.0', cfg.get('last_comments', ''))

                self._refresh_home_account_list()
                self._log("Da tai cau hinh!")
                messagebox.showinfo("Thanh cong", "Da tai cau hinh!")
            else:
                messagebox.showwarning("Canh bao", "Khong tim thay file cau hinh!")
        except Exception as e:
            self._log(f"Loi tai cau hinh: {e}", True)
            messagebox.showerror("Loi", f"Khong the tai: {e}")

    def _update_comment_hint(self, event=None):
        raw = self.comment_text.get('1.0', tk.END).strip()
        lines = [l for l in raw.split('\n') if l.strip()] if raw else []
        self.comment_hint.config(text=f"{len(lines)} noi dung | Moi tai khoan lay 1 noi dung ngau nhien")

    def _log(self, msg, is_error=False):
        def _do():
            tag = "[ERR] " if is_error else ""
            self.log_text.insert(tk.END, f"{tag}{msg}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _do)

    def _start_review(self):
        url = self.url_entry.get().strip()
        raw = self.comment_text.get('1.0', tk.END).strip()
        comment_lines = [l.strip() for l in raw.split('\n') if l.strip()] if raw else []
        target = self.target_count.get()
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

        if not self.google_accounts:
            messagebox.showerror("Loi", "Nhap it nhat 1 tai khoan Google!\nVao trang 'Tai khoan GG' de them.")
            return

        actual = min(target, len(self.google_accounts))
        actual_chrome = min(chrome_count, actual)
        if actual <= 0:
            messagebox.showerror("Loi", "Khong du tai khoan de danh gia!")
            return

        if not messagebox.askyesno("Xac nhan",
                f"Muc tieu: {target} danh gia\n"
                f"Tai khoan: {len(self.google_accounts)}\n"
                f"Se chay: {actual} danh gia\n"
                f"Chrome cung luc: {actual_chrome}\n\n"
                f"Bat dau?"):
            return

        self.log_text.delete('1.0', tk.END)
        self._log(f"BAT DAU: muc tieu {target} | {len(self.google_accounts)} tai khoan")
        self._log(f"Se chay {actual} danh gia | {actual_chrome} Chrome song song")
        self._stop_event.clear()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._is_reviewing = True

        thread = threading.Thread(target=self._run_review,
                                  args=(url, comment_lines, stars, target, chrome_count))
        thread.daemon = True
        thread.start()

    def _run_review(self, url, comment_lines, stars, target, chrome_count):
        import queue

        session_reviewed = 0
        session_failed = 0
        lock = threading.Lock()

        shuffled_comments = comment_lines[:]
        random.shuffle(shuffled_comments)
        shuffled_accounts = self.google_accounts[:]
        random.shuffle(shuffled_accounts)

        actual = min(target, len(shuffled_accounts))
        actual_chrome = min(chrome_count, actual)

        work_queue = queue.Queue()
        for i in range(actual):
            account = shuffled_accounts[i]
            comment = shuffled_comments[i % len(shuffled_comments)]
            work_queue.put((i, account, comment))

        def worker(worker_id):
            nonlocal session_reviewed, session_failed
            while not work_queue.empty() and not self._stop_event.is_set():
                try:
                    idx, account, comment = work_queue.get_nowait()
                except queue.Empty:
                    break

                email = account.get('email', '')
                password = account.get('password', '')
                profile_name = email_to_profile_name(email)
                profile_dir = os.path.join(PROFILES_DIR, profile_name)
                os.makedirs(profile_dir, exist_ok=True)
                already_logged = self.google_accounts_status.get(email, False)

                with lock:
                    total_done = session_reviewed + session_failed
                    self._log(f"\n--- [{total_done+1}/{actual}] Chrome-{worker_id} ---")
                    self._log(f"  TK: {email}")
                    if already_logged:
                        self._log(f"  [Session cu]")
                    else:
                        self._log(f"  [Dang nhap moi]")
                    self._log(f"  Noi dung: {comment[:60]}...")

                bot = None
                try:
                    bot = GoogleMapsReviewBot(
                        headless=False,
                        user_data_dir=profile_dir,
                        debug_port=9222 + worker_id * 100 + idx
                    )
                    bot.set_status_callback(self._log)
                    self.bots.append(bot)

                    if not bot.start_browser():
                        self._log("Loi Chrome! Bo qua.", True)
                        with lock:
                            session_failed += 1
                        continue

                    if not already_logged:
                        if not bot.login_google(email, password):
                            self._log("Loi dang nhap! Bo qua.", True)
                            with lock:
                                session_failed += 1
                            continue
                        self.google_accounts_status[email] = True
                        self._save_config()
                    else:
                        self._log(f"  Kiem tra session...")
                        if not bot.login_google(email, password):
                            self._log(f"  Session het han, dang nhap lai...")
                            if not bot.login_google(email, password):
                                self._log("Loi dang nhap!", True)
                                self.google_accounts_status[email] = False
                                with lock:
                                    session_failed += 1
                                continue
                            self.google_accounts_status[email] = True
                            self._save_config()
                        else:
                            self._log(f"  Session hop le!")

                    if not bot.navigate_to_place(url):
                        self._log("Loi dia diem! Bo qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.click_write_review_button():
                        self._log("Loi nut review! Bo qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.select_star_rating(stars):
                        self._log("Loi chon sao! Bo qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.write_comment(comment):
                        self._log("Loi viet binh luan! Bo qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.submit_review():
                        self._log("Loi gui danh gia! Bo qua.", True)
                        with lock:
                            session_failed += 1
                        continue

                    with lock:
                        session_reviewed += 1
                        self.review_count += 1
                        self._save_config()
                    api_call('/api/tool/review-done', 'POST',
                             {'place_url': url, 'comment': comment, 'stars': stars},
                             token=self.token, server_url=self.server_url)
                    with lock:
                        self._log(f"  THANH CONG! [{session_reviewed}/{actual}] | Tool: {self.review_count}")

                except Exception as e:
                    self._log(f"  Loi: {e}", True)
                    with lock:
                        session_failed += 1
                finally:
                    if bot:
                        try:
                            bot.close_browser()
                        except:
                            pass
                    work_queue.task_done()

        threads = []
        for i in range(actual_chrome):
            t = threading.Thread(target=worker, args=(i,), daemon=True)
            t.start()
            threads.append(t)
            time.sleep(2)

        for t in threads:
            t.join()

        self._log("\n" + "=" * 40)
        if session_reviewed >= target:
            self._log(f"DAT MUC TIEU! {session_reviewed}/{target}")
        elif session_reviewed + session_failed >= actual:
            self._log(f"HET TAI KHOAN! {session_reviewed} thanh cong, {session_failed} that bai / {target}")
        else:
            self._log(f"DUNG! {session_reviewed}/{target}")
        self._log(f"Tong tool: {self.review_count} danh gia")

        self._is_reviewing = False
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

    # ==================== GOOGLE ACCOUNTS PAGE ====================

    def _build_google_accounts_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        header_row = tk.Frame(page, bg=COLORS['bg'])
        header_row.pack(fill=tk.X, pady=(0, 12))
        tk.Label(header_row, text="Quan ly tai khoan Google", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(side=tk.LEFT)
        tk.Button(header_row, text="🔄  Kiem tra lai session", command=self._refresh_all_sessions,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        add_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        add_frame.pack(fill=tk.X, pady=(0, 12))
        add_inner = tk.Frame(add_frame, bg=COLORS['bg2'], padx=14, pady=12)
        add_inner.pack(fill=tk.X)

        tk.Label(add_inner, text="Them tai khoan moi", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2']).pack(anchor=tk.W, pady=(0, 8))

        row1 = tk.Frame(add_inner, bg=COLORS['bg2'])
        row1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(row1, text="Email:", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg2'], width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.ga_email = tk.Entry(row1, bg=COLORS['bg3'], fg=COLORS['fg'],
                                 insertbackground=COLORS['fg'], font=self.fonts['body'],
                                 relief=tk.FLAT, width=35)
        self.ga_email.pack(side=tk.LEFT, padx=(0, 16), ipady=4)

        tk.Label(row1, text="Mat khau:", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg2'], width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.ga_pass = tk.Entry(row1, bg=COLORS['bg3'], fg=COLORS['fg'],
                                insertbackground=COLORS['fg'], font=self.fonts['body'],
                                relief=tk.FLAT, width=25, show='*')
        self.ga_pass.pack(side=tk.LEFT, padx=(0, 16), ipady=4)

        tk.Button(row1, text="Them tai khoan", command=self._add_google_account,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(row1, text="Them nhieu (file)", command=self._import_accounts_file,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=8, cursor="hand2").pack(side=tk.LEFT)

        self.ga_status = tk.Label(add_inner, text="", font=self.fonts['small'],
                                  fg=COLORS['dim'], bg=COLORS['bg2'])
        self.ga_status.pack(anchor=tk.W)

        list_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_inner = tk.Frame(list_frame, bg=COLORS['bg2'], padx=14, pady=10)
        list_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(list_inner, text=f"Danh sach tai khoan ({len(self.google_accounts)})", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 8))

        cols_frame = tk.Frame(list_inner, bg=COLORS['bg4'], padx=10, pady=6)
        cols_frame.pack(fill=tk.X)
        tk.Label(cols_frame, text="#", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=4, anchor=tk.W).pack(side=tk.LEFT)
        tk.Label(cols_frame, text="Email", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=30, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cols_frame, text="Trang thai", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cols_frame, text="Profile", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=20, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cols_frame, text="Thao tac", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=10, anchor=tk.W).pack(side=tk.LEFT)

        self.ga_list_canvas = tk.Canvas(list_inner, bg=COLORS['bg2'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_inner, orient=tk.VERTICAL, command=self.ga_list_canvas.yview)
        self.ga_list_inner = tk.Frame(self.ga_list_canvas, bg=COLORS['bg2'])
        self.ga_list_inner.bind('<Configure>', lambda e: self.ga_list_canvas.configure(scrollregion=self.ga_list_canvas.bbox("all")))
        self.ga_list_canvas.create_window((0, 0), window=self.ga_list_inner, anchor=tk.NW)
        self.ga_list_canvas.configure(yscrollcommand=scrollbar.set)

        self.ga_list_canvas.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_google_accounts_list()

    def _refresh_google_accounts_list(self):
        for w in self.ga_list_inner.winfo_children():
            w.destroy()

        for i, acc in enumerate(self.google_accounts):
            email = acc.get('email', '')
            logged_in, status_color = self._get_profile_status_text(email)
            profile_name = email_to_profile_name(email)
            profile_exists = os.path.exists(os.path.join(PROFILES_DIR, profile_name))

            row_bg = COLORS['bg3'] if i % 2 == 0 else COLORS['bg2']
            row = tk.Frame(self.ga_list_inner, bg=row_bg, padx=10, pady=5)
            row.pack(fill=tk.X, pady=1)

            tk.Label(row, text=str(i + 1), font=self.fonts['small'], fg=COLORS['dim'],
                     bg=row_bg, width=4, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=email, font=self.fonts['small'], fg=COLORS['fg'],
                     bg=row_bg, width=30, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))

            status_frame = tk.Frame(row, bg=row_bg)
            status_frame.pack(side=tk.LEFT, padx=(0, 8))
            dot_color = COLORS['success'] if self.google_accounts_status.get(email, False) else COLORS['dim']
            tk.Label(status_frame, text="●", font=self.fonts['body'], fg=dot_color,
                     bg=row_bg).pack(side=tk.LEFT)
            tk.Label(status_frame, text=logged_in, font=self.fonts['tiny'], fg=status_color,
                     bg=row_bg).pack(side=tk.LEFT, padx=(4, 0))

            prof_text = profile_name[:20] + "..." if len(profile_name) > 20 else profile_name
            tk.Label(row, text=prof_text, font=self.fonts['tiny'], fg=COLORS['dim'],
                     bg=row_bg, width=20, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))

            btn_frame = tk.Frame(row, bg=row_bg)
            btn_frame.pack(side=tk.LEFT)

            if profile_exists:
                del_prof = tk.Label(btn_frame, text="[Xoa profile]", font=self.fonts['tiny'],
                                    fg=COLORS['warning'], bg=row_bg, cursor="hand2")
                del_prof.pack(side=tk.LEFT, padx=(0, 6))
                del_prof.bind('<Button-1>', lambda e, idx=i: self._delete_profile(idx))

            del_acc = tk.Label(btn_frame, text="[Xoa]", font=self.fonts['tiny'],
                               fg=COLORS['error'], bg=row_bg, cursor="hand2")
            del_acc.pack(side=tk.LEFT)
            del_acc.bind('<Button-1>', lambda e, idx=i: self._remove_google_account(idx))

    def _add_google_account(self):
        email = self.ga_email.get().strip()
        password = self.ga_pass.get().strip()
        if not email or not password:
            self.ga_status.config(text="Nhap day du email va mat khau!", fg=COLORS['error'])
            return

        for acc in self.google_accounts:
            if acc.get('email', '').lower() == email.lower():
                self.ga_status.config(text="Tai khoan nay da ton tai!", fg=COLORS['warning'])
                return

        self.google_accounts.append({'email': email, 'password': password})
        self.google_accounts_status[email] = self._check_profile_session(email)
        self._save_config()
        self._refresh_google_accounts_list()
        self.ga_email.delete(0, tk.END)
        self.ga_pass.delete(0, tk.END)
        self.ga_status.config(text=f"Da them: {email}", fg=COLORS['success'])

    def _remove_google_account(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            if messagebox.askyesno("Xac nhan", f"Xoa tai khoan {email}?"):
                self.google_accounts.pop(index)
                self.google_accounts_status.pop(email, None)
                self._save_config()
                self._refresh_google_accounts_list()
                self.ga_status.config(text=f"Da xoa: {email}", fg=COLORS['success'])

    def _delete_profile(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            profile_name = email_to_profile_name(email)
            profile_path = os.path.join(PROFILES_DIR, profile_name)
            if messagebox.askyesno("Xac nhan", f"Xoa Chrome profile cua {email}?\nLan tiep se phai dang nhap lai."):
                try:
                    import shutil
                    shutil.rmtree(profile_path, ignore_errors=True)
                    self.google_accounts_status[email] = False
                    self._save_config()
                    self._refresh_google_accounts_list()
                    self.ga_status.config(text=f"Da xoa profile: {email}", fg=COLORS['success'])
                except Exception as e:
                    self.ga_status.config(text=f"Loi xoa profile: {e}", fg=COLORS['error'])

    def _refresh_all_sessions(self):
        self.ga_status.config(text="Dang kiem tra...", fg=COLORS['warning'])
        self.root.update()
        self._check_all_profile_sessions()
        self._save_config()
        self._refresh_google_accounts_list()
        count = sum(1 for v in self.google_accounts_status.values() if v)
        self.ga_status.config(text=f"Kiem tra xong: {count}/{len(self.google_accounts)} da dang nhap",
                              fg=COLORS['success'])

    def _import_accounts_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Chon file danh sach tai khoan"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            added = 0
            skipped = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' not in line:
                    continue
                parts = line.split(':', 1)
                email = parts[0].strip()
                password = parts[1].strip()
                if not email or not password:
                    continue
                exists = False
                for acc in self.google_accounts:
                    if acc.get('email', '').lower() == email.lower():
                        exists = True
                        break
                if exists:
                    skipped += 1
                    continue
                self.google_accounts.append({'email': email, 'password': password})
                self.google_accounts_status[email] = self._check_profile_session(email)
                added += 1

            self._save_config()
            self._refresh_google_accounts_list()
            self.ga_status.config(text=f"Nhap thanh cong: {added} moi, {skipped} da co",
                                  fg=COLORS['success'])
        except Exception as e:
            self.ga_status.config(text=f"Loi doc file: {e}", fg=COLORS['error'])

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

        sec = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        sec_inner = tk.Frame(sec, bg=COLORS['bg2'], padx=10, pady=10)
        sec_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(sec_inner, text=f"Danh gia gan day ({len(reviews)} phan tu)",
                 font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 6))

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Hist.Treeview", background=COLORS['bg3'], foreground=COLORS['fg'],
                        fieldbackground=COLORS['bg3'], font=self.fonts['small'], rowheight=24)
        style.configure("Hist.Treeview.Heading", background=COLORS['bg4'], foreground=COLORS['fg'],
                        font=self.fonts['small'])

        cols = ("time", "url", "stars", "status")
        tree = ttk.Treeview(sec_inner, columns=cols, show="headings", style="Hist.Treeview", height=12)
        tree.heading("time", text="Thoi gian")
        tree.heading("url", text="Dia diem")
        tree.heading("stars", text="Sao")
        tree.heading("status", text="Trang thai")
        tree.column("time", width=140)
        tree.column("url", width=400)
        tree.column("stars", width=60)
        tree.column("status", width=80)

        for r in reviews:
            tree.insert("", tk.END, values=(
                r.get('created_at', ''),
                r.get('place_url', '')[:60],
                '⭐' * r.get('stars', 5),
                r.get('status', '')
            ))

        tree.pack(fill=tk.BOTH, expand=True)

        if not reviews:
            tk.Label(sec_inner, text="Chua co danh gia nao", font=self.fonts['small'],
                     fg=COLORS['dim'], bg=COLORS['bg2']).pack(pady=20)

    # ==================== NAP XU PAGE ====================

    def _build_deposit_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Nap tien -> Xu", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W)
        tk.Label(page, text="Ty le: 1.000d = 1 xu. Xu duoc cong tu dong sau khi SePay xac nhan chuyen khoan.",
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(2, 12))

        self.deposit_xu_label = tk.Label(page, text="So xu hien co: ...", font=self.fonts['body'],
                                          fg=COLORS['accent'], bg=COLORS['bg'])
        self.deposit_xu_label.pack(anchor=tk.W, pady=(0, 10))

        def on_profile(resp):
            if self.current_page != 'deposit' or not self.deposit_xu_label.winfo_exists():
                return
            if 'error' not in resp:
                self.deposit_xu_label.config(text=f"So xu hien co: {resp.get('xu', 0):,} \U0001FA99")
                self.user_info = self.user_info or {}
                self.user_info['xu'] = resp.get('xu', 0)
                self._update_sidebar_stats()

        self._async_api_call('/api/tool/profile', 'GET', on_done=on_profile)

        form_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        form_frame.pack(fill=tk.X, pady=(0, 12))
        form_inner = tk.Frame(form_frame, bg=COLORS['bg2'], padx=14, pady=10)
        form_inner.pack(fill=tk.X)

        row = tk.Frame(form_inner, bg=COLORS['bg2'])
        row.pack(fill=tk.X)
        tk.Label(row, text="So tien (d):", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.deposit_amount_entry = tk.Entry(row, bg=COLORS['bg3'], fg=COLORS['fg'],
                                              insertbackground=COLORS['fg'], font=self.fonts['body'],
                                              relief=tk.FLAT, width=16)
        self.deposit_amount_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self.deposit_amount_entry.insert(0, "50000")

        self.deposit_btn = tk.Button(row, text="Tao giao dich nap", command=self._start_deposit,
                                      bg=COLORS['accent'], fg='#000', font=self.fonts['small'],
                                      relief=tk.FLAT, padx=12, pady=4, cursor="hand2")
        self.deposit_btn.pack(side=tk.LEFT, padx=8)

        self.deposit_status_label = tk.Label(form_inner, text="", font=self.fonts['small'],
                                              fg=COLORS['dim'], bg=COLORS['bg2'])
        self.deposit_status_label.pack(anchor=tk.W, pady=(8, 0))

        self.deposit_result_frame = tk.Frame(page, bg=COLORS['bg2'],
                                              highlightbackground=COLORS['border'], highlightthickness=1)
        self.deposit_result_frame.pack(fill=tk.BOTH, expand=True)

    def _start_deposit(self):
        try:
            amount = int(self.deposit_amount_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Canh bao", "So tien khong hop le!")
            return
        if amount < 10000:
            messagebox.showwarning("Canh bao", "So tien toi thieu 10.000d!")
            return

        self.deposit_btn.config(state=tk.DISABLED)
        self.deposit_status_label.config(text="Dang tao giao dich...", fg=COLORS['warning'])

        def on_done(resp):
            if not hasattr(self, 'deposit_btn') or not self.deposit_btn.winfo_exists():
                return
            self.deposit_btn.config(state=tk.NORMAL)
            if 'error' in resp:
                self.deposit_status_label.config(text=resp['error'], fg=COLORS['error'])
                return
            self.deposit_status_label.config(text="Da tao giao dich, xem thong tin ben duoi:", fg=COLORS['dim'])
            self._show_deposit_result(resp)

        self._async_api_call('/api/tool/deposit/create', 'POST', {'amount': amount}, on_done=on_done)

    def _show_deposit_result(self, resp):
        for w in self.deposit_result_frame.winfo_children():
            w.destroy()

        inner = tk.Frame(self.deposit_result_frame, bg=COLORS['bg2'], padx=16, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(inner, bg=COLORS['bg2'])
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        self.deposit_qr_label = tk.Label(left, bg=COLORS['bg2'], text="Dang tai QR...",
                                          fg=COLORS['dim'], font=self.fonts['small'])
        self.deposit_qr_label.pack()

        right = tk.Frame(inner, bg=COLORS['bg2'])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        info_lines = [
            ("Ngan hang", resp.get('bank_code', '-')),
            ("So tai khoan", resp.get('bank_account', '-')),
            ("Chu tai khoan", resp.get('account_name', '-')),
            ("So tien", f"{resp.get('amount', 0):,}d ({resp.get('xu', 0):,} xu)"),
            ("Noi dung CK", resp.get('code', '-')),
        ]
        for label, value in info_lines:
            r = tk.Frame(right, bg=COLORS['bg2'])
            r.pack(fill=tk.X, pady=3)
            tk.Label(r, text=f"{label}:", font=self.fonts['small'], fg=COLORS['dim'],
                     bg=COLORS['bg2'], width=14, anchor=tk.W).pack(side=tk.LEFT)
            color = COLORS['accent'] if label == "Noi dung CK" else COLORS['fg']
            tk.Label(r, text=value, font=self.fonts['body'], fg=color,
                     bg=COLORS['bg2'], anchor=tk.W).pack(side=tk.LEFT)

        tk.Label(right, text="Nhap DUNG noi dung chuyen khoan de he thong tu dong cong xu!",
                 font=self.fonts['tiny'], fg=COLORS['warning'], bg=COLORS['bg2'],
                 wraplength=340, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))

        self.deposit_wait_label = tk.Label(right, text="⏳ Dang cho thanh toan...", font=self.fonts['small'],
                                            fg=COLORS['warning'], bg=COLORS['bg2'])
        self.deposit_wait_label.pack(anchor=tk.W, pady=(10, 0))

        qr_url = resp.get('qr_url')
        if qr_url:
            def fetch_qr():
                try:
                    req = urllib.request.Request(qr_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as r:
                        img_bytes = r.read()
                    self.root.after(0, lambda: self._set_deposit_qr_image(img_bytes))
                except Exception as e:
                    err = str(e)
                    self.root.after(0, lambda: self._set_deposit_qr_error(err))
            threading.Thread(target=fetch_qr, daemon=True).start()
        else:
            self.deposit_qr_label.config(text="(Server chua cau hinh QR)")

        self._poll_deposit_status(resp['tx_id'])

    def _set_deposit_qr_image(self, img_bytes):
        if not hasattr(self, 'deposit_qr_label') or not self.deposit_qr_label.winfo_exists():
            return
        try:
            photo = tk.PhotoImage(data=img_bytes)
            self.deposit_qr_label.config(image=photo, text="")
            self.deposit_qr_label.image = photo  # giu reference tranh bi garbage collect
        except Exception as e:
            self.deposit_qr_label.config(text=f"Loi hien QR: {e}")

    def _set_deposit_qr_error(self, err):
        if hasattr(self, 'deposit_qr_label') and self.deposit_qr_label.winfo_exists():
            self.deposit_qr_label.config(text=f"Khong tai duoc QR\n({err})")

    def _poll_deposit_status(self, tx_id):
        def on_status(resp):
            if not hasattr(self, 'deposit_wait_label') or not self.deposit_wait_label.winfo_exists():
                return  # nguoi dung da roi trang, dung polling

            if 'error' in resp:
                return

            if resp.get('status') == 'completed':
                self.deposit_wait_label.config(
                    text=f"✅ Da nhan {resp.get('xu_amount', 0):,} xu!", fg=COLORS['success'])
                self._async_api_call('/api/tool/profile', 'GET', on_done=self._on_profile_refresh_after_deposit)
                return

            self.root.after(3000, lambda: self._async_api_call(
                f'/api/tool/deposit/status/{tx_id}', 'GET', on_done=on_status))

        self._async_api_call(f'/api/tool/deposit/status/{tx_id}', 'GET', on_done=on_status)

    def _on_profile_refresh_after_deposit(self, resp):
        if 'error' in resp:
            return
        self.user_info = self.user_info or {}
        self.user_info['xu'] = resp.get('xu', 0)
        self._update_sidebar_stats()
        if hasattr(self, 'deposit_xu_label') and self.deposit_xu_label.winfo_exists():
            self.deposit_xu_label.config(text=f"So xu hien co: {resp.get('xu', 0):,} \U0001FA99")

    # ==================== ACCOUNT PAGE ====================

    def _build_account_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Thong tin tai khoan", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 16))

        loading = tk.Label(page, text="Dang tai...", font=self.fonts['small'],
                            fg=COLORS['dim'], bg=COLORS['bg'])
        loading.pack(anchor=tk.W)

        def on_done(resp):
            if self.current_page != 'account' or not page.winfo_exists():
                return  # nguoi dung da chuyen trang khac trong luc cho
            loading.destroy()

            if 'error' in resp:
                tk.Label(page, text=f"Loi: {resp['error']}", fg=COLORS['error'], bg=COLORS['bg']).pack()
                return

            self.user_info = self.user_info or {}
            self.user_info['xu'] = resp.get('xu', 0)
            self._update_sidebar_stats()

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
                ("So xu", f"{resp.get('xu', 0):,} \U0001FA99"),
                ("Tong danh gia", str(resp.get('total_reviews', 0))),
                ("Da danh gia (tool)", str(self.review_count)),
            ]

            for label, value in fields:
                row = tk.Frame(info_inner, bg=COLORS['bg2'])
                row.pack(fill=tk.X, pady=3)
                tk.Label(row, text=f"{label}:", font=self.fonts['small'], fg=COLORS['dim'],
                         bg=COLORS['bg2'], width=16, anchor=tk.W).pack(side=tk.LEFT)
                tk.Label(row, text=value, font=self.fonts['body'], fg=COLORS['fg'],
                         bg=COLORS['bg2'], anchor=tk.W).pack(side=tk.LEFT)

        self._async_api_call('/api/tool/profile', 'GET', on_done=on_done)

    # ==================== STATS PAGE ====================

    def _build_stats_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Thong ke", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 16))

        loading = tk.Label(page, text="Dang tai...", font=self.fonts['small'],
                            fg=COLORS['dim'], bg=COLORS['bg'])
        loading.pack(anchor=tk.W)

        def on_refresh_done(resp):
            if self.current_page != 'stats' or not page.winfo_exists():
                return
            loading.destroy()

            if 'error' in resp:
                tk.Label(page, text=f"Loi: {resp['error']}", fg=COLORS['error'], bg=COLORS['bg']).pack()
                return

            self.user_info = self.user_info or {}
            self.user_info['xu'] = resp.get('xu', 0)
            self._update_sidebar_stats()

            stats = [
                ("So xu hien co", f"{resp.get('xu', 0):,}", COLORS['success']),
                ("Tong da danh gia (server)", str(resp.get('total_reviews', 0)), COLORS['accent']),
                ("Da danh gia (tool)", str(self.review_count), COLORS['success']),
                ("Tai khoan GG", str(len(self.google_accounts)), COLORS['warning']),
                ("Session hoat dong", str(sum(1 for v in self.google_accounts_status.values() if v)), COLORS['star']),
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

            hist_holder = tk.Frame(page, bg=COLORS['bg'])
            hist_holder.pack(fill=tk.BOTH, expand=True)

            def on_history_done(hist_resp):
                if self.current_page != 'stats' or not hist_holder.winfo_exists():
                    return
                if 'error' in hist_resp:
                    return
                reviews = hist_resp.get('reviews', [])
                if not reviews:
                    return

                sec = tk.Frame(hist_holder, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
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
                    tk.Label(row, text=f"{'⭐'*r.get('stars',5)}",
                             font=self.fonts['small'], fg=COLORS['accent'], bg=COLORS['bg3']).pack(side=tk.RIGHT)

            self._async_api_call('/api/tool/history', 'GET', on_done=on_history_done)

        self._async_api_call('/api/tool/refresh', 'GET', on_done=on_refresh_done)


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewBotApp(root)
    root.mainloop()
