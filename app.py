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
        # Khởi tạo mặc định vài con Cloud Phone mẫu cho sướng
        default_data = {
            "phones": [
                {"id": "CP-01", "name": "Gà Gaming Cloud 01", "model": "ROG Phone 6 Pro", "android": "Android 13", "ram": "16GB", "status": "Online", "ip": "103.x.x.15"},
                {"id": "CP-02", "name": "Gà Gaming Cloud 02", "model": "Red Magic 8S", "android": "Android 14", "ram": "18GB", "status": "Online", "ip": "103.x.x.22"}
            ],
            "current_link": ""
        }
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "phones" not in data:
                return {"phones": [], "current_link": ""}
            return data
    except Exception:
        return {"phones": [], "current_link": ""}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Lỗi lưu DB:", e)

# --- 1. GIAO DIỆN CHÍNH CLOUD PHONE (DASHBOARD CHO NGƯỜI DÙNG) ---
@app.route('/')
def home():
    try:
        db = load_db()
        phones = db.get("phones", [])
        
        phones_html = ""
        for p in phones:
            status_color = "#22c55e" if p['status'] == "Online" else "#ef4444"
            phones_html += f"""
            <div style="background: #0b0f19; padding: 15px; border-radius: 12px; margin-bottom: 12px; border: 1px solid #334155; text-align: left;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #38bdf8; font-weight: bold; font-size: 14px;">💻 {p['name']} ({p['id']})</span>
                    <span style="background: {status_color}; color: white; padding: 3px 8px; border-radius: 20px; font-size: 10px; font-weight: bold;">{p['status']}</span>
                </div>
                <div style="margin-top: 8px; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                    📱 Thiết bị: <b style="color: #f8fafc;">{p['model']}</b><br>
                    🤖 Hệ điều hành: <b style="color: #f8fafc;">{p['android']}</b> | 🧠 RAM: <b style="color: #f8fafc;">{p['ram']}</b><br>
                    🌐 IP Cloud: <b style="color: #4ade80;">{p['ip']}</b>
                </div>
                <button onclick="connectCloud('{p['id']}')" style="background: #3b82f6; color: white; border: none; padding: 8px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 12px;">🚀 TRUY CẬP MÁY ẢO</button>
            </div>
            """
            
        if not phones_html:
            phones_html = '<div style="color: #64748b; text-align: center; padding: 20px;">Hiện chưa có Cloud Phone nào hoạt động.</div>'

        html_template = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Gà Gaming - Cloud Phone Dashboard</title>
            <style>
                body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
                .card {{ background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 440px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; text-align: center; max-height: 90vh; overflow-y: auto; }}
                .badge {{ background: #334155; color: #38bdf8; padding: 6px 12px; border-radius: 20px; font-size: 12px; display: inline-block; margin-bottom: 15px; font-weight: bold; }}
                .admin-link {{ display: block; margin-top: 15px; font-size: 11px; color: #64748b; text-decoration: none; }}
                .admin-link:hover {{ color: #94a3b8; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>☁️ Gà Gaming Cloud Phone</h2>
                <div class="badge">⚡ Hệ thống điện thoại đám mây ảo hóa cấp cao</div>
                <p style="font-size: 12px; color: #94a3b8; margin-bottom: 20px;">Danh sách các máy ảo đang chạy 24/7 trên mây:</p>
                
                {phones_html}

                <a href="/admin" class="admin-link">⚙️ Quản lý Cloud Phone (Admin)</a>
            </div>

            <script>
                function connectCloud(id) {{
                    alert("Đang kết nối tới " + id + " trên đám mây... Mời bạn sẵn sàng!");
                    // Tùy chỉnh hành động mở máy ảo ở đây
                }}
            </script>
        </body>
        </html>
        """
        return render_template_string(html_template)
    except Exception as e:
        return f"Lỗi giao diện: {str(e)}", 500

# --- 2. TRANG ADMIN QUẢN LÝ CLOUD PHONE ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    try:
        db = load_db()
        message = ""
        
        if request.method == 'POST' and 'password' in request.form and 'phone_name' not in request.form and 'delete_id' not in request.form:
            if request.form.get('password') == ADMIN_PASSWORD:
                session['admin_logged'] = True
                return redirect('/admin')
            else:
                message = "❌ Mật khẩu Admin không chính xác!"

        if not session.get('admin_logged'):
            return render_template_string(f"""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <title>Đăng Nhập Admin Cloud</title>
                <style>
                    body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
                    .card {{ background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 360px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                    input {{ width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; margin-top: 15px; }}
                    button {{ background: #3b82f6; color: white; border: none; padding: 10px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 15px; }}
                    button:hover {{ background: #2563eb; }}
                    .error {{ color: #ef4444; font-size: 12px; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>🔐 Đăng Nhập Admin Cloud</h2>
                    <form method="POST">
                        <input type="password" name="password" placeholder="Nhập mật khẩu Admin..." required>
                        <button type="submit">Đăng Nhập</button>
                    </form>
                    <div class="error">{message}</div>
                    <br><a href="/" style="color: #94a3b8; font-size: 12px; text-decoration: none;">← Quay lại trang chủ</a>
                </div>
            </body>
            </html>
            """)

        if request.method == 'POST':
            if 'phone_name' in request.form:
                p_name = request.form.get('phone_name', '').strip()
                p_model = request.form.get('phone_model', '').strip()
                p_android = request.form.get('phone_android', '').strip()
                p_ram = request.form.get('phone_ram', '').strip()
                
                new_id = "CP-" + ''.join(random.choices(string.digits, k=4))
                new_phone = {
                    "id": new_id,
                    "name": p_name if p_name else "Cloud Phone mới",
                    "model": p_model if p_model else "Snapdragon Device",
                    "android": p_android if p_android else "Android 13",
                    "ram": p_ram if p_ram else "12GB",
                    "status": "Online",
                    "ip": f"103.x.x.{random.randint(10, 99)}"
                }
                
                db["phones"].append(new_phone)
                save_db(db)
                message = f"✅ Đã tạo thành công máy ảo {new_id}!"

            if 'delete_id' in request.form:
                del_id = request.form.get('delete_id')
                db["phones"] = [p for p in db["phones"] if p["id"] != del_id]
                save_db(db)
                message = f"✅ Đã xóa máy ảo {del_id}!"

        phones = db.get("phones", [])
        manage_html = ""
        for p in phones:
            manage_html += f"""
            <div style="background: #0b0f19; padding: 10px; border-radius: 8px; margin-top: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
                <div>
                    <span style="color: #38bdf8; font-weight: bold;">{p['name']} ({p['id']})</span><br>
                    <span style="color: #94a3b8; font-size: 11px;">Model: {p['model']} | RAM: {p['ram']}</span>
                </div>
                <form method="POST" style="margin: 0;">
                    <input type="hidden" name="delete_id" value="{p['id']}">
                    <button type="submit" style="background: #ef4444; color: white; padding: 5px 10px; font-size: 11px; margin: 0; width: auto; cursor: pointer;">Xóa</button>
                </form>
            </div>
            """

        return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Quản Lý Cloud Phone - Admin</title>
            <style>
                body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
                .card {{ background: #1e293b; padding: 25px; border-radius: 16px; width: 100%; max-width: 500px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); box-sizing: border-box; max-height: 90vh; overflow-y: auto; }}
                input {{ width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; margin-top: 6px; margin-bottom: 10px; }}
                button {{ background: #22c55e; color: white; border: none; padding: 10px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }}
                button:hover {{ background: #16a34a; }}
                .logout {{ background: #ef4444; margin-top: 15px; }}
                .success {{ color: #4ade80; font-size: 13px; margin-top: 10px; text-align: center; font-weight: bold; }}
                .section {{ border-top: 1px solid #334155; margin-top: 20px; padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>⚙️ Quản Lý Hệ Thống Cloud Phone</h2>
                
                <form method="POST" class="section">
                    <label style="font-size: 12px; color: #38bdf8; font-weight: bold;">➕ Tạo Máy Ảo Cloud Mới:</label>
                    <input type="text" name="phone_name" placeholder="Tên máy (Ví dụ: Máy Treo Blox Fruits)">
                    <input type="text" name="phone_model" placeholder="Tên thiết bị (Ví dụ: ROG Phone 6)">
                    <input type="text" name="phone_android" placeholder="Hệ điều hành (Ví dụ: Android 13)">
                    <input type="text" name="phone_ram" placeholder="Dung lượng RAM (Ví dụ: 16GB)">
                    <button type="submit">Tạo Cloud Phone</button>
                </form>

                <div class="section">
                    <label style="font-size: 12px; color: #38bdf8; font-weight: bold;">📋 Danh Sách Máy Đang Quản Lý:</label>
                    <div style="max-height: 180px; overflow-y: auto; margin-top: 8px;">
                        {manage_html}
                    </div>
                </div>
                
                <div class="success">{message}</div>

                <form action="/admin/logout" method="POST">
                    <button type="submit" class="logout">Đăng Xuất Admin</button>
                </form>
                
                <div style="text-align: center; margin-top: 15px;">
                    <a href="/" style="color: #94a3b8; font-size: 12px; text-decoration: none;">← Về trang chủ Cloud</a>
                </div>
            </div>
        </body>
        </html>
        """, message=message, manage_html=manage_html)
    except Exception as e:
        return f"Lỗi Admin: {str(e)}", 500

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged', None)
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
