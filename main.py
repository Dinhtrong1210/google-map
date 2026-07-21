"""
Google Maps Review Bot - Desktop App
Login + Sidebar + API integration + Google Accounts Management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont
import threading
import os
import sys
import json
import time
import random
import webbrowser
import urllib.request
import urllib.error
from datetime import datetime
from review_bot import GoogleMapsReviewBot

VERSION = "4.0.0"
REVIEW_COST_XU_DEFAULT = 12  # gia tri hien thi mac dinh, server la nguon xac thuc thuc te

# Thu muc chua file exe/script that su - KHONG dung os.getcwd() vi thu muc lam viec
# luc khoi chay phu thuoc vao cach nguoi dung mo tool (shortcut khong dat san
# "Start in", chay tu cmd o thu muc khac, v.v.) va co the khac thu muc cai dat,
# khien tool_config.json/profiles khong tim thay tren mot so may.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "tool_config.json")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")

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


def _shade(hex_color, factor):
    """factor > 0: sáng hơn (về phía trắng); factor < 0: tối hơn (về phía đen)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    if factor >= 0:
        r = r + (255 - r) * factor
        g = g + (255 - g) * factor
        b = b + (255 - b) * factor
    else:
        r = r * (1 + factor)
        g = g * (1 + factor)
        b = b * (1 + factor)
    r, g, b = (max(0, min(255, int(v))) for v in (r, g, b))
    return f'#{r:02x}{g:02x}{b:02x}'


def make_button(parent, text, command, bg, fg='#000', hover_amount=0.14, **kwargs):
    """tk.Button với hiệu ứng hover/press, thay cho nút phẳng tĩnh mặc định."""
    hover_bg = _shade(bg, hover_amount)
    press_bg = _shade(bg, -0.14)
    kwargs.setdefault('relief', tk.FLAT)
    kwargs.setdefault('bd', 0)
    kwargs.setdefault('cursor', 'hand2')
    kwargs.setdefault('activebackground', press_bg)
    kwargs.setdefault('activeforeground', fg)

    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, **kwargs)

    def on_enter(_e):
        if str(btn['state']) != 'disabled':
            btn.config(bg=hover_bg)

    def on_leave(_e):
        if str(btn['state']) != 'disabled':
            btn.config(bg=bg)

    btn.bind('<Enter>', on_enter)
    btn.bind('<Leave>', on_leave)
    return btn


class StarRating(tk.Frame):
    """Hàng sao có thể bấm chọn, thay cho tk.Radiobutton mặc định (vòng tròn trắng xấu)."""

    def __init__(self, parent, variable, bg=None, size=15, **kwargs):
        bg = bg or COLORS['bg2']
        super().__init__(parent, bg=bg, **kwargs)
        self.variable = variable
        self.labels = []
        for i in range(1, 6):
            lbl = tk.Label(self, text='★', font=('Segoe UI', size), bg=bg,
                            fg=COLORS['dim'], cursor='hand2', padx=1)
            lbl.pack(side=tk.LEFT)
            lbl.bind('<Button-1>', lambda _e, v=i: self._select(v))
            lbl.bind('<Enter>', lambda _e, v=i: self._preview(v))
            lbl.bind('<Leave>', lambda _e: self._refresh())
            self.labels.append(lbl)
        self._refresh()

    def _select(self, v):
        self.variable.set(v)
        self._refresh()

    def _preview(self, v):
        for i, lbl in enumerate(self.labels, start=1):
            lbl.config(fg=COLORS['star'] if i <= v else COLORS['dim'])

    def _refresh(self):
        v = self.variable.get()
        for i, lbl in enumerate(self.labels, start=1):
            lbl.config(fg=COLORS['star'] if i <= v else COLORS['dim'])


class NumberStepper(tk.Frame):
    """Bộ điều khiển [-] [số] [+] thay cho tk.Spinbox mặc định (mũi tên trắng xấu)."""

    def __init__(self, parent, variable, from_=1, to=999, bg=None, width=3, **kwargs):
        bg = bg or COLORS['bg2']
        super().__init__(parent, bg=bg, **kwargs)
        self.variable = variable
        self.from_ = from_
        self.to = to

        minus = make_button(self, text='−', command=self._dec, bg=COLORS['bg4'], fg=COLORS['fg'],
                             font=('Segoe UI', 9, 'bold'), padx=6, pady=1)
        minus.pack(side=tk.LEFT)

        self.entry = tk.Entry(self, textvariable=variable, width=width, justify=tk.CENTER,
                               bg=COLORS['bg3'], fg=COLORS['fg'], insertbackground=COLORS['fg'],
                               relief=tk.FLAT, font=('Segoe UI', 10))
        self.entry.pack(side=tk.LEFT, padx=2, ipady=3)
        self.entry.bind('<FocusOut>', lambda _e: self._clamp())

        plus = make_button(self, text='+', command=self._inc, bg=COLORS['bg4'], fg=COLORS['fg'],
                            font=('Segoe UI', 9, 'bold'), padx=6, pady=1)
        plus.pack(side=tk.LEFT)

    def _clamp(self):
        try:
            v = int(self.variable.get())
        except (ValueError, tk.TclError):
            v = self.from_
        self.variable.set(max(self.from_, min(self.to, v)))

    def _dec(self):
        self._clamp()
        self.variable.set(max(self.from_, self.variable.get() - 1))

    def _inc(self):
        self._clamp()
        self.variable.set(min(self.to, self.variable.get() + 1))


class ScrollText(tk.Frame):
    """Text + thanh cuộn ttk màu tối, thay cho scrolledtext.ScrolledText (scrollbar xám mặc định xấu)."""

    def __init__(self, parent, height=4, bg=None, fg=None, font=None, wrap=tk.WORD,
                 outer_bg=None, **kwargs):
        bg = bg or COLORS['bg3']
        fg = fg or COLORS['fg']
        super().__init__(parent, bg=outer_bg or COLORS['bg2'])

        self.text = tk.Text(self, height=height, bg=bg, fg=fg, insertbackground=fg,
                             font=font, relief=tk.FLAT, wrap=wrap, **kwargs)
        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=vsb.set)

        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def get(self, *a, **kw):
        return self.text.get(*a, **kw)

    def insert(self, *a, **kw):
        return self.text.insert(*a, **kw)

    def delete(self, *a, **kw):
        return self.text.delete(*a, **kw)

    def see(self, *a, **kw):
        return self.text.see(*a, **kw)

    def bind(self, *a, **kw):
        return self.text.bind(*a, **kw)


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
        icon_path = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self._setup_fonts()
        self._setup_ttk_style()

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
        self._out_of_xu = False
        self.review_media = []  # list of list-of-path, song song voi tung dong binh luan

        self._load_config()
        self._show_login_screen()

    def _setup_fonts(self):
        self.fonts = {
            'title':    tkfont.Font(family="Segoe UI", size=16, weight="bold"),
            'heading':  tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            'body':     tkfont.Font(family="Segoe UI", size=10),
            'small':    tkfont.Font(family="Segoe UI", size=9),
            'tiny':     tkfont.Font(family="Segoe UI", size=8),
            'link':     tkfont.Font(family="Segoe UI", size=8, underline=True),
            'log':      tkfont.Font(family="Consolas", size=9),
            'stat_num': tkfont.Font(family="Consolas", size=24, weight="bold"),
            'stat_sm':  tkfont.Font(family="Consolas", size=16, weight="bold"),
            'sidebar':  tkfont.Font(family="Segoe UI", size=11),
            'sidebar_active': tkfont.Font(family="Segoe UI", size=11, weight="bold"),
            'btn':      tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            'big':      tkfont.Font(family="Segoe UI", size=20, weight="bold"),
        }

    def _setup_ttk_style(self):
        """Áp dụng theme tối cho các widget ttk (Scrollbar, Treeview) - mặc định của hệ điều
        hành rất sáng màu, xung khắc với giao diện tối của app."""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Vertical.TScrollbar', background=COLORS['bg4'], troughcolor=COLORS['bg2'],
                         bordercolor=COLORS['bg2'], arrowcolor=COLORS['dim'], relief=tk.FLAT,
                         lightcolor=COLORS['bg4'], darkcolor=COLORS['bg4'],
                         width=12, arrowsize=12)
        style.map('Vertical.TScrollbar',
                  background=[('active', COLORS['accent']), ('!active', COLORS['bg4'])],
                  arrowcolor=[('active', COLORS['bg']), ('!active', COLORS['dim'])],
                  lightcolor=[('active', COLORS['accent']), ('!active', COLORS['bg4'])],
                  darkcolor=[('active', COLORS['accent']), ('!active', COLORS['bg4'])])

        style.configure('Hist.Treeview', background=COLORS['bg3'], foreground=COLORS['fg'],
                         fieldbackground=COLORS['bg3'], font=self.fonts['small'], rowheight=26,
                         borderwidth=0)
        style.configure('Hist.Treeview.Heading', background=COLORS['bg4'], foreground=COLORS['fg'],
                         font=self.fonts['small'], relief=tk.FLAT)
        style.map('Hist.Treeview.Heading', background=[('active', COLORS['bg4'])])
        style.map('Hist.Treeview', background=[('selected', COLORS['active'])],
                  foreground=[('selected', COLORS['accent'])])

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
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
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _async_api_call(self, endpoint, method='GET', data=None, on_done=None):
        """Chạy api_call() ở thread nền, rồi gọi on_done(resp) trên main thread qua root.after()."""
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
            return "Đã đăng nhập", COLORS['success']
        return "Chưa đăng nhập", COLORS['dim']

    def _clear_window(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ==================== LOGIN SCREEN ====================

    def _show_login_screen(self):
        self._clear_window()
        _container, form = self._build_auth_shell("Đăng nhập")

        self.login_user = self._labeled_entry(form, "Username hoặc Email")
        self.login_pass = self._labeled_entry(form, "Mật khẩu", show='*')

        self.login_status = tk.Label(form, text="", font=self.fonts['small'],
                                     fg=COLORS['error'], bg=COLORS['bg2'])
        self.login_status.pack(pady=(0, 8))

        self.login_btn = make_button(form, text="ĐĂNG NHẬP", command=self._do_login,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                  width=30, pady=8)
        self.login_btn.pack(pady=(4, 0))

        links_row = tk.Frame(form, bg=COLORS['bg2'])
        links_row.pack(pady=(16, 0))

        reg_link = tk.Label(links_row, text="Đăng ký tài khoản", font=self.fonts['tiny'],
                             fg=COLORS['accent'], bg=COLORS['bg2'], cursor="hand2")
        reg_link.pack(side=tk.LEFT, padx=(0, 20))
        reg_link.bind('<Button-1>', lambda e: self._show_register_screen())

        forgot_link = tk.Label(links_row, text="Quên mật khẩu?", font=self.fonts['tiny'],
                                fg=COLORS['dim'], bg=COLORS['bg2'], cursor="hand2")
        forgot_link.pack(side=tk.LEFT)
        forgot_link.bind('<Button-1>', lambda e: self._show_forgot_password_screen())

        self.login_pass.bind('<Return>', lambda e: self._do_login())
        self.login_user.focus_set()

    def _do_login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get().strip()

        if not username or not password:
            self.login_status.config(text="Nhập đầy đủ thông tin!")
            return

        self.server_url = SERVER_URL
        self.login_status.config(text="Đang kết nối...", fg=COLORS['warning'])
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

    # ==================== REGISTER SCREEN ====================

    def _labeled_entry(self, parent, label_text, show=None, bg=None):
        bg = bg or COLORS['bg2']
        tk.Label(parent, text=label_text, font=self.fonts['small'],
                 fg=COLORS['dim'], bg=bg, anchor=tk.W).pack(fill=tk.X)
        e = tk.Entry(parent, bg=COLORS['bg3'], fg=COLORS['fg'],
                     insertbackground=COLORS['fg'], font=self.fonts['body'],
                     relief=tk.FLAT, show=show, highlightthickness=1,
                     highlightbackground=COLORS['border'], highlightcolor=COLORS['accent'])
        e.pack(fill=tk.X, ipady=6, pady=(2, 10))
        return e

    def _make_logo_badge(self, parent, size=64):
        canvas = tk.Canvas(parent, width=size, height=size, bg=COLORS['bg'], highlightthickness=0)
        canvas.create_oval(2, 2, size - 2, size - 2, fill=COLORS['accent'], outline='')
        canvas.create_text(size / 2, size / 2, text='📍', font=('Segoe UI Emoji', int(size * 0.42)))
        return canvas

    def _build_auth_shell(self, heading):
        """Khung dùng chung cho màn hình Đăng nhập / Đăng ký / Quên mật khẩu:
        bên trái là panel giới thiệu thương hiệu, bên phải là thẻ (card) chứa form."""
        left = tk.Frame(self.root, bg=COLORS['sidebar'], width=420)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        left_inner = tk.Frame(left, bg=COLORS['sidebar'])
        left_inner.place(relx=0.5, rely=0.5, anchor='center', width=310)

        self._make_logo_badge(left_inner, size=64).pack(pady=(0, 14))
        tk.Label(left_inner, text="GOOGLE MAPS\nREVIEW BOT", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['sidebar'], justify=tk.CENTER).pack()
        tk.Label(left_inner, text=f"v{VERSION}", font=self.fonts['tiny'], fg=COLORS['dim'],
                 bg=COLORS['sidebar']).pack(pady=(2, 18))

        intro = ("Công cụ tự động hoá đánh giá Google Maps: quản lý hàng loạt "
                 "tài khoản Google, chạy song song nhiều Chrome, theo dõi lịch sử "
                 "và thống kê ngay trên desktop.")
        tk.Label(left_inner, text=intro, font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['sidebar'], wraplength=300, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 16))

        for feat in ("Đa tài khoản Google", "Chạy song song nhiều Chrome", "Nạp xu tự động qua SePay"):
            row = tk.Frame(left_inner, bg=COLORS['sidebar'])
            row.pack(anchor=tk.W, pady=2)
            tk.Label(row, text="✓", font=self.fonts['small'], fg=COLORS['accent'],
                     bg=COLORS['sidebar']).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text=feat, font=self.fonts['small'], fg=COLORS['fg'],
                     bg=COLORS['sidebar']).pack(side=tk.LEFT)

        tk.Frame(left_inner, bg=COLORS['border'], height=1).pack(fill=tk.X, pady=20)

        tk.Label(left_inner, text="Sản phẩm được phát triển & vận hành bởi",
                 font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['sidebar'],
                 anchor=tk.W, justify=tk.LEFT).pack(fill=tk.X)
        tk.Label(left_inner, text="DJ MEDIA", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['sidebar'], anchor=tk.W).pack(fill=tk.X, pady=(2, 0))
        tk.Label(left_inner, text="Chuyên hỗ trợ DVFB, Quảng cáo Marketing,\nĐào tạo học viên, Thiết kế Website\n& Phát triển các Tools Auto tự động",
                 font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['sidebar'],
                 anchor=tk.W, justify=tk.LEFT, wraplength=300).pack(fill=tk.X)

        right = tk.Frame(self.root, bg=COLORS['bg'])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        container = tk.Frame(right, bg=COLORS['bg'])
        container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(container, text=heading, font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(pady=(0, 20))

        card = tk.Frame(container, bg=COLORS['bg2'], highlightbackground=COLORS['border'],
                         highlightthickness=1)
        card.pack()
        card_body = tk.Frame(card, bg=COLORS['bg2'], padx=32, pady=28, width=360)
        card_body.pack()

        return container, card_body

    def _show_register_screen(self):
        self._clear_window()
        _container, form = self._build_auth_shell("Tạo tài khoản mới")

        self.reg_username = self._labeled_entry(form, "Username (tối thiểu 3 ký tự)")
        self.reg_email = self._labeled_entry(form, "Email")
        self.reg_fullname = self._labeled_entry(form, "Họ tên (không bắt buộc)")
        self.reg_password = self._labeled_entry(form, "Mật khẩu (tối thiểu 6 ký tự)", show='*')
        self.reg_password2 = self._labeled_entry(form, "Nhập lại mật khẩu", show='*')

        self.reg_status = tk.Label(form, text="", font=self.fonts['small'], fg=COLORS['error'],
                                    bg=COLORS['bg2'], wraplength=340, justify=tk.LEFT)
        self.reg_status.pack(pady=(0, 8))

        self.reg_btn = make_button(form, text="ĐĂNG KÝ", command=self._do_register,
                                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                                  width=30, pady=8)
        self.reg_btn.pack(pady=(4, 0))

        back_link = tk.Label(form, text="← Quay lại đăng nhập", font=self.fonts['tiny'],
                              fg=COLORS['dim'], bg=COLORS['bg2'], cursor="hand2")
        back_link.pack(pady=(16, 0))
        back_link.bind('<Button-1>', lambda e: self._show_login_screen())

        self.reg_username.focus_set()

    def _do_register(self):
        username = self.reg_username.get().strip()
        email = self.reg_email.get().strip()
        fullname = self.reg_fullname.get().strip()
        password = self.reg_password.get()
        password2 = self.reg_password2.get()

        if not username or not email or not password:
            self.reg_status.config(text="Nhập đầy đủ thông tin!", fg=COLORS['error'])
            return
        if len(username) < 3:
            self.reg_status.config(text="Username tối thiểu 3 ký tự!", fg=COLORS['error'])
            return
        if len(password) < 6:
            self.reg_status.config(text="Mật khẩu tối thiểu 6 ký tự!", fg=COLORS['error'])
            return
        if password != password2:
            self.reg_status.config(text="Mật khẩu nhập lại không khớp!", fg=COLORS['error'])
            return
        if '@' not in email:
            self.reg_status.config(text="Email không hợp lệ!", fg=COLORS['error'])
            return

        self.server_url = SERVER_URL
        self.reg_status.config(text="Đang đăng ký...", fg=COLORS['warning'])
        self.reg_btn.config(state=tk.DISABLED)

        def on_done(resp):
            if not hasattr(self, 'reg_btn') or not self.reg_btn.winfo_exists():
                return
            self.reg_btn.config(state=tk.NORMAL)
            if 'error' in resp:
                self.reg_status.config(text=resp['error'], fg=COLORS['error'])
                return
            messagebox.showinfo("Thành công", "Đăng ký thành công! Hãy đăng nhập.")
            self._show_login_screen()
            self.login_user.insert(0, username)
            self.login_pass.focus_set()

        self._async_api_call('/api/tool/register', 'POST', {
            'username': username, 'email': email, 'password': password, 'fullname': fullname
        }, on_done=on_done)

    # ==================== FORGOT PASSWORD SCREEN ====================

    def _show_forgot_password_screen(self):
        self._clear_window()

        _container, form = self._build_auth_shell("Quên mật khẩu")

        tk.Label(form, text="Nhập username hoặc email đã đăng ký để nhận mã OTP qua email.",
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['bg2'],
                 wraplength=300, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 14))

        self.forgot_identifier = self._labeled_entry(form, "Username hoặc Email")

        self.forgot_status = tk.Label(form, text="", font=self.fonts['small'], fg=COLORS['error'],
                                       bg=COLORS['bg2'], wraplength=340, justify=tk.LEFT)
        self.forgot_status.pack(pady=(0, 8))

        self.forgot_send_btn = make_button(form, text="GỬI MÃ OTP", command=self._do_forgot_request,
                                          bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                                          width=30, pady=8)
        self.forgot_send_btn.pack(pady=(4, 0))

        # Bước 2: chỉ hiện sau khi gửi OTP thành công
        self.forgot_step2_frame = tk.Frame(form, bg=COLORS['bg2'])

        self.forgot_otp = self._labeled_entry(self.forgot_step2_frame, "Mã OTP (6 số, gửi qua email)")
        self.forgot_new_pass = self._labeled_entry(self.forgot_step2_frame, "Mật khẩu mới", show='*')

        self.forgot_reset_btn = make_button(self.forgot_step2_frame, text="ĐẶT LẠI MẬT KHẨU",
                                           command=self._do_reset_password,
                                           bg=COLORS['success'], fg='#000', font=self.fonts['btn'],
                                           width=30, pady=8)
        self.forgot_reset_btn.pack(pady=(4, 0))

        self.forgot_back_link = tk.Label(form, text="← Quay lại đăng nhập", font=self.fonts['tiny'],
                              fg=COLORS['dim'], bg=COLORS['bg2'], cursor="hand2")
        self.forgot_back_link.pack(pady=(16, 0))
        self.forgot_back_link.bind('<Button-1>', lambda e: self._show_login_screen())

        self.forgot_identifier.focus_set()

    def _do_forgot_request(self):
        identifier = self.forgot_identifier.get().strip()
        if not identifier:
            self.forgot_status.config(text="Nhập username hoặc email!", fg=COLORS['error'])
            return

        self.server_url = SERVER_URL
        self.forgot_status.config(text="Đang gửi mã OTP...", fg=COLORS['warning'])
        self.forgot_send_btn.config(state=tk.DISABLED)

        def on_done(resp):
            if not hasattr(self, 'forgot_send_btn') or not self.forgot_send_btn.winfo_exists():
                return
            self.forgot_send_btn.config(state=tk.NORMAL)
            if 'error' in resp:
                self.forgot_status.config(text=resp['error'], fg=COLORS['error'])
                return
            self.forgot_status.config(text=resp.get('message', 'Đã gửi mã OTP, kiểm tra email!'),
                                       fg=COLORS['success'])
            self.forgot_step2_frame.pack(fill=tk.X, before=self.forgot_back_link)
            self.forgot_otp.focus_set()

        self._async_api_call('/api/tool/forgot-password', 'POST',
                              {'username': identifier}, on_done=on_done)

    def _do_reset_password(self):
        identifier = self.forgot_identifier.get().strip()
        otp = self.forgot_otp.get().strip()
        new_password = self.forgot_new_pass.get()

        if not otp or not new_password:
            self.forgot_status.config(text="Nhập đầy đủ mã OTP và mật khẩu mới!", fg=COLORS['error'])
            return
        if len(new_password) < 6:
            self.forgot_status.config(text="Mật khẩu mới tối thiểu 6 ký tự!", fg=COLORS['error'])
            return

        self.forgot_status.config(text="Đang đặt lại mật khẩu...", fg=COLORS['warning'])
        self.forgot_reset_btn.config(state=tk.DISABLED)

        def on_done(resp):
            if not hasattr(self, 'forgot_reset_btn') or not self.forgot_reset_btn.winfo_exists():
                return
            self.forgot_reset_btn.config(state=tk.NORMAL)
            if 'error' in resp:
                self.forgot_status.config(text=resp['error'], fg=COLORS['error'])
                return
            messagebox.showinfo("Thành công", resp.get('message', 'Đã đặt lại mật khẩu!'))
            self._show_login_screen()
            self.login_user.insert(0, identifier)
            self.login_pass.focus_set()

        self._async_api_call('/api/tool/reset-password', 'POST', {
            'username': identifier, 'otp': otp, 'new_password': new_password
        }, on_done=on_done)

    # ==================== MAIN UI ====================

    def _show_main_ui(self):
        self._clear_window()

        sidebar = tk.Frame(self.root, bg=COLORS['sidebar'], width=210)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        header = tk.Frame(sidebar, bg=COLORS['sidebar'])
        header.pack(fill=tk.X, padx=16, pady=(18, 4))

        avatar = tk.Canvas(header, width=36, height=36, bg=COLORS['sidebar'], highlightthickness=0)
        avatar.create_oval(0, 0, 36, 36, fill=COLORS['accent'], outline='')
        initial = (self.user_info.get('username') or '?')[0:1].upper() or '?'
        avatar.create_text(18, 18, text=initial, font=('Segoe UI', 13, 'bold'), fill='#000000')
        avatar.pack(side=tk.LEFT, padx=(0, 10))

        name_col = tk.Frame(header, bg=COLORS['sidebar'])
        name_col.pack(side=tk.LEFT)
        tk.Label(name_col, text="REVIEW BOT", font=self.fonts['heading'],
                 fg=COLORS['fg'], bg=COLORS['sidebar'], anchor=tk.W).pack(anchor=tk.W)
        tk.Label(name_col, text=self.user_info.get('username', ''),
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['sidebar'], anchor=tk.W).pack(anchor=tk.W)

        sep = tk.Frame(sidebar, bg=COLORS['border'], height=1)
        sep.pack(fill=tk.X, padx=12, pady=12)

        self.sidebar_btns = {}
        self.sidebar_accents = {}
        menu_items = [
            ('home', '🏠  Đánh giá'),
            ('google_accounts', '📧  Tài khoản GG'),
            ('history', '📋  Lịch sử'),
            ('deposit', '💰  Nạp xu'),
            ('account', '👤  Tài khoản'),
            ('stats', '📊  Thống kê'),
        ]

        for key, label in menu_items:
            row = tk.Frame(sidebar, bg=COLORS['sidebar'])
            row.pack(fill=tk.X)

            accent = tk.Frame(row, bg=COLORS['sidebar'], width=3)
            accent.pack(side=tk.LEFT, fill=tk.Y)

            btn = tk.Label(row, text=label, font=self.fonts['sidebar'],
                           fg=COLORS['dim'], bg=COLORS['sidebar'],
                           cursor="hand2", anchor=tk.W, padx=13, pady=10)
            btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            btn.bind('<Button-1>', lambda e, k=key: self._navigate(k))

            def on_enter(_e, k=key):
                if self.current_page != k:
                    self.sidebar_btns[k].config(bg=COLORS['bg2'])
            def on_leave(_e, k=key):
                if self.current_page != k:
                    self.sidebar_btns[k].config(bg=COLORS['sidebar'])
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)

            self.sidebar_btns[key] = btn
            self.sidebar_accents[key] = accent

        sep2 = tk.Frame(sidebar, bg=COLORS['border'], height=1)
        sep2.pack(fill=tk.X, padx=12, pady=12)

        stats_card = tk.Frame(sidebar, bg=COLORS['bg2'], highlightbackground=COLORS['border'],
                               highlightthickness=1)
        stats_card.pack(fill=tk.X, padx=12)
        self.sidebar_stats = tk.Label(stats_card, text="", font=self.fonts['small'], justify=tk.LEFT,
                                       fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W, padx=10, pady=8)
        self.sidebar_stats.pack(fill=tk.X)

        bottom = tk.Frame(sidebar, bg=COLORS['sidebar'])
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=14)
        logout_lbl = tk.Label(bottom, text="⏻  Đăng xuất", font=self.fonts['tiny'],
                 fg=COLORS['error'], bg=COLORS['sidebar'], cursor="hand2")
        logout_lbl.pack(anchor=tk.W)
        logout_lbl.bind('<Button-1>', lambda e: self._logout())
        logout_lbl.bind('<Enter>', lambda e: logout_lbl.config(fg=_shade(COLORS['error'], 0.25)))
        logout_lbl.bind('<Leave>', lambda e: logout_lbl.config(fg=COLORS['error']))

        support_card = tk.Frame(sidebar, bg=COLORS['bg2'], highlightbackground=COLORS['border'],
                                 highlightthickness=1)
        support_card.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 10))
        support_inner = tk.Frame(support_card, bg=COLORS['bg2'], padx=10, pady=8)
        support_inner.pack(fill=tk.X)

        tk.Label(support_inner, text="Hỗ trợ", font=self.fonts['tiny'], fg=COLORS['dim'],
                 bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 4))

        self._make_support_link(support_inner, "💬 Zalo: 0828118789", "https://zalo.me/0828118789")
        self._make_support_link(support_inner, "✈️ TG: @Trongsuport", "https://t.me/Trongsuport")

        intro_card = tk.Frame(sidebar, bg=COLORS['bg2'], highlightbackground=COLORS['border'],
                               highlightthickness=1)
        intro_card.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(10, 0))
        intro_inner = tk.Frame(intro_card, bg=COLORS['bg2'], padx=10, pady=8)
        intro_inner.pack(fill=tk.X)

        tk.Label(intro_inner, text="🏢 DJ Media", font=self.fonts['tiny'], fg=COLORS['dim'],
                 bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 4))
        tk.Label(intro_inner,
                 text="DVFB • Marketing • Đào tạo\nWebsite • Tools Auto",
                 font=self.fonts['tiny'], fg=COLORS['fg'], bg=COLORS['bg2'],
                 wraplength=175, justify=tk.LEFT, anchor=tk.W).pack(fill=tk.X)

        self.main_area = tk.Frame(self.root, bg=COLORS['bg'])
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._update_sidebar_stats()
        self._navigate('home')

    def _make_scrollable_page(self, parent, padx=20, pady=16):
        """Tao 1 Frame ma toan bo noi dung ben trong cuon duoc bang lan chuot khi
        vuot qua chieu cao cua so - dung thay cho tk.Frame(parent) thong thuong o
        dau moi ham _build_xxx_page. Tra ve Frame de build noi dung vao nhu binh thuong."""
        container = tk.Frame(parent, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg=COLORS['bg'], highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        inner = tk.Frame(canvas, bg=COLORS['bg'])
        inner_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        content = tk.Frame(inner, bg=COLORS['bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)

        def _on_inner_configure(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind('<Configure>', _on_inner_configure)

        def _on_canvas_configure(event):
            canvas.itemconfig(inner_id, width=event.width)
        canvas.bind('<Configure>', _on_canvas_configure)

        self._bind_mousewheel(canvas, canvas)
        return content

    def _bind_mousewheel(self, hover_widget, canvas):
        """Cho phep cuon canvas bang lan chuot, chi khi con tro dang o tren hover_widget
        (tranh anh huong scroll cua cac vung khac trong app vi bind_all la toan cuc)."""
        def _on_wheel(event):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass  # canvas da bi huy (vd: trang duoc ve lai trong khi chuot dang o tren no)

        def _unbind(_e=None):
            try:
                hover_widget.unbind_all('<MouseWheel>')
            except tk.TclError:
                pass

        hover_widget.bind('<Enter>', lambda e: hover_widget.bind_all('<MouseWheel>', _on_wheel))
        hover_widget.bind('<Leave>', _unbind)
        hover_widget.bind('<Destroy>', _unbind)

    def _make_support_link(self, parent, text, url):
        lbl = tk.Label(parent, text=text, font=self.fonts['link'], fg=COLORS['accent'],
                       bg=COLORS['bg2'], cursor='hand2', anchor=tk.W)
        lbl.pack(fill=tk.X, pady=1)
        lbl.bind('<Button-1>', lambda e: webbrowser.open(url))
        lbl.bind('<Enter>', lambda e: lbl.config(fg=_shade(COLORS['accent'], 0.3)))
        lbl.bind('<Leave>', lambda e: lbl.config(fg=COLORS['accent']))
        return lbl

    def _update_sidebar_stats(self):
        acc_count = len(self.google_accounts)
        logged_in = sum(1 for v in self.google_accounts_status.values() if v)
        xu = (self.user_info or {}).get('xu', 0)
        self.sidebar_stats.config(
            text=f"Xu: {xu:,} \U0001FA99\nGG accounts: {acc_count} ({logged_in} active)\nĐã đánh giá: {self.review_count}")

    def _navigate(self, page):
        self.current_page = page
        for key, btn in self.sidebar_btns.items():
            accent = self.sidebar_accents.get(key)
            if key == page:
                btn.config(bg=COLORS['active'], fg=COLORS['accent'], font=self.fonts['sidebar_active'])
                if accent:
                    accent.config(bg=COLORS['accent'])
            else:
                btn.config(bg=COLORS['sidebar'], fg=COLORS['dim'], font=self.fonts['sidebar'])
                if accent:
                    accent.config(bg=COLORS['sidebar'])

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
        if messagebox.askyesno("Xác nhận", "Đăng xuất?"):
            self.token = None
            self.user_info = None
            self._save_config()
            self._show_login_screen()

    # ==================== HOME PAGE ====================

    def _build_home_page(self):
        page = self._make_scrollable_page(self.main_area)

        tk.Label(page, text="Chạy đánh giá", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W)
        tk.Label(page, text=f"Đã đánh giá: {self.review_count} | Tài khoản GG: {len(self.google_accounts)} | "
                             f"Chi phí: {REVIEW_COST_XU_DEFAULT} xu/đánh giá",
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
        StarRating(row_opt, self.star_var, bg=COLORS['bg2']).pack(side=tk.LEFT, padx=(4, 0))

        tk.Label(row_opt, text="  Chrome:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT, padx=(12, 0))
        self.chrome_count = tk.IntVar(value=1)
        NumberStepper(row_opt, self.chrome_count, from_=1, to=10,
                      bg=COLORS['bg2']).pack(side=tk.LEFT, padx=4)

        tk.Label(row_opt, text="  Số lượng:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT, padx=(12, 0))
        self.target_count = tk.IntVar(value=5)
        NumberStepper(row_opt, self.target_count, from_=1, to=500, width=4,
                      bg=COLORS['bg2']).pack(side=tk.LEFT, padx=4)

        sec_accounts = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec_accounts.pack(fill=tk.X, pady=(0, 10))
        inner_acc = tk.Frame(sec_accounts, bg=COLORS['bg2'], padx=14, pady=10)
        inner_acc.pack(fill=tk.X)

        acc_header = tk.Frame(inner_acc, bg=COLORS['bg2'])
        acc_header.pack(fill=tk.X)
        tk.Label(acc_header, text="Tài khoản Google:", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(side=tk.LEFT)

        count_text = f"({len(self.google_accounts)} tài khoản)"
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

        make_button(add_acc_row, text="+ Thêm", command=self._quick_add_account,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['tiny'],
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(0, 4))

        self.account_list_frame = tk.Frame(inner_acc, bg=COLORS['bg2'])
        self.account_list_frame.pack(fill=tk.X, pady=(4, 0))
        self._refresh_home_account_list()

        sec2 = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        sec2.pack(fill=tk.X, pady=(0, 10))
        inner2 = tk.Frame(sec2, bg=COLORS['bg2'], padx=14, pady=10)
        inner2.pack(fill=tk.X)

        tk.Label(inner2, text="Nội dung bình luận (mỗi dòng = 1 đánh giá):", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)
        self.comment_text = ScrollText(inner2, height=4, bg=COLORS['bg3'], fg=COLORS['fg'],
                                        font=self.fonts['body'], outer_bg=COLORS['bg2'])
        self.comment_text.pack(fill=tk.X, pady=(2, 4))

        self.comment_hint = tk.Label(inner2, text="0 dòng", font=self.fonts['tiny'],
                                     fg=COLORS['dim'], bg=COLORS['bg2'])
        self.comment_hint.pack(anchor=tk.W)
        self.comment_text.bind('<KeyRelease>', self._on_comment_text_changed)

        tk.Label(inner2, text="Ảnh/video riêng cho từng dòng (tùy chọn):", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(10, 2))
        self.media_rows_frame = tk.Frame(inner2, bg=COLORS['bg2'])
        self.media_rows_frame.pack(fill=tk.X)
        self._refresh_review_media_rows()

        btn_row = tk.Frame(page, bg=COLORS['bg'])
        btn_row.pack(fill=tk.X, pady=(0, 10))

        self.btn_start = make_button(btn_row, text=">> BẮT ĐẦU ĐÁNH GIÁ <<",
                                    command=self._start_review, bg=COLORS['success'], fg='#000',
                                    font=self.fonts['btn'], relief=tk.FLAT, padx=20, pady=6, cursor="hand2")
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = make_button(btn_row, text="DỪNG", command=self._stop_review,
                                   bg=COLORS['error'], fg='white', font=self.fonts['btn'],
                                   relief=tk.FLAT, padx=16, pady=6, cursor="hand2", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))

        save_btn_row = tk.Frame(page, bg=COLORS['bg'])
        save_btn_row.pack(fill=tk.X, pady=(0, 8))

        make_button(save_btn_row, text="💾  Lưu cấu hình", command=self._save_home_config,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

        make_button(save_btn_row, text="📂  Tải cấu hình", command=self._load_home_config,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

        make_button(btn_row, text="Xóa Chrome", command=self._kill_chrome,
                  bg=COLORS['warning'], fg='#000', font=self.fonts['small'],
                  relief=tk.FLAT, padx=8, pady=6, cursor="hand2").pack(side=tk.RIGHT)

        log_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_inner = tk.Frame(log_frame, bg=COLORS['bg2'], padx=4, pady=4)
        log_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_inner, text="  LOG", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X)
        self.log_text = ScrollText(log_inner, height=14, bg=COLORS['log_bg'], fg=COLORS['log_fg'],
                                    font=self.fonts['log'], outer_bg=COLORS['bg2'])
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self._log("Sẵn sàng! Nhập thông tin và bắt đầu đánh giá.")

    def _build_account_row(self, parent, i, acc):
        row = tk.Frame(parent, bg=COLORS['bg3'], padx=6, pady=3)
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

        del_btn = tk.Label(row, text="[Xóa]", font=self.fonts['tiny'], fg=COLORS['error'],
                           bg=COLORS['bg3'], cursor="hand2")
        del_btn.pack(side=tk.RIGHT)
        del_btn.bind('<Button-1>', lambda e, idx=i: self._remove_account(idx))

    def _refresh_home_account_list(self):
        for w in self.account_list_frame.winfo_children():
            w.destroy()

        if not self.google_accounts:
            tk.Label(self.account_list_frame, text="Chưa có tài khoản nào. Thêm ở trên hoặc vào trang 'Tài khoản GG'.",
                     font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['bg2']).pack(anchor=tk.W)
            return

        total = len(self.google_accounts)
        limit = getattr(self, '_home_acc_limit', 10)
        shown = self.google_accounts[:limit]

        if len(shown) > 10:
            # Danh sach da mo rong qua 1 trang - bo vao khung co gioi han chieu cao,
            # cuon duoc bang lan chuot, tranh day trang chinh xuong qua dai.
            list_holder = tk.Frame(self.account_list_frame, bg=COLORS['bg2'])
            list_holder.pack(fill=tk.X)
            canvas = tk.Canvas(list_holder, bg=COLORS['bg2'], highlightthickness=0, height=260)
            vsb = ttk.Scrollbar(list_holder, orient=tk.VERTICAL, command=canvas.yview)
            rows_frame = tk.Frame(canvas, bg=COLORS['bg2'])
            rows_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=rows_frame, anchor=tk.NW)
            canvas.configure(yscrollcommand=vsb.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            self._bind_mousewheel(canvas, canvas)
            row_parent = rows_frame
        else:
            row_parent = self.account_list_frame

        for i, acc in enumerate(shown):
            self._build_account_row(row_parent, i, acc)

        if total > len(shown):
            more_lbl = tk.Label(self.account_list_frame, text=f"▼ Xem thêm ({total - len(shown)} tài khoản)",
                                 font=self.fonts['tiny'], fg=COLORS['accent'], bg=COLORS['bg2'], cursor="hand2")
            more_lbl.pack(anchor=tk.W, pady=(4, 0))
            more_lbl.bind('<Button-1>', lambda e: self._expand_home_accounts())

        if self.acc_count_label:
            self.acc_count_label.config(text=f"({total} tài khoản)")

    def _expand_home_accounts(self):
        self._home_acc_limit = getattr(self, '_home_acc_limit', 10) + 10
        self._refresh_home_account_list()

    def _quick_add_account(self):
        email = self.quick_email.get().strip()
        password = self.quick_pass.get().strip()
        if not email or not password:
            messagebox.showwarning("Cảnh báo", "Nhập đầy đủ email và mật khẩu!")
            return

        for acc in self.google_accounts:
            if acc.get('email', '').lower() == email.lower():
                messagebox.showwarning("Cảnh báo", "Tài khoản này đã tồn tại!")
                return

        self.google_accounts.append({'email': email, 'password': password})
        self.google_accounts_status[email] = self._check_profile_session(email)
        self._save_config()
        self._refresh_home_account_list()
        self.quick_email.delete(0, tk.END)
        self.quick_pass.delete(0, tk.END)
        self._log(f"Đã thêm tài khoản: {email}")

    def _remove_account(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            if messagebox.askyesno("Xác nhận", f"Xóa tài khoản {email}?"):
                self.google_accounts.pop(index)
                self.google_accounts_status.pop(email, None)
                self._save_config()
                self._refresh_home_account_list()
                self._log(f"Đã xóa tài khoản: {email}")

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
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._log("Đã lưu cấu hình!")
            messagebox.showinfo("Thành công", "Đã lưu cấu hình!")
        except Exception as e:
            self._log(f"Lỗi lưu cấu hình: {e}", True)
            messagebox.showerror("Lỗi", f"Không thể lưu: {e}")

    def _load_home_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
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
                self._log("Đã tải cấu hình!")
                messagebox.showinfo("Thành công", "Đã tải cấu hình!")
            else:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy file cấu hình!")
        except Exception as e:
            self._log(f"Lỗi tải cấu hình: {e}", True)
            messagebox.showerror("Lỗi", f"Không thể tải: {e}")

    def _update_comment_hint(self, event=None):
        raw = self.comment_text.get('1.0', tk.END).strip()
        lines = [l for l in raw.split('\n') if l.strip()] if raw else []
        self.comment_hint.config(text=f"{len(lines)} nội dung | Mỗi tài khoản lấy 1 nội dung ngẫu nhiên")

    def _on_comment_text_changed(self, event=None):
        self._update_comment_hint()
        self._refresh_review_media_rows()

    def _get_comment_lines(self):
        raw = self.comment_text.get('1.0', tk.END).strip()
        return [l.strip() for l in raw.split('\n') if l.strip()] if raw else []

    def _refresh_review_media_rows(self):
        lines = self._get_comment_lines()
        # dieu chinh do dai self.review_media cho khop so dong hien tai,
        # giu nguyen media da gan cho cac dong con lai theo vi tri
        while len(self.review_media) < len(lines):
            self.review_media.append([])
        del self.review_media[len(lines):]

        for w in self.media_rows_frame.winfo_children():
            w.destroy()

        if not lines:
            tk.Label(self.media_rows_frame,
                     text="Nhập nội dung bình luận ở trên trước, rồi gán ảnh/video riêng cho từng dòng ở đây.",
                     font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['bg2'],
                     anchor=tk.W, wraplength=520, justify=tk.LEFT).pack(fill=tk.X, pady=2)
            return

        for i, line in enumerate(lines):
            row = tk.Frame(self.media_rows_frame, bg=COLORS['bg2'])
            row.pack(fill=tk.X, pady=1)
            preview = (line[:40] + '…') if len(line) > 40 else line
            tk.Label(row, text=f"Dòng {i + 1}: {preview}", font=self.fonts['tiny'],
                     fg=COLORS['fg'], bg=COLORS['bg2'], anchor=tk.W, width=45).pack(side=tk.LEFT)
            make_button(row, text="📷 Ảnh/Video", command=lambda idx=i: self._pick_media_for_line(idx),
                      bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['tiny'],
                      relief=tk.FLAT, padx=6, pady=2, cursor="hand2").pack(side=tk.LEFT, padx=(6, 6))
            count = len(self.review_media[i])
            hint_text = f"✓ {count} file" if count else "Chưa chọn"
            hint_color = COLORS['success'] if count else COLORS['dim']
            tk.Label(row, text=hint_text, font=self.fonts['tiny'], fg=hint_color,
                     bg=COLORS['bg2']).pack(side=tk.LEFT)

    def _pick_media_for_line(self, idx):
        paths = filedialog.askopenfilenames(
            title=f"Chọn ảnh/video cho dòng {idx + 1}",
            filetypes=[("Ảnh/Video", "*.jpg *.jpeg *.png *.webp *.mp4 *.mov *.avi *.mkv"),
                       ("Tất cả file", "*.*")]
        )
        if idx < len(self.review_media):
            self.review_media[idx] = list(paths) if paths else []
        self._refresh_review_media_rows()

    def _log(self, msg, is_error=False):
        def _do():
            tag = "[ERR] " if is_error else ""
            self.log_text.insert(tk.END, f"{tag}{msg}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _do)

    def _start_review(self):
        url = self.url_entry.get().strip()
        comment_lines = self._get_comment_lines()
        target = self.target_count.get()
        chrome_count = self.chrome_count.get()
        stars = self.star_var.get()

        if not url:
            messagebox.showerror("Lỗi", "Nhập Link Google Maps!")
            return
        if not comment_lines:
            messagebox.showerror("Lỗi", "Nhập ít nhất 1 nội dung bình luận!")
            return
        for i, line in enumerate(comment_lines):
            if len(line) < 5:
                messagebox.showerror("Lỗi", f"Dòng {i+1} quá ngắn:\n{line}")
                return

        if not self.google_accounts:
            messagebox.showerror("Lỗi", "Nhập ít nhất 1 tài khoản Google!\nVào trang 'Tài khoản GG' để thêm.")
            return

        # Dam bao review_media dung khop voi comment_lines hien tai (vd nguoi
        # dung go xong roi bam Bat dau ma chua trigger KeyRelease lan cuoi).
        self._refresh_review_media_rows()
        review_items = list(zip(comment_lines, self.review_media))

        total_accounts = len(self.google_accounts)
        actual_chrome = max(1, min(chrome_count, target, total_accounts))

        self.btn_start.config(state=tk.DISABLED)

        def on_profile(resp):
            self.btn_start.config(state=tk.NORMAL)
            if 'error' in resp:
                messagebox.showerror("Lỗi", f"Không kiểm tra được số xu: {resp['error']}")
                return

            xu = resp.get('xu', 0)
            cost = resp.get('review_cost_xu', REVIEW_COST_XU_DEFAULT)
            if xu < cost:
                self._prompt_topup(
                    f"Bạn đang có {xu} xu, cần tối thiểu {cost} xu để chạy 1 đánh giá.\n\n"
                    f"Nạp thêm xu ngay bây giờ?")
                return

            self._confirm_and_start_review(url, review_items, stars, target, chrome_count,
                                            total_accounts, actual_chrome, cost)

        self._async_api_call('/api/tool/profile', 'GET', on_done=on_profile)

    def _prompt_topup(self, message):
        if messagebox.askyesno("Không đủ xu", message):
            self._navigate('deposit')

    def _confirm_and_start_review(self, url, review_items, stars, target, chrome_count,
                                   total_accounts, actual_chrome, cost):
        if not messagebox.askyesno("Xác nhận",
                f"Mục tiêu: {target} đánh giá THÀNH CÔNG\n"
                f"Tài khoản khả dụng: {total_accounts}\n"
                f"Chrome cùng lúc: {actual_chrome}\n"
                f"Chi phí: {cost} xu/đánh giá (tối đa {target * cost} xu nếu đủ tài khoản)\n\n"
                f"Nếu 1 tài khoản bị lỗi/không đăng nhập được, tool sẽ tự động\n"
                f"thử tài khoản khác cho đến khi đủ mục tiêu (hoặc hết tài khoản/hết xu).\n\n"
                f"Bắt đầu?"):
            return

        self.log_text.delete('1.0', tk.END)
        self._log(f"BẮT ĐẦU: mục tiêu {target} đánh giá thành công | {total_accounts} tài khoản khả dụng")
        self._log(f"{actual_chrome} Chrome song song | {cost} xu/đánh giá")
        self._stop_event.clear()
        self._out_of_xu = False
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._is_reviewing = True

        thread = threading.Thread(target=self._run_review,
                                  args=(url, review_items, stars, target, chrome_count))
        thread.daemon = True
        thread.start()

    def _run_review(self, url, review_items, stars, target, chrome_count):
        session_reviewed = 0
        session_failed = 0
        lock = threading.Lock()
        next_index = [0]  # con tro dung chung, dung list de sua duoc trong closure

        # review_items la list (comment, media_paths) - shuffle CA CAP voi
        # nhau de moi noi dung van giu dung media rieng cua no sau khi tron,
        # khong duoc tron rieng comment va media (se lam sai lech cap).
        shuffled_items = review_items[:]
        random.shuffle(shuffled_items)
        shuffled_accounts = self.google_accounts[:]
        random.shuffle(shuffled_accounts)
        total_accounts = len(shuffled_accounts)

        actual_chrome = max(1, min(chrome_count, target, total_accounts))

        def get_next_account():
            """Lay tai khoan tiep theo chua thu qua. Tra ve None neu da du muc tieu,
            het tai khoan, het xu, hoac nguoi dung bam Dung - bao hieu worker nen dung."""
            with lock:
                if (session_reviewed >= target or self._out_of_xu
                        or self._stop_event.is_set() or next_index[0] >= total_accounts):
                    return None
                idx = next_index[0]
                next_index[0] += 1
                account = shuffled_accounts[idx]
                comment, media_paths = shuffled_items[idx % len(shuffled_items)]
                return idx, account, comment, media_paths

        def worker(worker_id):
            nonlocal session_reviewed, session_failed
            while True:
                item = get_next_account()
                if item is None:
                    break
                idx, account, comment, media_paths = item

                email = account.get('email', '')
                password = account.get('password', '')
                profile_name = email_to_profile_name(email)
                profile_dir = os.path.join(PROFILES_DIR, profile_name)
                os.makedirs(profile_dir, exist_ok=True)
                already_logged = self.google_accounts_status.get(email, False)

                with lock:
                    total_done = session_reviewed + session_failed
                    self._log(f"\n--- [Lần {total_done+1}, mục tiêu {target} thành công] Chrome-{worker_id} ---")
                    self._log(f"  TK: {email}")
                    if already_logged:
                        self._log(f"  [Session cũ]")
                    else:
                        self._log(f"  [Đăng nhập mới]")
                    self._log(f"  Nội dung: {comment[:60]}...")
                    if media_paths:
                        self._log(f"  Đính kèm: {len(media_paths)} ảnh/video")

                charge_resp = api_call('/api/tool/review-charge', 'POST',
                                       token=self.token, server_url=self.server_url)
                if 'error' in charge_resp:
                    with lock:
                        self._log(f"  Không đủ xu! Con {charge_resp.get('xu', 0)} xu "
                                   f"(cần {charge_resp.get('cost', REVIEW_COST_XU_DEFAULT)} xu/đánh giá). Dừng lại.", True)
                        session_failed += 1
                        self._out_of_xu = True
                    continue

                review_success = False
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
                        self._log("Lỗi Chrome! Bỏ qua.", True)
                        with lock:
                            session_failed += 1
                        continue

                    if not already_logged:
                        if not bot.login_google(email, password):
                            self._log("Lỗi đăng nhập! Bỏ qua.", True)
                            with lock:
                                session_failed += 1
                            continue
                        self.google_accounts_status[email] = True
                        self._save_config()
                    else:
                        self._log(f"  Kiểm tra session...")
                        if not bot.login_google(email, password):
                            self._log(f"  Session hết hạn, đăng nhập lại...")
                            if not bot.login_google(email, password):
                                self._log("Lỗi đăng nhập!", True)
                                self.google_accounts_status[email] = False
                                with lock:
                                    session_failed += 1
                                continue
                            self.google_accounts_status[email] = True
                            self._save_config()
                        else:
                            self._log(f"  Session hợp lệ!")

                    if not bot.navigate_to_place(url):
                        self._log("Lỗi địa điểm! Bỏ qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.click_write_review_button():
                        self._log("Lỗi nút review! Bỏ qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.select_star_rating(stars):
                        self._log("Lỗi chọn sao! Bỏ qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if not bot.write_comment(comment):
                        self._log("Lỗi viết bình luận! Bỏ qua.", True)
                        with lock:
                            session_failed += 1
                        continue
                    if media_paths:
                        bot.attach_photos(media_paths)  # tuy chon, that bai khong lam dung review
                    if not bot.submit_review():
                        self._log("Lỗi gửi đánh giá! Bỏ qua.", True)
                        with lock:
                            session_failed += 1
                        continue

                    review_success = True
                    with lock:
                        session_reviewed += 1
                        self.review_count += 1
                        self._save_config()
                    api_call('/api/tool/review-done', 'POST',
                             {'place_url': url, 'comment': comment, 'stars': stars},
                             token=self.token, server_url=self.server_url)
                    with lock:
                        self._log(f"  THÀNH CÔNG! [{session_reviewed}/{target}] | Tool: {self.review_count}")

                except Exception as e:
                    self._log(f"  Lỗi: {e}", True)
                    with lock:
                        session_failed += 1
                finally:
                    if not review_success:
                        api_call('/api/tool/review-refund', 'POST',
                                 token=self.token, server_url=self.server_url)
                    if bot:
                        try:
                            bot.close_browser()
                        except:
                            pass

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
            self._log(f"ĐẠT MỤC TIÊU! {session_reviewed}/{target}")
        elif next_index[0] >= total_accounts:
            self._log(f"HẾT TÀI KHOẢN! {session_reviewed} thành công, {session_failed} thất bại / mục tiêu {target}")
        else:
            self._log(f"DỪNG! {session_reviewed}/{target}")
        self._log(f"Tổng tool: {self.review_count} đánh giá")

        self._is_reviewing = False
        self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

        if self._out_of_xu:
            self.root.after(0, lambda: self._prompt_topup(
                "Bạn đã hết xu giữa chừng nên một số đánh giá bị bỏ qua.\n\n"
                "Nạp thêm xu ngay bây giờ?"))

    def _stop_review(self):
        if messagebox.askyesno("Xác nhận", "Dừng tất cả?"):
            self._stop_event.set()
            for bot in self.bots:
                try:
                    bot.close_browser()
                except:
                    pass
            self.bots = []
            self._kill_chrome()
            self._log("Đã dừng!")
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
        tk.Label(header_row, text="Quản lý tài khoản Google", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(side=tk.LEFT)
        make_button(header_row, text="🔄  Kiểm tra lại session", command=self._refresh_all_sessions,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        add_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        add_frame.pack(fill=tk.X, pady=(0, 12))
        add_inner = tk.Frame(add_frame, bg=COLORS['bg2'], padx=14, pady=12)
        add_inner.pack(fill=tk.X)

        tk.Label(add_inner, text="Thêm tài khoản mới", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2']).pack(anchor=tk.W, pady=(0, 8))

        row1 = tk.Frame(add_inner, bg=COLORS['bg2'])
        row1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(row1, text="Email:", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg2'], width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.ga_email = tk.Entry(row1, bg=COLORS['bg3'], fg=COLORS['fg'],
                                 insertbackground=COLORS['fg'], font=self.fonts['body'],
                                 relief=tk.FLAT, width=30)
        self.ga_email.pack(side=tk.LEFT, padx=(0, 16), ipady=4)

        tk.Label(row1, text="Mật khẩu:", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg2'], width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.ga_pass = tk.Entry(row1, bg=COLORS['bg3'], fg=COLORS['fg'],
                                insertbackground=COLORS['fg'], font=self.fonts['body'],
                                relief=tk.FLAT, width=20, show='*')
        self.ga_pass.pack(side=tk.LEFT, ipady=4)

        row1b = tk.Frame(add_inner, bg=COLORS['bg2'])
        row1b.pack(fill=tk.X, pady=(8, 6))

        make_button(row1b, text="Thêm tài khoản", command=self._add_google_account,
                  bg=COLORS['accent'], fg='#000', font=self.fonts['btn'],
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))

        make_button(row1b, text="Thêm nhiều (file)", command=self._import_accounts_file,
                  bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                  relief=tk.FLAT, padx=8, cursor="hand2").pack(side=tk.LEFT)

        self.ga_status = tk.Label(add_inner, text="", font=self.fonts['small'],
                                  fg=COLORS['dim'], bg=COLORS['bg2'])
        self.ga_status.pack(anchor=tk.W)

        list_frame = tk.Frame(page, bg=COLORS['bg2'], highlightbackground=COLORS['border'], highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_inner = tk.Frame(list_frame, bg=COLORS['bg2'], padx=14, pady=10)
        list_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(list_inner, text=f"Danh sách tài khoản ({len(self.google_accounts)})", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 8))

        cols_frame = tk.Frame(list_inner, bg=COLORS['bg4'], padx=10, pady=6)
        cols_frame.pack(fill=tk.X)
        tk.Label(cols_frame, text="#", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=4, anchor=tk.W).pack(side=tk.LEFT)
        tk.Label(cols_frame, text="Email", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=30, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cols_frame, text="Trạng thái", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=16, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cols_frame, text="Profile", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=20, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(cols_frame, text="Thao tác", font=self.fonts['small'], fg=COLORS['dim'],
                 bg=COLORS['bg4'], width=10, anchor=tk.W).pack(side=tk.LEFT)

        self.ga_list_canvas = tk.Canvas(list_inner, bg=COLORS['bg2'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_inner, orient=tk.VERTICAL, command=self.ga_list_canvas.yview)
        self.ga_list_inner = tk.Frame(self.ga_list_canvas, bg=COLORS['bg2'])
        self.ga_list_inner.bind('<Configure>', lambda e: self.ga_list_canvas.configure(scrollregion=self.ga_list_canvas.bbox("all")))
        self.ga_list_canvas.create_window((0, 0), window=self.ga_list_inner, anchor=tk.NW)
        self.ga_list_canvas.configure(yscrollcommand=scrollbar.set)

        self.ga_list_canvas.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_mousewheel(self.ga_list_canvas, self.ga_list_canvas)

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
                del_prof = tk.Label(btn_frame, text="[Xóa profile]", font=self.fonts['tiny'],
                                    fg=COLORS['warning'], bg=row_bg, cursor="hand2")
                del_prof.pack(side=tk.LEFT, padx=(0, 6))
                del_prof.bind('<Button-1>', lambda e, idx=i: self._delete_profile(idx))

            del_acc = tk.Label(btn_frame, text="[Xóa]", font=self.fonts['tiny'],
                               fg=COLORS['error'], bg=row_bg, cursor="hand2")
            del_acc.pack(side=tk.LEFT)
            del_acc.bind('<Button-1>', lambda e, idx=i: self._remove_google_account(idx))

    def _add_google_account(self):
        email = self.ga_email.get().strip()
        password = self.ga_pass.get().strip()
        if not email or not password:
            self.ga_status.config(text="Nhập đầy đủ email và mật khẩu!", fg=COLORS['error'])
            return

        for acc in self.google_accounts:
            if acc.get('email', '').lower() == email.lower():
                self.ga_status.config(text="Tài khoản này đã tồn tại!", fg=COLORS['warning'])
                return

        self.google_accounts.append({'email': email, 'password': password})
        self.google_accounts_status[email] = self._check_profile_session(email)
        self._save_config()
        self._refresh_google_accounts_list()
        self.ga_email.delete(0, tk.END)
        self.ga_pass.delete(0, tk.END)
        self.ga_status.config(text=f"Đã thêm: {email}", fg=COLORS['success'])

    def _remove_google_account(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            if messagebox.askyesno("Xác nhận", f"Xóa tài khoản {email}?"):
                self.google_accounts.pop(index)
                self.google_accounts_status.pop(email, None)
                self._save_config()
                self._refresh_google_accounts_list()
                self.ga_status.config(text=f"Đã xóa: {email}", fg=COLORS['success'])

    def _delete_profile(self, index):
        if 0 <= index < len(self.google_accounts):
            email = self.google_accounts[index].get('email', '')
            profile_name = email_to_profile_name(email)
            profile_path = os.path.join(PROFILES_DIR, profile_name)
            if messagebox.askyesno("Xác nhận", f"Xóa Chrome profile của {email}?\nLần tiếp theo sẽ phải đăng nhập lại."):
                try:
                    import shutil
                    shutil.rmtree(profile_path, ignore_errors=True)
                    self.google_accounts_status[email] = False
                    self._save_config()
                    self._refresh_google_accounts_list()
                    self.ga_status.config(text=f"Đã xóa profile: {email}", fg=COLORS['success'])
                except Exception as e:
                    self.ga_status.config(text=f"Lỗi xóa profile: {e}", fg=COLORS['error'])

    def _refresh_all_sessions(self):
        self.ga_status.config(text="Đang kiểm tra...", fg=COLORS['warning'])
        self.root.update()
        self._check_all_profile_sessions()
        self._save_config()
        self._refresh_google_accounts_list()
        count = sum(1 for v in self.google_accounts_status.values() if v)
        self.ga_status.config(text=f"Kiểm tra xong: {count}/{len(self.google_accounts)} đã đăng nhập",
                              fg=COLORS['success'])

    def _import_accounts_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Chọn file danh sách tài khoản"
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
            self.ga_status.config(text=f"Nhập thành công: {added} mới, {skipped} đã có",
                                  fg=COLORS['success'])
        except Exception as e:
            self.ga_status.config(text=f"Lỗi đọc file: {e}", fg=COLORS['error'])

    # ==================== HISTORY PAGE ====================

    def _build_history_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Lịch sử đánh giá", font=self.fonts['title'],
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

        tk.Label(sec_inner, text=f"Đánh giá gần đây ({len(reviews)} phần tử)",
                 font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg2'], anchor=tk.W).pack(fill=tk.X, pady=(0, 6))

        cols = ("time", "url", "stars", "status")
        tree = ttk.Treeview(sec_inner, columns=cols, show="headings", style="Hist.Treeview", height=12)
        tree.heading("time", text="Thời gian")
        tree.heading("url", text="Địa điểm")
        tree.heading("stars", text="Sao")
        tree.heading("status", text="Trạng thái")
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
            tk.Label(sec_inner, text="Chưa có đánh giá nào", font=self.fonts['small'],
                     fg=COLORS['dim'], bg=COLORS['bg2']).pack(pady=20)

    # ==================== NAP XU PAGE ====================

    def _build_deposit_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Nạp tiền -> Xu", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W)
        tk.Label(page, text="Tỷ lệ: 1.000đ = 1 xu. Xu được cộng tự động sau khi SePay xác nhận chuyển khoản.",
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(2, 12))

        self.deposit_xu_label = tk.Label(page, text="Số xu hiện có: ...", font=self.fonts['body'],
                                          fg=COLORS['accent'], bg=COLORS['bg'])
        self.deposit_xu_label.pack(anchor=tk.W, pady=(0, 10))

        def on_profile(resp):
            if self.current_page != 'deposit' or not self.deposit_xu_label.winfo_exists():
                return
            if 'error' not in resp:
                self.deposit_xu_label.config(text=f"Số xu hiện có: {resp.get('xu', 0):,} \U0001FA99")
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
        tk.Label(row, text="Số tiền (đ):", font=self.fonts['small'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.deposit_amount_entry = tk.Entry(row, bg=COLORS['bg3'], fg=COLORS['fg'],
                                              insertbackground=COLORS['fg'], font=self.fonts['body'],
                                              relief=tk.FLAT, width=16)
        self.deposit_amount_entry.pack(side=tk.LEFT, padx=8, ipady=4)
        self.deposit_amount_entry.insert(0, "50000")

        self.deposit_btn = make_button(row, text="Tạo giao dịch nạp", command=self._start_deposit,
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
            messagebox.showwarning("Cảnh báo", "Số tiền không hợp lệ!")
            return
        if amount < 10000:
            messagebox.showwarning("Cảnh báo", "Số tiền tối thiểu 10.000đ!")
            return

        self.deposit_btn.config(state=tk.DISABLED)
        self.deposit_status_label.config(text="Đang tạo giao dịch...", fg=COLORS['warning'])

        def on_done(resp):
            if not hasattr(self, 'deposit_btn') or not self.deposit_btn.winfo_exists():
                return
            self.deposit_btn.config(state=tk.NORMAL)
            if 'error' in resp:
                self.deposit_status_label.config(text=resp['error'], fg=COLORS['error'])
                return
            self.deposit_status_label.config(text="Đã tạo giao dịch, xem thông tin bên dưới:", fg=COLORS['dim'])
            self._show_deposit_result(resp)

        self._async_api_call('/api/tool/deposit/create', 'POST', {'amount': amount}, on_done=on_done)

    def _show_deposit_result(self, resp):
        for w in self.deposit_result_frame.winfo_children():
            w.destroy()

        inner = tk.Frame(self.deposit_result_frame, bg=COLORS['bg2'], padx=16, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(inner, bg=COLORS['bg2'])
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        self.deposit_qr_label = tk.Label(left, bg=COLORS['bg2'], text="Đang tải QR...",
                                          fg=COLORS['dim'], font=self.fonts['small'])
        self.deposit_qr_label.pack()

        right = tk.Frame(inner, bg=COLORS['bg2'])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        info_lines = [
            ("Ngân hàng", resp.get('bank_code', '-')),
            ("Số tài khoản", resp.get('bank_account', '-')),
            ("Chủ tài khoản", resp.get('account_name', '-')),
            ("Số tiền", f"{resp.get('amount', 0):,}đ ({resp.get('xu', 0):,} xu)"),
            ("Nội dung CK", resp.get('code', '-')),
        ]
        for label, value in info_lines:
            r = tk.Frame(right, bg=COLORS['bg2'])
            r.pack(fill=tk.X, pady=3)
            tk.Label(r, text=f"{label}:", font=self.fonts['small'], fg=COLORS['dim'],
                     bg=COLORS['bg2'], width=14, anchor=tk.W).pack(side=tk.LEFT)
            color = COLORS['accent'] if label == "Nội dung CK" else COLORS['fg']
            tk.Label(r, text=value, font=self.fonts['body'], fg=color,
                     bg=COLORS['bg2'], anchor=tk.W).pack(side=tk.LEFT)

        tk.Label(right, text="Nhập ĐÚNG nội dung chuyển khoản để hệ thống tự động cộng xu!",
                 font=self.fonts['tiny'], fg=COLORS['warning'], bg=COLORS['bg2'],
                 wraplength=340, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))

        self.deposit_wait_label = tk.Label(right, text="⏳ Đang chờ thanh toán...", font=self.fonts['small'],
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
            self.deposit_qr_label.config(text="(Server chưa cấu hình QR)")

        self._poll_deposit_status(resp['tx_id'])

    def _set_deposit_qr_image(self, img_bytes):
        if not hasattr(self, 'deposit_qr_label') or not self.deposit_qr_label.winfo_exists():
            return
        try:
            photo = tk.PhotoImage(data=img_bytes)
            self.deposit_qr_label.config(image=photo, text="")
            self.deposit_qr_label.image = photo  # giu reference tranh bi garbage collect
        except Exception as e:
            self.deposit_qr_label.config(text=f"Lỗi hiện QR: {e}")

    def _set_deposit_qr_error(self, err):
        if hasattr(self, 'deposit_qr_label') and self.deposit_qr_label.winfo_exists():
            self.deposit_qr_label.config(text=f"Không tải được QR\n({err})")

    def _poll_deposit_status(self, tx_id):
        def on_status(resp):
            if not hasattr(self, 'deposit_wait_label') or not self.deposit_wait_label.winfo_exists():
                return  # người dùng đã rời trang, dừng polling

            if 'error' in resp:
                return

            if resp.get('status') == 'completed':
                self.deposit_wait_label.config(
                    text=f"✅ Đã nhận {resp.get('xu_amount', 0):,} xu!", fg=COLORS['success'])
                self._async_api_call('/api/tool/profile', 'GET', on_done=self._on_profile_refresh_after_deposit)
                return

            self.root.after(2000, lambda: self._async_api_call(
                f'/api/tool/deposit/status/{tx_id}', 'GET', on_done=on_status))

        self._async_api_call(f'/api/tool/deposit/status/{tx_id}', 'GET', on_done=on_status)

    def _on_profile_refresh_after_deposit(self, resp):
        if 'error' in resp:
            return
        self.user_info = self.user_info or {}
        self.user_info['xu'] = resp.get('xu', 0)
        self._update_sidebar_stats()
        if hasattr(self, 'deposit_xu_label') and self.deposit_xu_label.winfo_exists():
            self.deposit_xu_label.config(text=f"Số xu hiện có: {resp.get('xu', 0):,} \U0001FA99")

    # ==================== ACCOUNT PAGE ====================

    def _build_account_page(self):
        page = tk.Frame(self.main_area, bg=COLORS['bg'])
        page.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        tk.Label(page, text="Thông tin tài khoản", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 16))

        loading = tk.Label(page, text="Đang tải...", font=self.fonts['small'],
                            fg=COLORS['dim'], bg=COLORS['bg'])
        loading.pack(anchor=tk.W)

        def on_done(resp):
            if self.current_page != 'account' or not page.winfo_exists():
                return  # người dùng đã chuyển trang khác trong lúc chờ
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
                ("Họ tên", resp.get('fullname', '')),
                ("Vai trò", resp.get('role', '')),
                ("Ngày tạo", resp.get('created_at', '')),
                ("Số xu", f"{resp.get('xu', 0):,} \U0001FA99"),
                ("Tổng đánh giá", str(resp.get('total_reviews', 0))),
                ("Đã đánh giá (tool)", str(self.review_count)),
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

        tk.Label(page, text="Thống kê", font=self.fonts['title'],
                 fg=COLORS['fg'], bg=COLORS['bg']).pack(anchor=tk.W, pady=(0, 16))

        loading = tk.Label(page, text="Đang tải...", font=self.fonts['small'],
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
                ("Số xu hiện có", f"{resp.get('xu', 0):,}", COLORS['success']),
                ("Tổng đã đánh giá (server)", str(resp.get('total_reviews', 0)), COLORS['accent']),
                ("Đã đánh giá (tool)", str(self.review_count), COLORS['success']),
                ("Tài khoản GG", str(len(self.google_accounts)), COLORS['warning']),
                ("Session hoạt động", str(sum(1 for v in self.google_accounts_status.values() if v)), COLORS['star']),
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

                tk.Label(sec_inner, text="Đánh giá gần đây", font=self.fonts['heading'],
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
