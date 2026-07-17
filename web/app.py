import os
import sqlite3
import hashlib
import secrets
import time
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, g
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', secrets.token_hex(32))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = os.environ.get(
    'DATABASE_PATH',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
)

# In-memory token store for desktop tool API (token -> user_id)
tool_tokens = {}


# ==================== DATABASE ====================

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            fullname TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            wallet_balance INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_reviews INTEGER DEFAULT 0,
            last_login TIMESTAMP DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT DEFAULT '',
            note TEXT DEFAULT '',
            sepay_id TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            place_url TEXT NOT NULL,
            comment TEXT DEFAULT '',
            stars INTEGER DEFAULT 5,
            cost INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );
    ''')

    cursor = db.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash('admin123')
        db.execute(
            'INSERT INTO users (username, email, password, fullname, role) VALUES (?, ?, ?, ?, ?)',
            ('admin', 'admin@admin.com', admin_pass, 'Administrator', 'admin')
        )

    db.commit()
    db.close()


# ==================== USER MODEL ====================

class User(UserMixin):
    def __init__(self, id, username, email, fullname, phone, wallet_balance, role, is_active, total_reviews, last_login):
        self.id = id
        self.username = username
        self.email = email
        self.fullname = fullname
        self.phone = phone
        self.wallet_balance = wallet_balance
        self.role = role
        self._is_active = is_active
        self.total_reviews = total_reviews
        self.last_login = last_login

    @property
    def is_active(self):
        return bool(self._is_active)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if row:
        return User(
            row['id'], row['username'], row['email'], row['fullname'],
            row['phone'], row['wallet_balance'], row['role'], row['is_active'],
            row['total_reviews'], row['last_login']
        )
    return None


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Không có quyền truy cập!', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ==================== AUTH ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        fullname = request.form.get('fullname', '').strip()
        phone = request.form.get('phone', '').strip()

        if not username or not email or not password:
            flash('Vui lòng nhập đầy đủ thông tin!', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username phải có ít nhất 3 ký tự!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự!', 'error')
            return render_template('register.html')

        if '@' not in email:
            flash('Email không hợp lệ!', 'error')
            return render_template('register.html')

        db = get_db()
        try:
            hashed = generate_password_hash(password)
            db.execute(
                'INSERT INTO users (username, email, password, fullname, phone) VALUES (?, ?, ?, ?, ?)',
                (username, email, hashed, fullname, phone)
            )
            db.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username hoặc email đã tồn tại!', 'error')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Vui lòng nhập đầy đủ thông tin!', 'error')
            return render_template('login.html')

        db = get_db()
        row = db.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, username)
        ).fetchone()

        if row and check_password_hash(row['password'], password):
            if not row['is_active']:
                flash('Tài khoản đã bị khóa! Liên hệ admin.', 'error')
                return render_template('login.html')

            user = User(
                row['id'], row['username'], row['email'], row['fullname'],
                row['phone'], row['wallet_balance'], row['role'], row['is_active'],
                row['total_reviews'], row['last_login']
            )
            login_user(user)
            db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (row['id'],))
            db.commit()
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard'))

        flash('Sai tài khoản hoặc mật khẩu!', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất.', 'success')
    return redirect(url_for('login'))


# ==================== USER DASHBOARD ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    reviews = db.execute(
        'SELECT * FROM reviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
        (current_user.id,)
    ).fetchall()
    api_key = db.execute(
        'SELECT key FROM api_keys WHERE user_id = ? AND is_active = 1 LIMIT 1',
        (current_user.id,)
    ).fetchone()

    return render_template('dashboard.html',
                           reviews=reviews,
                           api_key=api_key['key'] if api_key else None)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    fullname = request.form.get('fullname', '').strip()
    phone = request.form.get('phone', '').strip()
    new_password = request.form.get('new_password', '').strip()

    db = get_db()
    if fullname:
        db.execute('UPDATE users SET fullname = ?, phone = ? WHERE id = ?',
                   (fullname, phone, current_user.id))

    if new_password and len(new_password) >= 6:
        hashed = generate_password_hash(new_password)
        db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, current_user.id))
        flash('Đã cập nhật mật khẩu!', 'success')
    elif new_password and len(new_password) < 6:
        flash('Mật khẩu mới phải ít nhất 6 ký tự!', 'error')

    db.commit()
    flash('Đã cập nhật thông tin!', 'success')
    return redirect(url_for('dashboard'))


# ==================== API CHO BOT ====================

@app.route('/api/bot/verify', methods=['POST'])
def api_verify():
    api_key = request.headers.get('X-API-Key', '')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 401

    db = get_db()
    key_row = db.execute(
        'SELECT * FROM api_keys WHERE key = ? AND is_active = 1', (api_key,)
    ).fetchone()

    if not key_row:
        return jsonify({'error': 'Invalid API key'}), 401

    user = db.execute('SELECT * FROM users WHERE id = ?', (key_row['user_id'],)).fetchone()
    if not user or not user['is_active']:
        return jsonify({'error': 'Account disabled'}), 403

    return jsonify({
        'user_id': user['id'],
        'username': user['username'],
        'total_reviews': user['total_reviews'],
    })


@app.route('/api/bot/deduct', methods=['POST'])
def api_deduct():
    api_key = request.headers.get('X-API-Key', '')
    data = request.get_json()
    if not api_key or not data:
        return jsonify({'error': 'Invalid request'}), 400

    db = get_db()
    key_row = db.execute(
        'SELECT * FROM api_keys WHERE key = ? AND is_active = 1', (api_key,)
    ).fetchone()
    if not key_row:
        return jsonify({'error': 'Invalid API key'}), 401

    user_id = key_row['user_id']
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.execute(
        'INSERT INTO reviews (user_id, place_url, comment, stars, cost, status) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, data.get('place_url', ''), data.get('comment', ''), data.get('stars', 5), 0, 'completed')
    )
    db.execute('UPDATE users SET total_reviews = total_reviews + 1 WHERE id = ?', (user_id,))
    db.commit()

    return jsonify({
        'status': 'success',
        'total_reviews': user['total_reviews'] + 1,
    })


@app.route('/api/bot/balance')
def api_balance():
    api_key = request.headers.get('X-API-Key', '')
    if not api_key:
        return jsonify({'error': 'Missing API key'}), 401

    db = get_db()
    key_row = db.execute(
        'SELECT * FROM api_keys WHERE key = ? AND is_active = 1', (api_key,)
    ).fetchone()
    if not key_row:
        return jsonify({'error': 'Invalid API key'}), 401

    user = db.execute('SELECT * FROM users WHERE id = ?', (key_row['user_id'],)).fetchone()
    return jsonify({
        'total_reviews': user['total_reviews'],
    })


# ==================== API CHO TOOL DESKTOP ====================

@app.route('/api/tool/login', methods=['POST'])
def tool_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Nhap day du thong tin'}), 400

    db = get_db()
    row = db.execute(
        'SELECT * FROM users WHERE username = ? OR email = ?', (username, username)
    ).fetchone()

    if not row or not check_password_hash(row['password'], password):
        return jsonify({'error': 'Sai tai khoan hoac mat khau'}), 401

    if not row['is_active']:
        return jsonify({'error': 'Tai khoan da bi khoa'}), 403

    token = secrets.token_hex(32)
    db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (row['id'],))
    db.commit()
    tool_tokens[token] = row['id']

    return jsonify({
        'token': token,
        'user': {
            'id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'fullname': row['fullname'],
            'role': row['role'],
            'total_reviews': row['total_reviews']
        }
    })


@app.route('/api/tool/register', methods=['POST'])
def tool_register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    fullname = data.get('fullname', '').strip()

    if not username or not email or not password:
        return jsonify({'error': 'Nhap day du thong tin'}), 400
    if len(username) < 3:
        return jsonify({'error': 'Username toi thieu 3 ky tu'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Mat khau toi thieu 6 ky tu'}), 400
    if '@' not in email:
        return jsonify({'error': 'Email khong hop le'}), 400

    db = get_db()
    try:
        hashed = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (username, email, password, fullname) VALUES (?, ?, ?, ?)',
            (username, email, hashed, fullname)
        )
        db.commit()
        return jsonify({'message': 'Dang ky thanh cong'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username hoac email da ton tai'}), 400


def _tool_auth():
    token = request.headers.get('X-Auth-Token', '')
    user_id = tool_tokens.get(token)
    return user_id


@app.route('/api/tool/profile', methods=['GET'])
def tool_profile():
    user_id = _tool_auth()
    if not user_id:
        return jsonify({'error': 'Session expired, vui long dang nhap lai'}), 401

    db = get_db()
    row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not row:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': row['id'],
        'username': row['username'],
        'email': row['email'],
        'fullname': row['fullname'],
        'phone': row['phone'],
        'role': row['role'],
        'total_reviews': row['total_reviews'],
        'is_active': row['is_active'],
        'created_at': row['created_at'],
        'last_login': row['last_login']
    })


@app.route('/api/tool/refresh', methods=['GET'])
def tool_refresh():
    user_id = _tool_auth()
    if not user_id:
        return jsonify({'error': 'Session expired'}), 401

    db = get_db()
    row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not row:
        return jsonify({'error': 'User not found'}), 404

    reviews = db.execute(
        'SELECT * FROM reviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 50', (user_id,)
    ).fetchall()

    return jsonify({
        'total_reviews': row['total_reviews'],
        'history': [dict(r) for r in reviews]
    })


@app.route('/api/tool/review-done', methods=['POST'])
def tool_review_done():
    user_id = _tool_auth()
    if not user_id:
        return jsonify({'error': 'Session expired'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    db = get_db()
    db.execute(
        'INSERT INTO reviews (user_id, place_url, comment, stars, cost, status) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, data.get('place_url', ''), data.get('comment', ''), data.get('stars', 5), 0, 'completed')
    )
    db.execute('UPDATE users SET total_reviews = total_reviews + 1 WHERE id = ?', (user_id,))
    db.commit()

    row = db.execute('SELECT total_reviews FROM users WHERE id = ?', (user_id,)).fetchone()
    return jsonify({
        'status': 'success',
        'total_reviews': row['total_reviews'],
    })


@app.route('/api/tool/deduct', methods=['POST'])
def tool_deduct():
    user_id = _tool_auth()
    if not user_id:
        return jsonify({'error': 'Session expired'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.execute(
        'INSERT INTO reviews (user_id, place_url, comment, stars, cost, status) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, data.get('place_url', ''), data.get('comment', ''), data.get('stars', 5), 0, 'completed')
    )
    db.execute('UPDATE users SET total_reviews = total_reviews + 1 WHERE id = ?', (user_id,))
    db.commit()

    new_user = db.execute('SELECT total_reviews FROM users WHERE id = ?', (user_id,)).fetchone()
    return jsonify({
        'status': 'success',
        'total_reviews': new_user['total_reviews'],
    })


@app.route('/api/tool/history')
def tool_history():
    user_id = _tool_auth()
    if not user_id:
        return jsonify({'error': 'Session expired'}), 401

    db = get_db()
    reviews = db.execute(
        'SELECT * FROM reviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 100', (user_id,)
    ).fetchall()

    return jsonify({
        'reviews': [dict(r) for r in reviews]
    })


# ==================== ADMIN ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()

    search = request.args.get('q', '').strip()
    page = max(1, request.args.get('page', 1, type=int))
    per_page = 20

    if search:
        users = db.execute(
            'SELECT * FROM users WHERE username LIKE ? OR email LIKE ? OR fullname LIKE ? OR phone LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%', per_page, (page - 1) * per_page)
        ).fetchall()
        total_users_q = db.execute(
            'SELECT COUNT(*) FROM users WHERE username LIKE ? OR email LIKE ? OR fullname LIKE ? OR phone LIKE ?',
            (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')
        ).fetchone()[0]
    else:
        users = db.execute(
            'SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (per_page, (page - 1) * per_page)
        ).fetchall()
        total_users_q = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]

    total_pages = max(1, (total_users_q + per_page - 1) // per_page)

    reviews = db.execute(
        'SELECT r.*, u.username FROM reviews r JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC LIMIT 30'
    ).fetchall()

    total_users_count = db.execute('SELECT COUNT(*) FROM users WHERE role = "user"').fetchone()[0]
    total_reviews = db.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]

    return render_template('admin.html',
                           users=users,
                           reviews=reviews,
                           total_users=total_users_count,
                           total_reviews=total_reviews,
                           search=search,
                           page=page,
                           total_pages=total_pages)


@app.route('/admin/topup', methods=['POST'])
@admin_required
def admin_topup():
    user_id = request.form.get('user_id')
    amount = request.form.get('amount')
    note = request.form.get('note', '').strip()
    try:
        user_id = int(user_id)
        amount = int(amount)
    except (ValueError, TypeError):
        flash('Dữ liệu không hợp lệ!', 'error')
        return redirect(url_for('admin_dashboard'))

    if amount <= 0:
        flash('Số tiền phải lớn hơn 0!', 'error')
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User không tồn tại!', 'error')
        return redirect(url_for('admin_dashboard'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute('UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?', (amount, user_id))
    db.execute(
        'INSERT INTO transactions (user_id, amount, type, description, note, status, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (user_id, amount, 'admin_topup', f'Admin nạp {amount:,}đ', note, 'completed', now)
    )
    db.commit()
    flash(f'Đã nạp {amount:,}đ cho {user["username"]}!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit-user', methods=['POST'])
@admin_required
def admin_edit_user():
    user_id = request.form.get('user_id')
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        flash('Dữ liệu không hợp lệ!', 'error')
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User không tồn tại!', 'error')
        return redirect(url_for('admin_dashboard'))

    if user['role'] == 'admin':
        flash('Không thể chỉnh sửa admin!', 'error')
        return redirect(url_for('admin_dashboard'))

    fullname = request.form.get('fullname', user['fullname']).strip()
    email = request.form.get('email', user['email']).strip()
    phone = request.form.get('phone', user['phone']).strip()
    role = request.form.get('role', user['role']).strip()
    balance = request.form.get('balance', user['wallet_balance'])

    try:
        balance = int(balance)
    except (ValueError, TypeError):
        balance = user['wallet_balance']

    if role not in ('user', 'admin'):
        role = 'user'

    try:
        db.execute(
            'UPDATE users SET fullname = ?, email = ?, phone = ?, role = ?, wallet_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (fullname, email, phone, role, balance, user_id)
        )
        db.commit()
        flash(f'Đã cập nhật {user["username"]}!', 'success')
    except sqlite3.IntegrityError:
        flash('Email đã tồn tại!', 'error')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/toggle-user', methods=['POST'])
@admin_required
def admin_toggle_user():
    user_id = request.form.get('user_id')
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    if user['role'] == 'admin':
        return jsonify({'error': 'Cannot toggle admin'}), 400

    new_status = 0 if user['is_active'] else 1
    db.execute('UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_status, user_id))
    db.commit()
    return jsonify({'status': 'ok', 'is_active': new_status})


@app.route('/admin/confirm-tx', methods=['POST'])
@admin_required
def admin_confirm_tx():
    tx_id = request.form.get('tx_id')
    try:
        tx_id = int(tx_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid'}), 400

    db = get_db()
    tx = db.execute(
        'SELECT * FROM transactions WHERE id = ? AND status = "pending"', (tx_id,)
    ).fetchone()
    if not tx:
        return jsonify({'error': 'Transaction not found or already processed'}), 404

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute(
        'UPDATE transactions SET status = "completed", completed_at = ? WHERE id = ?', (now, tx_id)
    )
    db.execute(
        'UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?', (tx['amount'], tx['user_id'])
    )
    db.commit()
    return jsonify({'status': 'ok', 'amount': tx['amount']})


@app.route('/admin/delete-tx', methods=['POST'])
@admin_required
def admin_delete_tx():
    tx_id = request.form.get('tx_id')
    try:
        tx_id = int(tx_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid'}), 400

    db = get_db()
    tx = db.execute('SELECT * FROM transactions WHERE id = ?', (tx_id,)).fetchone()
    if not tx:
        return jsonify({'error': 'Not found'}), 404

    if tx['status'] == 'completed' and tx['type'] == 'deposit':
        db.execute(
            'UPDATE users SET wallet_balance = MAX(0, wallet_balance - ?) WHERE id = ?', (tx['amount'], tx['user_id'])
        )

    db.execute('DELETE FROM transactions WHERE id = ?', (tx_id,))
    db.commit()
    return jsonify({'status': 'ok'})


@app.route('/admin/gen-key', methods=['POST'])
@admin_required
def admin_gen_key():
    user_id = request.form.get('user_id')
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        flash('Dữ liệu không hợp lệ!', 'error')
        return redirect(url_for('admin_dashboard'))

    key = secrets.token_hex(16)
    db = get_db()
    db.execute(
        'INSERT INTO api_keys (user_id, key, name) VALUES (?, ?, ?)',
        (user_id, key, 'Default Key')
    )
    db.commit()
    flash(f'API Key đã tạo cho user #{user_id}: {key}', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete-key', methods=['POST'])
@admin_required
def admin_delete_key():
    key_id = request.form.get('key_id')
    try:
        key_id = int(key_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid'}), 400

    db = get_db()
    db.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
    db.commit()
    return jsonify({'status': 'ok'})


@app.route('/admin/delete-user', methods=['POST'])
@admin_required
def admin_delete_user():
    user_id = request.form.get('user_id')
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return jsonify({'error': 'Not found'}), 404
    if user['role'] == 'admin':
        return jsonify({'error': 'Cannot delete admin'}), 400

    db.execute('DELETE FROM api_keys WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM reviews WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
