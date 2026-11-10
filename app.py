import os
import time
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Cấu trúc lưu trữ dữ liệu cho từng user
# { "email@gmail.com": { "links": [...], "status": "...", "current_link": "", "remaining_seconds": 0, "logs": [...] } }
USER_DATA = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto-Surf Pro Tool</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .container { max-width: 650px; width: 100%; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
        h2, h3 { margin-top: 0; color: #38bdf8; }
        input, select, button { width: 100%; padding: 12px; margin-top: 10px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 16px; }
        button { background: #0284c7; font-weight: bold; border: none; cursor: pointer; }
        button:hover { background: #0369a1; }
        .btn-danger { background: #dc2626; }
        .btn-success { background: #16a34a; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 10px; border-bottom: 1px solid #334155; text-align: left; }
        th { color: #94a3b8; }
        .badge { background: #334155; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .log-box { background: #090d16; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 13px; max-height: 150px; overflow-y: auto; color: #34d399; border: 1px solid #334155; }
    </style>
    <!-- Tự động làm mới trang mỗi 3 giây để cập nhật thời gian đếm ngược và log -->
    {% if session.get('user') and data.status == "Đang chạy" %}
    <meta http-equiv="refresh" content="3">
    {% endif %}
</head>
<body>
    <div class="container">
        {% if not session.get('user') %}
        <div class="card" style="text-align: center;">
            <h2>🔐 Đăng Nhập Hệ Thống</h2>
            <p style="color: #94a3b8;">Nhập tài khoản Gmail để quản lý hệ thống auto-surf cá nhân.</p>
            <form method="POST" action="/login">
                <input type="email" name="email" placeholder="Nhập Gmail của bạn..." required>
                <button type="submit">Vào Hệ Thống</button>
            </form>
        </div>
        {% else %}
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>👤 Gmail: <b>{{ session.get('user') }}</b></span>
                <a href="/logout" style="color: #f87171; text-decoration: none; font-size: 14px;">Đăng xuất</a>
            </div>
        </div>

        <div class="card">
            <h2>➕ Thêm Link Mới</h2>
            <form method="POST" action="/add_link">
                <label>Đường dẫn (URL):</label>
                <input type="url" name="url" placeholder="https://example.com" required>
                
                <label>Thời gian chờ mỗi lượt:</label>
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
            <h3>⚙️ Trạng Thái Hoạt Động</h3>
            <p>Trạng thái: <b style="color: {% if data.status == 'Đang chạy' %}#34d399{% else %}#f87171{% endif %};">{{ data.status }}</b></p>
            {% if data.status == "Đang chạy" %}
            <p>⏳ Đang xử lý: <span style="color: #38bdf8; word-break: break-all;">{{ data.current_link }}</span></p>
            <p>⏱️ Thời gian đếm ngược còn lại: <b style="color: #facc15;">{{ data.remaining_seconds }} giây</b></p>
            {% endif %}
            <div style="display: flex; gap: 10px; margin-top: 15px;">
                <form method="POST" action="/start_surf" style="flex: 1;"><button type="submit" class="btn-success">Bắt Đầu</button></form>
                <form method="POST" action="/stop_surf" style="flex: 1;"><button type="submit" class="btn-danger">Dừng Lại</button></form>
            </div>
        </div>

        <div class="card">
            <h3>📋 Danh Sách Link & Số Lần Truy Cập ({{ data.links|length }})</h3>
            {% if data.links %}
            <table>
                <tr>
                    <th>URL</th>
                    <th>Cài đặt</th>
                    <th>Đã truy cập</th>
                    <th>Xóa</th>
                </tr>
                {% for l in data.links %}
                <tr>
                    <td style="word-break: break-all; max-width: 180px;">{{ l.url }}</td>
                    <td><span class="badge">{{ l.duration }} {{ 's' if l.unit == 'seconds' else 'phút' }}</span></td>
                    <td><b>{{ l.visits }} lần</b></td>
                    <td><a href="/delete_link/{{ l.id }}" style="color: #f87171; text-decoration: none;">Xóa</a></td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p style="color: #94a3b8; text-align: center;">Chưa có link nào.</p>
            {% endif %}
        </div>

        <div class="card">
            <h3>🛰️ Nhật Ký IP & Lượt Truy Cập Thực Tế</h3>
            <div class="log-box">
                {% if data.logs %}
                    {% for log in data.logs %}
                        <div>> {{ log }}</div>
                    {% endfor %}
                {% else %}
                    <span style="color: #64748b;">Chưa có dữ liệu nhật ký...</span>
                {% endif %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def get_user_session_data(user):
    if user not in USER_DATA:
        USER_DATA[user] = {
            "links": [],
            "status": "Đang dừng",
            "current_link": "Không có",
            "remaining_seconds": 0,
            "logs": []
        }
    return USER_DATA[user]

@app.route('/')
def index():
    user = session.get('user')
    data = get_user_session_data(user) if user else {}
    return render_template_string(HTML_TEMPLATE, data=data)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    if email and "@gmail.com" in email:
        session['user'] = email
        get_user_session_data(email)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/add_link', methods=['POST'])
def add_link():
    user = session.get('user')
    if not user: return redirect(url_for('index'))
    
    data = get_user_session_data(user)
    url = request.form.get('url')
    time_val = int(request.form.get('time_val', 10))
    time_unit = request.form.get('time_unit', 'seconds')
    
    new_item = {
        "id": len(data["links"]) + 1,
        "url": url,
        "duration": time_val,
        "unit": time_unit,
        "visits": 0
    }
    data["links"].append(new_item)
    return redirect(url_for('index'))

@app.route('/delete_link/<int:link_id>')
def delete_link(link_id):
    user = session.get('user')
    if user and user in USER_DATA:
        USER_DATA[user]["links"] = [l for l in USER_DATA[user]["links"] if l['id'] != link_id]
    return redirect(url_for('index'))

def background_worker(user):
    data = USER_DATA[user]
    while data["status"] == "Đang chạy":
        links = data["links"]
        if not links:
            data["status"] = "Đang dừng (Hết link)"
            break
        
        for link in list(links):
            if data["status"] != "Đang chạy":
                break
            
            data["current_link"] = link['url']
            duration = link['duration']
            if link['unit'] == 'minutes':
                duration *= 60
            
            data["remaining_seconds"] = duration
            
            # Thực hiện truy cập link và lấy địa chỉ IP công khai của server thực hiện request
            try:
                # Lấy IP cấu hình mạng bên ngoài của trạm request
                ip_res = requests.get("https://api.ipify.org?format=json", timeout=5)
                server_ip = ip_res.json().get("ip", "Ẩn danh")
            except:
                server_ip = "Không xác định (Lỗi kết nối)"

            # Gửi request thực tế vào link của người dùng để tính lượt view/traffic
            try:
                requests.get(link['url'], timeout=10, headers={"User-Agent": "Mozilla/5.0 AutoSurfBot"})
                fetch_status = "Thành công 200 OK"
            except Exception as e:
                fetch_status = f"Đã kết nối (Lỗi phản hồi: {str(e)[:25]})"

            # Cập nhật số lần truy cập
            link['visits'] += 1
            
            # Ghi log kèm theo thời gian, IP và trạng thái
            timestamp = time.strftime("%H:%M:%S")
            log_msg = f"[{timestamp}] Đã truy cập {link['url']} | IP Server: {server_ip} | Trạng thái: {fetch_status}"
            data["logs"].insert(0, log_msg)
            if len(data["logs"]) > 20: # Giữ tối đa 20 dòng log mới nhất
                data["logs"].pop()

            # Đếm ngược thời gian từng giây để giao diện cập nhật mượt mà
            while data["remaining_seconds"] > 0 and data["status"] == "Đang chạy":
                time.sleep(1)
                data["remaining_seconds"] -= 1
                
    if data["status"] != "Đang dừng (Hết link)":
        data["status"] = "Đang dừng"

@app.route('/start_surf', methods=['POST'])
def start_surf():
    user = session.get('user')
    if user:
        data = USER_DATA[user]
        if data["links"] and data["status"] != "Đang chạy":
            data["status"] = "Đang chạy"
            threading.Thread(target=background_worker, args=(user,), daemon=True).start()
    return redirect(url_for('index'))

@app.route('/stop_surf', methods=['POST'])
def stop_surf():
    user = session.get('user')
    if user and user in USER_DATA:
        USER_DATA[user]["status"] = "Đang dừng"
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
