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
import tempfile
from datetime import datetime
from review_bot import GoogleMapsReviewBot

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

VERSION = "3.0.0"
CONFIG_FILE = "tool_config.json"
PROFILES_DIR = os.path.join(os.getcwd(), "profiles")

SERVER_URL = "http://103.90.227.131:5000"

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
        self.sepay_api_key = ''
        self.sepay_account_id = ''
        self.deposit_polling = False
        self.deposit_tx_id = None

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
                self.sepay_api_key = cfg.get('sepay_api_key', '')
                self.sepay_account_id = cfg.get('sepay_account_id', '')
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
                'sepay_api_key': self.sepay_api_key,
                'sepay_account_id': self.sepay_account_id,
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

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
            ('google_accounts', '📧  Tai khoan GG'),
            ('nap_tien', '💰  Nap tien'),
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
        elif page == 'google_accounts':
            self._build_google_accounts_page()
        elif page == 'nap_tien':
            self._build_nap_tien_page()
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
        self.log("San sang! Nhap thong tin va bat dau danh gia.")

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
        self.log(f"Da them tai khoan: {email}")

    def _remove_account(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            if messagebox.askyesno("Xac nhan", f"Xoa tai khoan {email}?"):
                self.google_accounts.pop(index)
                self.google_accounts_status.pop(email, None)
                self._save_config()
                self._refresh_home_account_list()
                self.log(f"Da xoa tai khoan: {email}")

    def _save_home_config(self):
        try:
            data = {
                'google_accounts': self.google_accounts,
                'google_accounts_status': self.google_accounts_status,
                'last_url': self.url_entry.get().strip() if hasattr(self, 'url_entry') else '',
                'last_stars': self.star_var.get() if hasattr(self, 'star_var') else 5,
                'last_chrome_count': self.chrome_count.get() if hasattr(self, 'chrome_count') else 1,
                'last_comments': self.comment_text.get('1.0', tk.END).strip() if hasattr(self, 'comment_text') else '',
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log("Da luu cau hinh!")
            messagebox.showinfo("Thanh cong", "Da luu cau hinh!")
        except Exception as e:
            self.log(f"Loi luu cau hinh: {e}", True)
            messagebox.showerror("Loi", f"Khong the luu: {e}")

    def _load_home_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    cfg = json.load(f)
                self.google_accounts = cfg.get('google_accounts', [])
                self._check_all_profile_sessions()

                if hasattr(self, 'url_entry'):
                    self.url_entry.delete(0, tk.END)
                    self.url_entry.insert(0, cfg.get('last_url', ''))
                if hasattr(self, 'star_var'):
                    self.star_var.set(cfg.get('last_stars', 5))
                if hasattr(self, 'chrome_count'):
                    self.chrome_count.set(cfg.get('last_chrome_count', 1))
                if hasattr(self, 'comment_text'):
                    self.comment_text.delete('1.0', tk.END)
                    self.comment_text.insert('1.0', cfg.get('last_comments', ''))

                self._refresh_home_account_list()
                self.log("Da tai cau hinh!")
                messagebox.showinfo("Thanh cong", "Da tai cau hinh!")
            else:
                messagebox.showwarning("Canh bao", "Khong tim thay file cau hinh!")
        except Exception as e:
            self.log(f"Loi tai cau hinh: {e}", True)
            messagebox.showerror("Loi", f"Khong the tai: {e}")

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

        if not self.google_accounts:
            messagebox.showerror("Loi", "Nhap it nhat 1 tai khoan Google!\nVao trang 'Tai khoan GG' de them.")
            return

        self._refresh_balance()
        balance = self.user_info.get('balance', 0)
        needed = 12000
        if balance < needed:
            messagebox.showerror("Loi", f"So du khong du!\nHien tai: {balance:,}d\nCan: {needed:,}d\n\nVui long nap them tai web.")
            return

        if not messagebox.askyesno("Xac nhan", f"Chay {chrome_count} Chrome voi {len(comment_lines)} noi dung?\n{len(self.google_accounts)} tai khoan GG | So du: {balance:,}d"):
            return

        self.log_text.delete('1.0', tk.END)
        self._log(f"BAT DAU: {chrome_count} Chrome | {len(comment_lines)} noi dung | {len(self.google_accounts)} tai khoan")
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
            shuffled_comments = comment_lines[:]
            random.shuffle(shuffled_comments)
            shuffled_accounts = self.google_accounts[:]
            random.shuffle(shuffled_accounts)

            resp = api_call('/api/tool/profile', 'GET', token=self.token, server_url=self.server_url)
            if 'error' in resp:
                self._log(f"Loi kiem tra tai khoan: {resp['error']}", True)
                return

            self._log(f"Tai khoan: {resp.get('username')} | So du: {resp.get('balance'):,}d")

            for j in range(chrome_count):
                if self._stop_event.is_set():
                    break

                account = shuffled_accounts[j % len(shuffled_accounts)]
                comment = shuffled_comments[j % len(shuffled_comments)]
                email = account.get('email', '')
                password = account.get('password', '')

                profile_name = email_to_profile_name(email)
                profile_dir = os.path.join(PROFILES_DIR, profile_name)
                os.makedirs(profile_dir, exist_ok=True)

                already_logged = self.google_accounts_status.get(email, False)

                self._log(f"\n--- Chrome {j+1}/{chrome_count} ---")
                self._log(f"  TK: {email}")
                if already_logged:
                    self._log(f"  [Session cu - skip login]")
                else:
                    self._log(f"  [Dang nhap moi]")
                self._log(f"  Noi dung: {comment[:60]}...")

                def run_one(c_idx, c_comment, c_email, c_password, c_profile_dir, c_already_logged):
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
                            user_data_dir=c_profile_dir,
                            debug_port=9222 + c_idx
                        )
                        bot.set_status_callback(self._log)
                        self.bots.append(bot)

                        if not bot.start_browser():
                            self._log("Loi Chrome!", True)
                            return

                        if not c_already_logged:
                            if not bot.login_google(c_email, c_password):
                                self._log("Loi dang nhap! Bo qua tai khoan nay.", True)
                                return
                            self.google_accounts_status[c_email] = True
                            self._save_config()
                        else:
                            self._log(f"  Kiem tra session cu...")
                            if not bot.login_google(c_email, c_password):
                                self._log(f"  Session het han, dang nhap lai...")
                                if not bot.login_google(c_email, c_password):
                                    self._log("Loi dang nhap!", True)
                                    self.google_accounts_status[c_email] = False
                                    return
                                self.google_accounts_status[c_email] = True
                                self._save_config()
                            else:
                                self._log(f"  Session con hop le - skip login!")

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

                t = threading.Thread(target=run_one,
                                     args=(j, comment, email, password, profile_dir, already_logged))
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

    # ==================== NAP TIEN PAGE ====================

    def _build_nap_tien_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Nap tien", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 4))

        bal = self.user_info.get('balance', 0)
        tk.Label(page, text=f"So du hien tai: {bal:,}d  |  Con lai: {bal // 12000} danh gia",
                 font=self.fonts['small'], fg=COLORS['accent'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 12))

        top_row = tk.Frame(page, bg=COLORS['bg'])
        top_row.pack(fill=tk.X, pady=(0, 12))

        left_col = tk.Frame(top_row, bg=COLORS['bg'])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        amt_frame = tk.Frame(left_col, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        amt_frame.pack(fill=tk.X, pady=(0, 10))
        amt_inner = tk.Frame(amt_frame, bg=COLORS['bg2'], padx=14, pady=12)
        amt_inner.pack(fill=tk.X)

        tk.Label(amt_inner, text="So tien nap (VND):", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)

        preset_row = tk.Frame(amt_inner, bg=COLORS['bg2'])
        preset_row.pack(fill=tk.X, pady=(6, 4))

        self.deposit_amount = tk.StringVar(value="50000")
        for amt in ["10000", "20000", "50000", "100000", "200000", "500000"]:
            tk.Button(preset_row, text=f"{int(amt):,}d",
                      command=lambda a=amt: self.deposit_amount.set(a),
                      bg=COLORS['bg3'], fg=COLORS['fg'], font=self.fonts['tiny'],
                      relief=tk.FLAT, padx=8, pady=3, cursor="hand2").pack(side=tk.LEFT, padx=(0, 4))

        self.amt_entry = tk.Entry(amt_inner, textvariable=self.deposit_amount,
                                   bg=COLORS['bg3'], fg=COLORS['fg'],
                                   insertbackground=COLORS['fg'], font=self.fonts['body'],
                                   relief=tk.FLAT)
        self.amt_entry.pack(fill=tk.X, ipady=6, pady=(4, 8))

        btn_row = tk.Frame(amt_inner, bg=COLORS['bg2'])
        btn_row.pack(fill=tk.X)

        self.btn_deposit = tk.Button(btn_row, text="💰  Tao ma QR nap tien",
                                      command=self._create_deposit, bg=COLORS['success'], fg='#000',
                                      font=self.fonts['btn'], relief=tk.FLAT, padx=16, pady=6, cursor="hand2")
        self.btn_deposit.pack(side=tk.LEFT)

        self.deposit_status = tk.Label(amt_inner, text="", font=self.fonts['small'],
                                        fg=COLORS['dim'], bg=COLORS['bg2'])
        self.deposit_status.pack(anchor=tk.W, pady=(6, 0))

        info_frame = tk.Frame(left_col, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        info_frame.pack(fill=tk.X)
        info_inner = tk.Frame(info_frame, bg=COLORS['bg2'], padx=14, pady=10)
        info_inner.pack(fill=tk.X)

        tk.Label(info_inner, text="Huong dan:", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2']).pack(anchor=tk.W, pady=(0, 4))

        steps = [
            "1. Nhap so tien va nhan 'Tao ma QR'",
            "2. Quet ma QR de thanh toan",
            "3. Noi dung chuyen khoan phai dung: NAP<so>",
            "4. He thong se tu dong kiem tra va nap tien",
            "5. Neu Sepay chua setup, dung chuyen khoan truc tiep",
        ]
        for step in steps:
            tk.Label(info_inner, text=step, font=self.fonts['tiny'],
                     fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)

        right_col = tk.Frame(top_row, bg=COLORS['bg'])
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(12, 0))

        qr_frame = tk.Frame(right_col, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        qr_frame.pack(fill=tk.BOTH, expand=True)
        qr_inner = tk.Frame(qr_frame, bg=COLORS['bg2'], padx=14, pady=14)
        qr_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(qr_inner, text="Ma QR thanh toan", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2']).pack(anchor=tk.W, pady=(0, 8))

        self.qr_label = tk.Label(qr_inner, text="Chua tao ma QR",
                                  font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['bg2'])
        self.qr_label.pack(expand=True)

        self.deposit_info_label = tk.Label(qr_inner, text="",
                                            font=self.fonts['tiny'], fg=COLORS['fg'], bg=COLORS['bg2'],
                                            justify=tk.LEFT)
        self.deposit_info_label.pack(anchor=tk.W, pady=(8, 0))

        hist_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        hist_inner = tk.Frame(hist_frame, bg=COLORS['bg2'], padx=14, pady=10)
        hist_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(hist_inner, text="Lich su giao dich", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 6))

        resp = api_call('/api/tool/history', 'GET', token=self.token, server_url=self.server_url)
        if 'error' not in resp:
            transactions = resp.get('transactions', [])
            if transactions:
                for tx in transactions[:10]:
                    row = tk.Frame(hist_inner, bg=COLORS['bg3'], padx=10, pady=5)
                    row.pack(fill=tk.X, pady=1)
                    status = tx.get('status', '')
                    s_color = COLORS['success'] if status == 'completed' else COLORS['warning']
                    tk.Label(row, text=tx.get('created_at', '')[:16], font=self.fonts['tiny'],
                             fg=COLORS['dim'], bg=COLORS['bg3'], width=16, anchor=tk.W).pack(side=tk.LEFT)
                    tk.Label(row, text=tx.get('description', ''), font=self.fonts['small'],
                             fg=COLORS['fg'], bg=COLORS['bg3'], anchor=tk.W).pack(side=tk.LEFT, padx=8)
                    tk.Label(row, text=f"{tx.get('amount', 0):,}d", font=self.fonts['small'],
                             fg=COLORS['accent'], bg=COLORS['bg3']).pack(side=tk.RIGHT, padx=(8, 0))
                    tk.Label(row, text=status, font=self.fonts['tiny'],
                             fg=s_color, bg=COLORS['bg3'], width=10).pack(side=tk.RIGHT)
            else:
                tk.Label(hist_inner, text="Chua co giao dich nao", font=self.fonts['small'],
                         fg=COLORS['dim'], bg=COLORS['bg2']).pack(pady=10)
        else:
            tk.Label(hist_inner, text="Khong the tai lich su", font=self.fonts['small'],
                     fg=COLORS['error'], bg=COLORS['bg2']).pack(pady=10)

    def _create_deposit(self):
        try:
            amount = int(self.deposit_amount.get())
        except ValueError:
            self.deposit_status.config(text="So tien khong hop le!", fg=COLORS['error'])
            return

        if amount < 10000:
            self.deposit_status.config(text="Toi thieu 10,000d!", fg=COLORS['error'])
            return

        self.deposit_status.config(text="Dang tao giao dich...", fg=COLORS['warning'])
        self.btn_deposit.config(state=tk.DISABLED)
        self.root.update()

        resp = api_call('/api/tool/deposit', 'POST', {'amount': amount},
                        token=self.token, server_url=self.server_url)

        if 'error' in resp:
            self.deposit_status.config(text=f"Loi: {resp['error']}", fg=COLORS['error'])
            self.btn_deposit.config(state=tk.NORMAL)
            return

        tx_id = resp.get('transaction_id')
        self.deposit_tx_id = tx_id
        sepay_url = resp.get('sepay_url')
        description = resp.get('description', f'NAP{tx_id}')
        note = resp.get('note', '')

        qr_data = sepay_url if sepay_url else f"STK: {resp.get('sepay_account', 'N/A')}\nND: {description}\nSo tien: {amount:,}d"

        self._display_qr(qr_data, amount, description, note)

        self.deposit_status.config(
            text=f"Giao dich #{tx_id} da tao! Dang kiem tra tu dong...",
            fg=COLORS['success'])
        self.btn_deposit.config(state=tk.NORMAL)

        self.deposit_polling = True
        poll_thread = threading.Thread(target=self._poll_deposit, args=(tx_id,))
        poll_thread.daemon = True
        poll_thread.start()

    def _display_qr(self, qr_data, amount, description, note):
        if not HAS_QRCODE:
            self.qr_label.config(text=f"Can cai thu vien qrcode:\npip install qrcode[pil]")
            self.deposit_info_label.config(text=f"So tien: {amount:,}d\nNoi dung: {description}\n{note}")
            return

        try:
            qr = qrcode.QRCode(version=1, box_size=6, border=3)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            qr_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(qr_dir, exist_ok=True)
            qr_path = os.path.join(qr_dir, f"deposit_qr_{self.deposit_tx_id}.png")
            img.save(qr_path)

            if HAS_PIL:
                pil_img = Image.open(qr_path)
                pil_img = pil_img.resize((250, 250), Image.LANCZOS)
                self._qr_photo = ImageTk.PhotoImage(pil_img)
                self.qr_label.config(image=self._qr_photo, text="")
            else:
                self.qr_label.config(text=f"[QR saved to {qr_path}]\nMo file de xem")

            info = f"So tien: {amount:,}d\n"
            info += f"Noi dung: {description}\n"
            if note:
                info += f"{note}\n"
            info += "\nQuet QR de thanh toan!"
            self.deposit_info_label.config(text=info)

        except Exception as e:
            self.qr_label.config(text=f"Loi tao QR: {e}")
            self.deposit_info_label.config(text=f"So tien: {amount:,}d\nNoi dung: {description}")

    def _poll_deposit(self, tx_id):
        max_attempts = 120
        attempt = 0
        while self.deposit_polling and attempt < max_attempts:
            time.sleep(5)
            attempt += 1

            resp = api_call(f'/api/tool/check-deposit/{tx_id}', 'GET',
                            token=self.token, server_url=self.server_url)

            if 'error' not in resp and resp.get('status') == 'completed':
                self.deposit_polling = False
                self.root.after(0, lambda: self._deposit_completed(tx_id, resp.get('amount', 0)))
                return

        self.deposit_polling = False
        self.root.after(0, lambda: self.deposit_status.config(
            text=f"Giao dich #{tx_id}: Dang cho thanh toan. Quay lai sau de kiem tra.",
            fg=COLORS['warning']))

    def _deposit_completed(self, tx_id, amount):
        self.deposit_status.config(
            text=f"Thanh cong! Da nap {amount:,}d (GD #{tx_id})",
            fg=COLORS['success'])
        self._refresh_balance()
        self._cleanup_qr_files()
        messagebox.showinfo("Thanh cong", f"Da nap {amount:,}d thanh cong!")

    def _cleanup_qr_files(self):
        try:
            qr_dir = os.path.join(os.getcwd(), "temp")
            if os.path.exists(qr_dir):
                for f in os.listdir(qr_dir):
                    if f.startswith("deposit_qr_"):
                        os.remove(os.path.join(qr_dir, f))
        except:
            pass

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
