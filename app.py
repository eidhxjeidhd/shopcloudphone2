import os
import time
import threading
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Dữ liệu mẫu lưu trữ trong bộ nhớ tạm (hoặc kết nối Database tùy ý sau này)
# Cấu trúc: { "email@gmail.com": [ {"id": 1, "url": "...", "duration": 10, "unit": "seconds"} ] }
USER_LINKS = {}
RUNNING_STATUS = {}  # Trạng thái chạy của từng user

# Giao diện HTML + CSS trực quan, tối ưu cho cả điện thoại
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-Surf Link Tool</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 600px; width: 100%; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; }
        input, select, button { width: 100%; padding: 12px; margin-top: 10px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #0284c7; font-weight: bold; border: none; cursor: pointer; }
        button:hover { background: #0369a1; }
        .btn-danger { background: #dc2626; }
        .btn-danger:hover { background: #b91c1c; }
        .btn-success { background: #16a34a; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #334155; text-align: left; }
        th { color: #94a3b8; }
        .badge { background: #334155; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.get('user') %}
        <div class="card" style="text-align: center;">
            <h2>🔐 Đăng Nhập Hệ Thống</h2>
            <p style="color: #94a3b8;">Nhập tài khoản Gmail của bạn để bắt đầu quản lý danh sách link.</p>
            <form method="POST" action="/login">
                <input type="email" name="email" placeholder="Nhập địa chỉ Gmail của bạn..." required>
                <button type="submit">Đăng Nhập Ngay</button>
            </form>
        </div>
        {% else %}
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>👤 Chào, <b>{{ session.get('user') }}</b></span>
                <a href="/logout" style="color: #f87171; text-decoration: none; font-size: 14px;">Đăng xuất</a>
            </div>
        </div>

        <div class="card">
            <h2>➕ Thêm Link Mới</h2>
            <form method="POST" action="/add_link">
                <label>Đường dẫn (URL):</label>
                <input type="url" name="url" placeholder="https://example.com" required>
                
                <label>Thời gian truy cập:</label>
                <div style="display: flex; gap: 10px;">
                    <input type="number" name="time_val" value="10" min="1" required style="flex: 2;">
                    <select name="time_unit" style="flex: 1;">
                        <option value="seconds">Giây</option>
                        <option value="minutes">Phút</option>
                    </select>
                </div>
                <button type="submit" class="btn-success">Thêm Vào Danh Sách</button>
            </form>
        </div>

        <div class="card">
            <h3>⚙️ Trạng Thái & Điều Khiển</h3>
            <p>Trạng thái chạy: <b>{{ status }}</b></p>
            <div style="display: flex; gap: 10px;">
                <form method="POST" action="/start_surf" style="flex: 1;"><button type="submit" class="btn-success">Bắt Đầu Chạy</button></form>
                <form method="POST" action="/stop_surf" style="flex: 1;"><button type="submit" class="btn-danger">Dừng Lại</button></form>
            </div>
        </div>

        <div class="card">
            <h3>📋 Danh Sách Link Đã Thêm ({{ links|length }})</h3>
            {% if links %}
            <table>
                <tr>
                    <th>URL</th>
                    <th>Thời gian</th>
                    <th>Hành động</th>
                </tr>
                {% for l in links %}
                <tr>
                    <td style="word-break: break-all; max-width: 200px;">{{ l.url }}</td>
                    <td><span class="badge">{{ l.duration }} {{ 'giây' if l.unit == 'seconds' else 'phút' }}</span></td>
                    <td><a href="/delete_link/{{ l.id }}" style="color: #f87171; text-decoration: none;">Xóa</a></td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p style="color: #94a3b8; text-align: center;">Chưa có link nào được thêm.</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    user = session.get('user')
    links = USER_LINKS.get(user, []) if user else []
    status = RUNNING_STATUS.get(user, "Đang dừng")
    return render_template_string(HTML_TEMPLATE, links=links, status=status)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    if email and "@gmail.com" in email:
        session['user'] = email
        if email not in USER_LINKS:
            USER_LINKS[email] = []
        if email not in RUNNING_STATUS:
            RUNNING_STATUS[email] = "Đang dừng"
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/add_link', methods=['POST'])
def add_link():
    user = session.get('user')
    if not user:
        return redirect(url_for('index'))
    
    url = request.form.get('url')
    time_val = int(request.form.get('time_val', 10))
    time_unit = request.form.get('time_unit', 'seconds')
    
    new_item = {
        "id": len(USER_LINKS[user]) + 1,
        "url": url,
        "duration": time_val,
        "unit": time_unit
    }
    USER_LINKS[user].append(new_item)
    return redirect(url_for('index'))

@app.route('/delete_link/<int:link_id>')
def delete_link(link_id):
    user = session.get('user')
    if user and user in USER_LINKS:
        USER_LINKS[user] = [l for l in USER_LINKS[user] if l['id'] != link_id]
    return redirect(url_for('index'))

def background_worker(user):
    """Tiến trình xử lý tuần tự từng link theo đúng thời gian tùy chỉnh"""
    while RUNNING_STATUS.get(user) == "Đang chạy":
        links = USER_LINKS.get(user, [])
        if not links:
            RUNNING_STATUS[user] = "Đang dừng (Hết link)"
            break
        
        # Xử lý lần lượt từng link một trong hàng đợi
        for link in list(links):
            if RUNNING_STATUS.get(user) != "Đang chạy":
                break
            
            # Tính thời gian chờ (quy đổi ra giây)
            duration = link['duration']
            if link['unit'] == 'minutes':
                duration *= 60
                
            # Cập nhật trạng thái đang xử lý link nào
            RUNNING_STATUS[user] = f"Đang truy cập: {link['url']} (Chờ {link['duration']} {link['unit']})"
            
            # Thực hiện delay đúng số giây đã chọn cho link đó
            time.sleep(duration)
            
    if RUNNING_STATUS.get(user) != "Đang dừng (Hết link)":
        RUNNING_STATUS[user] = "Đang dừng"

@app.route('/start_surf', methods=['POST'])
def start_surf():
    user = session.get('user')
    if user and USER_LINKS.get(user):
        if RUNNING_STATUS.get(user) != "Đang chạy":
            RUNNING_STATUS[user] = "Đang chạy"
            threading.Thread(target=background_worker, args=(user,), daemon=True).start()
    return redirect(url_for('index'))

@app.route('/stop_surf', methods=['POST'])
def stop_surf():
    user = session.get('user')
    if user:
        RUNNING_STATUS[user] = "Đang dừng"
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
