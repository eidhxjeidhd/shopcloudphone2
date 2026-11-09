import os
import time
import json
import random
import string
from flask import Flask, render_template_string, jsonify, request, session, redirect

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

DB_FILE = "cloud_phones_db.json"
ADMIN_PASSWORD = "admin_gagaming_123"

def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "phones": [
                {"id": "CP-01", "name": "Gà Gaming Cloud 01", "model": "ROG Phone 6 Pro", "android": "Android 13", "ram": "16GB", "status": "Online", "ip": "103.x.x.15"},
                {"id": "CP-02", "name": "Gà Gaming Cloud 02", "model": "Red Magic 8S", "android": "Android 14", "ram": "18GB", "status": "Online", "ip": "103.x.x.22"}
            ],
            "keys_kho": [],      # Kho chứa key chưa dùng
            "keys_active": []    # Key đang hoạt động
        }
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"phones": [], "keys_kho": [], "keys_active": []}
            if "keys_kho" not in data: data["keys_kho"] = []
            if "keys_active" not in data: data["keys_active"] = []
            return data
    except Exception:
        return {"phones": [], "keys_kho": [], "keys_active": []}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Lỗi lưu DB:", e)

# --- API KIỂM TRA KEY CHO GAME (ĐÃ SỬA LOGIC TỰ ĐỘNG CHUYỂN TỪ KHO SANG ACTIVE) ---
@app.route('/api/check-key', methods=['GET'])
def api_check_key():
    key_input = request.args.get('key', '').strip()
    if not key_input:
        return jsonify({"success": False, "message": "Vui lòng nhập key!"})
    
    db = load_db()
    
    # 1. Kiểm tra xem key đã nằm trong danh sách đang hoạt động chưa
    for k in db.get("keys_active", []):
        if k["key"] == key_input:
            # Kiểm tra thời hạn (nếu hết hạn thì xóa)
            if time.time() > k["expire_time"]:
                db["keys_active"].remove(k)
                save_db(db)
                return jsonify({"success": False, "message": "Key đã hết hạn sử dụng!"})
            return jsonify({"success": True, "message": "Key hợp lệ!"})
            
    # 2. Nếu chưa hoạt động, tìm trong KHO
    for k in db.get("keys_kho", []):
        if k["key"] == key_input:
            # Lấy ra khỏi kho
            db["keys_kho"].remove(k)
            
            # Tính thời hạn (Ví dụ: 1 ngày = 86400 giây)
            duration = k.get("duration_seconds", 86400) 
            expire_time = time.time() + duration
            
            # Đưa sang danh sách Active
            active_item = {
                "key": key_input,
                "expire_time": expire_time,
                "created_at": time.time()
            }
            db["keys_active"].append(active_item)
            save_db(db)
            
            return jsonify({"success": True, "message": "Kích hoạt key thành công!"})
            
    return jsonify({"success": False, "message": "Key sai hoặc không tồn tại trong hệ thống!"})

# --- TRANG CHỦ ---
@app.route('/')
def home():
    db = load_db()
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Gà Gaming - Hệ Thống</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 400px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
                a { color: #38bdf8; text-decoration: none; display: block; margin-top: 15px; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🎮 Gà Gaming Hub</h2>
                <p style="color: #94a3b8; font-size: 13px;">Hệ thống xác thực key và quản lý dịch vụ hoạt động ổn định.</p>
                <a href="/admin">⚙️ Vào Trang Quản Trị (Admin)</a>
            </div>
        </body>
        </html>
    """)

# --- TRANG ADMIN QUẢN LÝ KHO KEY ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    db = load_db()
    message = ""
    
    if request.method == 'POST' and 'password' in request.form and 'keys_input' not in request.form:
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect('/admin')
        else:
            message = "❌ Mật khẩu Admin không chính xác!"

    if not session.get('admin_logged'):
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Đăng Nhập Admin</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 350px; text-align: center; }
                input { width: 100%; padding: 10px; margin-top: 10px; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
                button { background: #3b82f6; color: white; border: none; padding: 10px; width: 100%; border-radius: 6px; margin-top: 15px; cursor: pointer; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🔐 Đăng Nhập Admin</h2>
                <form method="POST">
                    <input type="password" name="password" placeholder="Mật khẩu..." required>
                    <button type="submit">Đăng Nhập</button>
                </form>
            </div>
        </body>
        </html>
        """)

    if request.method == 'POST':
        if 'keys_input' in request.form:
            raw_keys = request.form.get('keys_input', '')
            days = int(request.form.get('days', 1))
            duration_sec = days * 86400
            
            added_count = 0
            for line in raw_keys.split('\n'):
                k = line.strip()
                if k:
                    db["keys_kho"].append({"key": k, "duration_seconds": duration_sec})
                    added_count += 1
            save_db(db)
            message = f"✅ Đã nạp thành công {added_count} key vào kho!"

    kho_count = len(db.get("keys_kho", []))
    active_count = len(db.get("keys_active", []))

    active_html = ""
    for act in db.get("keys_active", []):
        time_left = max(0, int(act["expire_time"] - time.time()))
        hours_left = time_left // 3600
        active_html += f"""
        <div style="background: #0b0f19; padding: 8px; border-radius: 6px; margin-top: 5px; font-size: 11px; display: flex; justify-content: space-between;">
            <span style="color: #4ade80;">🔑 {act['key']}</span>
            <span style="color: #94a3b8;">Còn lại: {hours_left} giờ</span>
        </div>
        """

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Quản Lý Kho Key</title>
        <style>
            body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .card {{ background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; }}
            textarea, select {{ width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; margin-top: 8px; margin-bottom: 12px; }}
            button {{ background: #22c55e; color: white; border: none; padding: 10px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; }}
            .stats {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
            .stat-box {{ background: #0b0f19; padding: 10px; border-radius: 8px; width: 48%; text-align: center; border: 1px solid #334155; font-size: 13px; }}
            .logout {{ background: #ef4444; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>⚙️ Quản Lý Kho Key</h2>
            
            <div class="stats">
                <div class="stat-box">📦 Kho: <b style="color: #38bdf8;">{kho_count} Key</b></div>
                <div class="stat-box">⚡ Hoạt động: <b style="color: #4ade80;">{active_count} Key</b></div>
            </div>

            <form method="POST">
                <label style="font-size: 12px; color: #38bdf8; font-weight: bold;">Thời hạn key:</label>
                <select name="days">
                    <option value="1">1 Ngày</option>
                    <option value="7">7 Ngày</option>
                    <option value="30">30 Ngày</option>
                </select>

                <label style="font-size: 12px; color: #38bdf8; font-weight: bold;">Danh sách Key (mỗi key một dòng):</label>
                <textarea name="keys_input" rows="4" placeholder="GA-KEY-01&#10;GA-KEY-02"></textarea>
                
                <button type="submit">➕ Thêm Key Vào Kho</button>
            </form>

            <div style="margin-top: 20px;">
                <label style="font-size: 12px; color: #38bdf8; font-weight: bold;">📋 Key Đang Hoạt Động:</label>
                <div style="max-height: 120px; overflow-y: auto; margin-top: 5px;">
                    {active_html if active_html else '<div style="color: #64748b; font-size: 11px; text-align: center; padding: 10px;">Chưa có key nào đang kích hoạt.</div>'}
                </div>
            </div>

            <div style="color: #4ade80; font-size: 12px; text-align: center; margin-top: 10px; font-weight: bold;">{message}</div>

            <form action="/admin/logout" method="POST">
                <button type="submit" class="logout">Đăng Xuất Admin</button>
            </form>
        </div>
    </body>
    </html>
    """, message=message, kho_count=kho_count, active_count=active_count, active_html=active_html)

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged', None)
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
