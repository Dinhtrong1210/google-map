"""
Google Maps Review Bot - Desktop App
GUI hien dai voi bo dem danh gia
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter import font as tkfont
import threading
import os
import json
import time
import random
from datetime import datetime
from review_bot import GoogleMapsReviewBot, save_config, load_config

VERSION = "1.0.0"
REVIEW_LOG_FILE = "review_log.json"

COLORS = {
    'bg':         '#0f0f1a',
    'bg2':        '#1a1a2e',
    'bg3':        '#252542',
    'bg4':        '#30305a',
    'fg':         '#e8e8f0',
    'dim':        '#7878a0',
    'accent':     '#00d4ff',
    'accent2':    '#7b5cff',
    'success':    '#00e676',
    'error':      '#ff4757',
    'warning':    '#ffc107',
    'star':       '#ffd700',
    'header_bg':  '#0a1628',
    'btn_start':  '#00c853',
    'btn_stop':   '#ff1744',
    'log_bg':     '#050510',
    'log_fg':     '#00ff88',
    'border':     '#3a3a6e',
}


class ReviewBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Google Maps Review Bot v{VERSION}")
        self.root.geometry("900x800")
        self.root.minsize(850, 750)
        self.root.configure(bg=COLORS['bg'])

        self._setup_fonts()

        self.is_running = False
        self.bots = []
        self.review_stats = self._load_review_log()
        self._stop_event = threading.Event()

        self._build_ui()
        self._load_saved_config()
        self._update_stats_display()

    def _setup_fonts(self):
        self.fonts = {
            'title':     tkfont.Font(family="Segoe UI", size=16, weight="bold"),
            'subtitle':  tkfont.Font(family="Segoe UI", size=11),
            'heading':   tkfont.Font(family="Segoe UI", size=10, weight="bold"),
            'body':      tkfont.Font(family="Segoe UI", size=10),
            'small':     tkfont.Font(family="Segoe UI", size=9),
            'tiny':      tkfont.Font(family="Segoe UI", size=8),
            'log':       tkfont.Font(family="Consolas", size=9),
            'stat_num':  tkfont.Font(family="Consolas", size=18, weight="bold"),
            'stat_label':tkfont.Font(family="Segoe UI", size=9),
            'btn':       tkfont.Font(family="Segoe UI", size=10, weight="bold"),
        }

    def _make_section(self, parent, title):
        outer = tk.Frame(parent, bg=COLORS['bg'], bd=0)
        outer.pack(fill=tk.X, padx=12, pady=(4, 2))

        header = tk.Frame(outer, bg=COLORS['bg3'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text=f"  {title}", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg3'], anchor=tk.W).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        body = tk.Frame(outer, bg=COLORS['bg2'], bd=1, relief=tk.FLAT,
                        highlightbackground=COLORS['border'], highlightthickness=1)
        body.pack(fill=tk.X)
        inner = tk.Frame(body, bg=COLORS['bg2'], padx=10, pady=8)
        inner.pack(fill=tk.BOTH, expand=True)
        return inner

    def _build_ui(self):
        canvas = tk.Canvas(self.root, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=COLORS['bg'])

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.bind('<Configure>', lambda e: canvas.itemconfig(self.canvas_window, width=e.width))

        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._build_header()
        self._build_stats_bar()
        self._build_link_section()
        self._build_comment_section()
        self._build_account_section()
        self._build_button_bar()

        bottom = tk.Frame(self.root, bg=COLORS['bg'])
        bottom.pack(side="bottom", fill="both", expand=True)
        self._build_log_section(bottom)
        self._build_status_bar(bottom)

    def _build_header(self):
        header = tk.Frame(self.scroll_frame, bg=COLORS['header_bg'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        left = tk.Frame(header, bg=COLORS['header_bg'])
        left.pack(side=tk.LEFT, fill=tk.Y, padx=16)
        tk.Label(left, text="GOOGLE MAPS REVIEW BOT", font=self.fonts['title'],
                 fg=COLORS['accent'], bg=COLORS['header_bg']).pack(anchor=tk.W, pady=(12, 0))
        tk.Label(left, text=f"v{VERSION}  |  Review automation tool",
                 font=self.fonts['small'], fg=COLORS['dim'], bg=COLORS['header_bg']).pack(anchor=tk.W)

    def _build_stats_bar(self):
        stats_frame = tk.Frame(self.scroll_frame, bg=COLORS['bg2'], height=55,
                               highlightbackground=COLORS['border'], highlightthickness=1)
        stats_frame.pack(fill=tk.X, padx=12, pady=8)
        stats_frame.pack_propagate(False)

        stat_data = [
            ("TONG", 'stat_total'),
            ("THANH CONG", 'stat_success'),
            ("THAT BAI", 'stat_fail'),
            ("HOAN THANH", 'stat_rate'),
        ]

        for i, (label, attr) in enumerate(stat_data):
            col = tk.Frame(stats_frame, bg=COLORS['bg2'])
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=8)

            num_label = tk.Label(col, text="0", font=self.fonts['stat_num'],
                                 fg=COLORS['accent'], bg=COLORS['bg2'])
            num_label.pack()
            setattr(self, attr, num_label)

            tk.Label(col, text=label, font=self.fonts['stat_label'],
                     fg=COLORS['dim'], bg=COLORS['bg2']).pack()

            if i < len(stat_data) - 1:
                sep = tk.Frame(stats_frame, bg=COLORS['border'], width=1)
                sep.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=12)

    def _build_link_section(self):
        s = self._make_section(self.scroll_frame, "LINK & CAI DAT")

        row = tk.Frame(s, bg=COLORS['bg2'])
        row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(row, text="Link Maps:", font=self.fonts['body'],
                 fg=COLORS['fg'], bg=COLORS['bg2'], width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.url_entry = tk.Entry(row, bg=COLORS['bg3'], fg=COLORS['fg'],
                                  insertbackground=COLORS['fg'], font=self.fonts['body'],
                                  relief=tk.FLAT, bd=2)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        row2 = tk.Frame(s, bg=COLORS['bg2'])
        row2.pack(fill=tk.X, pady=(0, 2))

        tk.Label(row2, text="So sao:", font=self.fonts['body'],
                 fg=COLORS['fg'], bg=COLORS['bg2'], width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.star_var = tk.IntVar(value=5)
        for s_val in range(1, 6):
            rb = tk.Radiobutton(row2, text=f"{'*' * s_val}", variable=self.star_var, value=s_val,
                                bg=COLORS['bg2'], fg=COLORS['star'],
                                selectcolor=COLORS['bg3'], activebackground=COLORS['bg2'],
                                activeforeground=COLORS['star'], font=self.fonts['body'])
            rb.pack(side=tk.LEFT, padx=4)

        tk.Label(row2, text="Chrome:", font=self.fonts['body'],
                 fg=COLORS['fg'], bg=COLORS['bg2']).pack(side=tk.LEFT, padx=(20, 0))
        self.chrome_count = tk.IntVar(value=1)
        tk.Spinbox(row2, from_=1, to=10, textvariable=self.chrome_count, width=4,
                   bg=COLORS['bg3'], fg=COLORS['fg'], font=self.fonts['btn'],
                   buttonbackground=COLORS['bg4'], relief=tk.FLAT).pack(side=tk.LEFT, padx=4)

        tk.Label(row2, text="(1-10 cung luc)", font=self.fonts['tiny'],
                 fg=COLORS['dim'], bg=COLORS['bg2']).pack(side=tk.LEFT)

    def _build_comment_section(self):
        s = self._make_section(self.scroll_frame, "NOI DUNG BINH LUAN (moi dong = 1 danh gia)")

        self.comment_text = scrolledtext.ScrolledText(
            s, height=4, bg=COLORS['bg3'], fg=COLORS['fg'],
            insertbackground=COLORS['fg'], font=self.fonts['body'],
            wrap=tk.WORD, relief=tk.FLAT, bd=2)
        self.comment_text.pack(fill=tk.X)

        hint = tk.Frame(s, bg=COLORS['bg2'])
        hint.pack(fill=tk.X, pady=(4, 0))
        self.comment_count_label = tk.Label(hint,
            text="0 dong | 0 tai khoan -> moi Chrome lay 1 dong random",
            font=self.fonts['tiny'], fg=COLORS['dim'], bg=COLORS['bg2'])
        self.comment_count_label.pack(side=tk.LEFT)
        self.comment_text.bind('<KeyRelease>', self._update_comment_count)

    def _build_account_section(self):
        s = self._make_section(self.scroll_frame, "QUAN LY TAI KHOAN")

        add_frame = tk.Frame(s, bg=COLORS['bg2'])
        add_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(add_frame, text="Email:", font=self.fonts['small'],
                 fg=COLORS['fg'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.acc_email = tk.Entry(add_frame, bg=COLORS['bg3'], fg=COLORS['fg'],
                                  insertbackground=COLORS['fg'], font=self.fonts['small'],
                                  width=26, relief=tk.FLAT)
        self.acc_email.pack(side=tk.LEFT, padx=(2, 8), ipady=2)

        tk.Label(add_frame, text="Pass:", font=self.fonts['small'],
                 fg=COLORS['fg'], bg=COLORS['bg2']).pack(side=tk.LEFT)
        self.acc_pass = tk.Entry(add_frame, bg=COLORS['bg3'], fg=COLORS['fg'],
                                 insertbackground=COLORS['fg'], font=self.fonts['small'],
                                 width=20, show='*', relief=tk.FLAT)
        self.acc_pass.pack(side=tk.LEFT, padx=(2, 8), ipady=2)

        btn_add = tk.Button(add_frame, text="+ Them", command=self._add_account,
                            bg=COLORS['btn_start'], fg='white', font=self.fonts['small'],
                            activebackground=COLORS['success'], relief=tk.FLAT, padx=10, cursor="hand2")
        btn_add.pack(side=tk.LEFT, padx=(0, 8))

        btn_import = tk.Button(add_frame, text="Import TXT", command=self._import_accounts,
                               bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['small'],
                               activebackground=COLORS['bg3'], relief=tk.FLAT, padx=8, cursor="hand2")
        btn_import.pack(side=tk.LEFT)

        tree_frame = tk.Frame(s, bg=COLORS['bg2'])
        tree_frame.pack(fill=tk.X, pady=(0, 4))

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Acc.Treeview",
                        background=COLORS['bg3'], foreground=COLORS['fg'],
                        fieldbackground=COLORS['bg3'], font=self.fonts['small'], rowheight=26)
        style.configure("Acc.Treeview.Heading",
                        background=COLORS['bg4'], foreground=COLORS['fg'],
                        font=self.fonts['small'])
        style.map("Acc.Treeview", background=[('selected', COLORS['bg4'])])

        columns = ("email", "password", "status")
        self.account_tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                          style="Acc.Treeview", selectmode="extended", height=4)
        self.account_tree.heading("email", text="Email")
        self.account_tree.heading("password", text="Mat khau")
        self.account_tree.heading("status", text="Trang thai")
        self.account_tree.column("email", width=280)
        self.account_tree.column("password", width=160)
        self.account_tree.column("status", width=120)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        self.account_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_row = tk.Frame(s, bg=COLORS['bg2'])
        bottom_row.pack(fill=tk.X)

        self.acc_count_label = tk.Label(bottom_row, text="So tai khoan: 0",
                                         font=self.fonts['small'], fg=COLORS['warning'], bg=COLORS['bg2'])
        self.acc_count_label.pack(side=tk.LEFT)

        btn_del = tk.Button(bottom_row, text="Xoa da chon", command=self._remove_selected_account,
                            bg=COLORS['error'], fg='white', font=self.fonts['tiny'],
                            relief=tk.FLAT, padx=8, cursor="hand2")
        btn_del.pack(side=tk.RIGHT)

    def _build_button_bar(self):
        btn_frame = tk.Frame(self.scroll_frame, bg=COLORS['bg'], height=50)
        btn_frame.pack(fill=tk.X, padx=12, pady=8)

        btn_save = tk.Button(btn_frame, text="LUU CAU HINH", command=self._save_config,
                             bg=COLORS['bg4'], fg=COLORS['fg'], font=self.fonts['btn'],
                             activebackground=COLORS['bg3'], relief=tk.FLAT, padx=12, pady=6,
                             cursor="hand2")
        btn_save.pack(side=tk.LEFT, padx=3)

        self.btn_run = tk.Button(btn_frame, text=">> BAT DAU <<", command=self._start_review,
                                 bg=COLORS['btn_start'], fg='white', font=self.fonts['btn'],
                                 activebackground=COLORS['success'], relief=tk.FLAT, padx=20, pady=6,
                                 cursor="hand2")
        self.btn_run.pack(side=tk.LEFT, padx=3)

        self.btn_stop = tk.Button(btn_frame, text="DUNG", command=self._stop_review,
                                  bg=COLORS['btn_stop'], fg='white', font=self.fonts['btn'],
                                  activebackground=COLORS['error'], relief=tk.FLAT, padx=20, pady=6,
                                  cursor="hand2", state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=3)

        btn_kill = tk.Button(btn_frame, text="XOA CHROME", command=self._kill_chrome,
                             bg=COLORS['warning'], fg='black', font=self.fonts['small'],
                             relief=tk.FLAT, padx=10, pady=6, cursor="hand2")
        btn_kill.pack(side=tk.RIGHT, padx=3)

        btn_reset = tk.Button(btn_frame, text="RESET COUNTER", command=self._reset_stats,
                              bg=COLORS['dim'], fg='white', font=self.fonts['tiny'],
                              relief=tk.FLAT, padx=8, pady=6, cursor="hand2")
        btn_reset.pack(side=tk.RIGHT, padx=3)

    def _build_log_section(self, parent=None):
        if parent is None:
            parent = self.scroll_frame
        log_frame = tk.Frame(parent, bg=COLORS['bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

        log_header = tk.Frame(log_frame, bg=COLORS['bg3'], height=32)
        log_header.pack(fill=tk.X)
        log_header.pack_propagate(False)
        tk.Label(log_header, text="  LOG OUTPUT", font=self.fonts['heading'],
                 fg=COLORS['accent'], bg=COLORS['bg3']).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=8, bg=COLORS['log_bg'], fg=COLORS['log_fg'],
            insertbackground=COLORS['log_fg'], font=self.fonts['log'],
            wrap=tk.WORD, relief=tk.FLAT, bd=1,
            highlightbackground=COLORS['border'], highlightthickness=1)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

        self.log("San sang! Nhap thong tin va bat dau danh gia.")
        self.log("Moi tai khoan dung profile rieng (giu dang nhap)")

    def _build_status_bar(self, parent=None):
        if parent is None:
            parent = self.scroll_frame
        status = tk.Frame(parent, bg=COLORS['header_bg'], height=28)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)

        self.status_label = tk.Label(status, text="  Ready", font=self.fonts['tiny'],
                                     fg=COLORS['dim'], bg=COLORS['header_bg'], anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.time_label = tk.Label(status, text="", font=self.fonts['tiny'],
                                   fg=COLORS['dim'], bg=COLORS['header_bg'], anchor=tk.E)
        self.time_label.pack(side=tk.RIGHT, padx=12)

    def _update_stats_display(self):
        total = self.review_stats.get('total', 0)
        success = self.review_stats.get('success', 0)
        fail = self.review_stats.get('fail', 0)
        rate = f"{(success / total * 100):.0f}%" if total > 0 else "0%"

        self.stat_total.configure(text=str(total))
        self.stat_success.configure(text=str(success))
        self.stat_fail.configure(text=str(fail))
        self.stat_rate.configure(text=rate)

        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))

    def _load_review_log(self):
        try:
            if os.path.exists(REVIEW_LOG_FILE):
                with open(REVIEW_LOG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'total': 0, 'success': 0, 'fail': 0}

    def _save_review_log(self):
        try:
            with open(REVIEW_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.review_stats, f, indent=2)
        except:
            pass

    def _increment_stats(self, success=True):
        self.review_stats['total'] = self.review_stats.get('total', 0) + 1
        if success:
            self.review_stats['success'] = self.review_stats.get('success', 0) + 1
        else:
            self.review_stats['fail'] = self.review_stats.get('fail', 0) + 1
        self._save_review_log()
        self.root.after(0, self._update_stats_display)

    def _reset_stats(self):
        if messagebox.askyesno("Xac nhan", "Reset bo dem ve 0?"):
            self.review_stats = {'total': 0, 'success': 0, 'fail': 0}
            self._save_review_log()
            self._update_stats_display()
            self.log("Da reset bo dem!")

    def _log_from_thread(self, message, is_error=False):
        self.root.after(0, lambda: self.log(message, is_error))

    def log(self, message, is_error=False):
        tag = "[ERR] " if is_error else ""
        self.log_text.insert(tk.END, f"{tag}{message}\n")
        self.log_text.see(tk.END)

    def _update_comment_count(self, event=None):
        lines = self._get_comment_lines()
        acc_count = len(self.account_tree.get_children())
        n = len(lines)
        if n == 0:
            self.comment_count_label.config(text=f"0 dong | {acc_count} tai khoan -> can nhap noi dung")
        else:
            self.comment_count_label.config(
                text=f"{n} dong | {acc_count} tai khoan -> moi Chrome lay 1 dong (khong trung)")

    def _get_comment_lines(self):
        raw = self.comment_text.get('1.0', tk.END).strip()
        if not raw:
            return []
        return [line.strip() for line in raw.split('\n') if line.strip()]

    def _add_account(self):
        email = self.acc_email.get().strip()
        password = self.acc_pass.get().strip()
        if not email or not password:
            messagebox.showerror("Loi", "Nhap day du email va mat khau!")
            return
        for item in self.account_tree.get_children():
            if self.account_tree.item(item, 'values')[0] == email:
                messagebox.showerror("Loi", "Email da ton tai!")
                return
        self.account_tree.insert("", tk.END, values=(email, password, "Chua chay"))
        self.acc_email.delete(0, tk.END)
        self.acc_pass.delete(0, tk.END)
        self._update_acc_count()
        self.log(f"+ Da them: {email}")

    def _remove_selected_account(self):
        selected = self.account_tree.selection()
        if not selected:
            return
        for item in selected:
            self.account_tree.delete(item)
        self._update_acc_count()

    def _update_acc_count(self):
        count = len(self.account_tree.get_children())
        self.acc_count_label.config(text=f"So tai khoan: {count}")

    def _get_accounts(self):
        accounts = []
        for item in self.account_tree.get_children():
            vals = self.account_tree.item(item, 'values')
            accounts.append({'email': vals[0], 'password': vals[1], 'tree_id': item})
        return accounts

    def _import_accounts(self):
        filepath = filedialog.askopenfilename(
            title="Chon file tai khoan",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            count = 0
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    parts = line.split(':', 1)
                    email = parts[0].strip()
                    password = parts[1].strip()
                    if email and password:
                        exists = any(
                            self.account_tree.item(it, 'values')[0] == email
                            for it in self.account_tree.get_children()
                        )
                        if not exists:
                            self.account_tree.insert("", tk.END, values=(email, password, "Chua chay"))
                            count += 1
            self._update_acc_count()
            self.log(f"+ Da nhap {count} tai khoan tu file")
        except Exception as e:
            messagebox.showerror("Loi", f"Khong the doc file:\n{e}")

    def _save_config(self):
        accounts = []
        for item in self.account_tree.get_children():
            vals = self.account_tree.item(item, 'values')
            accounts.append({'email': vals[0], 'password': vals[1]})
        config = {
            'place_url': self.url_entry.get(),
            'comment': self.comment_text.get('1.0', tk.END).strip(),
            'stars': self.star_var.get(),
            'chrome_count': self.chrome_count.get(),
            'accounts': accounts
        }
        if save_config(config):
            self.log("Da luu cau hinh!")
            messagebox.showinfo("Thanh cong", "Da luu cau hinh!")
        else:
            self.log("Loi luu cau hinh!", True)

    def _load_saved_config(self):
        config = load_config()
        if config:
            self.url_entry.insert(0, config.get('place_url', ''))
            self.comment_text.insert('1.0', config.get('comment', ''))
            if config.get('stars'):
                self.star_var.set(config['stars'])
            if 'chrome_count' in config:
                self.chrome_count.set(config['chrome_count'])
            for acc in config.get('accounts', []):
                if acc.get('email') and acc.get('password'):
                    self.account_tree.insert("", tk.END, values=(acc['email'], acc['password'], "Chua chay"))
            self._update_acc_count()
            self.log("Da load cau hinh tu file")

    def _update_ui_state(self, running):
        self.is_running = running
        if running:
            self.btn_run.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            self.status_label.config(text="  Dang chay...", fg=COLORS['success'])
        else:
            self.btn_run.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.status_label.config(text="  Ready", fg=COLORS['dim'])

    def _update_account_status(self, email, status):
        def _do():
            for item in self.account_tree.get_children():
                vals = self.account_tree.item(item, 'values')
                if vals[0] == email:
                    self.account_tree.item(item, values=(vals[0], vals[1], status))
                    break
        self.root.after(0, _do)

    def _kill_chrome(self):
        os.system('taskkill /f /im chrome.exe 2>nul')
        self.log("Da tat tat ca Chrome!")

    def _get_profile_dir(self, email):
        safe_name = email.replace('@', '_at_').replace('.', '_')
        return os.path.join(os.getcwd(), 'profiles', safe_name)

    def _start_review(self):
        place_url = self.url_entry.get().strip()
        comment_lines = self._get_comment_lines()
        accounts = self._get_accounts()
        chrome_count = self.chrome_count.get()

        if not place_url:
            messagebox.showerror("Loi", "Nhap Link Google Maps!")
            return
        if not comment_lines:
            messagebox.showerror("Loi", "Nhap it nhat 1 noi dung binh luan!")
            return
        for i, line in enumerate(comment_lines):
            if len(line) < 5:
                messagebox.showerror("Loi", f"Dong {i+1} qua ngan (toi thieu 5 ky tu):\n{line}")
                return
        if not accounts:
            messagebox.showerror("Loi", "Nhap it nhat 1 tai khoan!")
            return
        if chrome_count > len(accounts):
            chrome_count = len(accounts)
            self.chrome_count.set(chrome_count)

        if not messagebox.askyesno("Xac nhan",
                f"Se chay {chrome_count} Chrome voi {len(accounts)} tai khoan.\n"
                f"{len(comment_lines)} noi dung binh luan (moi Chrome lay 1 dong ngau nhien).\n"
                f"Tong da danh gia: {self.review_stats['total']} | "
                f"Thanh cong: {self.review_stats['success']}\n\n"
                f"Bam OK de bat dau"):
            return

        self.log_text.delete('1.0', tk.END)
        self.log(f"BAT DAU: {chrome_count} Chrome | {len(accounts)} tai khoan")
        self.log(f"Noi dung: {len(comment_lines)} dong (moi Chrome lay 1 dong ngau nhien)")
        self.log("=" * 50)
        self._stop_event.clear()
        self._update_ui_state(True)

        thread = threading.Thread(target=self._run_multi_review,
                                  args=(accounts, place_url, comment_lines,
                                        self.star_var.get(), chrome_count))
        thread.daemon = True
        thread.start()

    def _run_multi_review(self, accounts, place_url, comment_lines, stars, chrome_count):
        try:
            self.bots = []
            total = len(accounts)

            shuffled_comments = comment_lines[:]
            random.shuffle(shuffled_comments)
            self._log_from_thread(f"Da tron {len(shuffled_comments)} noi dung binh luan")

            comment_idx = 0

            for i in range(0, total, chrome_count):
                if self._stop_event.is_set():
                    self._log_from_thread("Dung theo yeu cau!")
                    break

                batch = accounts[i:i + chrome_count]
                threads = []

                for j, acc in enumerate(batch):
                    if self._stop_event.is_set():
                        break

                    idx = i + j + 1
                    current_comment = shuffled_comments[comment_idx % len(shuffled_comments)]
                    comment_idx += 1

                    self._log_from_thread(f"\n--- Chrome {idx}/{total}: {acc['email']} ---")
                    self._log_from_thread(f"  Noi dung: {current_comment[:60]}...")
                    self._update_account_status(acc['email'], "Dang chay...")

                    user_data = self._get_profile_dir(acc['email'])
                    os.makedirs(user_data, exist_ok=True)

                    def run_one(account, profile_dir, chrome_idx, review_comment):
                        bot = None
                        try:
                            bot = GoogleMapsReviewBot(
                                headless=False,
                                user_data_dir=profile_dir,
                                debug_port=9222 + chrome_idx
                            )
                            bot.set_status_callback(self._log_from_thread)
                            self.bots.append(bot)

                            if self._stop_event.is_set():
                                return False

                            if not bot.start_browser():
                                self._update_account_status(account['email'], "LOI Chrome")
                                self._increment_stats(success=False)
                                return False

                            if not bot.login_google(account['email'], account['password']):
                                self._update_account_status(account['email'], "LOI Dang nhap")
                                self._increment_stats(success=False)
                                return False

                            if not bot.navigate_to_place(place_url):
                                self._update_account_status(account['email'], "LOI Dia diem")
                                self._increment_stats(success=False)
                                return False

                            if not bot.click_write_review_button():
                                self._update_account_status(account['email'], "LOI Nut review")
                                self._increment_stats(success=False)
                                return False

                            if not bot.select_star_rating(stars):
                                self._update_account_status(account['email'], "LOI Sao")
                                self._increment_stats(success=False)
                                return False

                            if not bot.write_comment(review_comment):
                                self._update_account_status(account['email'], "LOI Binh luan")
                                self._increment_stats(success=False)
                                return False

                            if not bot.submit_review():
                                self._update_account_status(account['email'], "LOI Gui")
                                self._increment_stats(success=False)
                                return False

                            self._update_account_status(account['email'], "THANH CONG")
                            self._increment_stats(success=True)
                            return True

                        except Exception as e:
                            self._update_account_status(account['email'], f"LOI: {str(e)[:20]}")
                            self._increment_stats(success=False)
                            return False
                        finally:
                            if bot:
                                try:
                                    bot.close_browser()
                                except:
                                    pass

                    t = threading.Thread(target=run_one, args=(acc, user_data, j, current_comment))
                    threads.append(t)
                    t.start()
                    if j < len(batch) - 1:
                        time.sleep(3)

                for t in threads:
                    t.join()

                if i + chrome_count < total and not self._stop_event.is_set():
                    self._log_from_thread(f"\nXong batch {i // chrome_count + 1}, chuan bi batch tiep theo...")
                    time.sleep(5)

            self._log_from_thread("\n" + "=" * 50)
            self._log_from_thread(f"HOAN TAT! Tong: {self.review_stats['total']} | "
                                  f"Thanh cong: {self.review_stats['success']} | "
                                  f"That bai: {self.review_stats['fail']}")

        except Exception as e:
            self._log_from_thread(f"Loi chinh: {e}", True)
        finally:
            self.root.after(0, lambda: self._update_ui_state(False))

    def _stop_review(self):
        if messagebox.askyesno("Xac nhan", "Dung tat ca Chrome?"):
            self._stop_event.set()
            self.log("Dang dung...")
            for bot in self.bots:
                try:
                    bot.close_browser()
                except:
                    pass
            self.bots = []
            self._kill_chrome()
            self._update_ui_state(False)
            self.log("Da dung!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewBotApp(root)
    root.mainloop()
