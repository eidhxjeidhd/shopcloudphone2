import os
import subprocess
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Thư mục lưu trữ code các bot do người dùng tạo
BOTS_DIR = "user_bots"
os.makedirs(BOTS_DIR, exist_ok=True)

# Lưu trữ các tiến trình bot đang chạy trên server
running_bots = {}

@app.route('/')
def home():
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <title>Telegram Bot Web Host 24/7</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }
                .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }
                input, textarea, button { width: 100%; padding: 10px; margin-top: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
                textarea { height: 150px; font-family: monospace; }
                button { background: #22c55e; font-weight: bold; cursor: pointer; border: none; }
                button:hover { background: #16a34a; }
                .status { margin-top: 10px; font-weight: bold; color: #38bdf8; }
            </style>
        </head>
        <body>
            <h1>🤖 Trình Tạo & Chạy Bot Telegram 24/7</h1>
            <div class="card">
                <h3>1. Cấu hình & Viết Code cho Bot</h3>
                <label>Telegram Bot Token:</label>
                <input type="text" id="botToken" placeholder="Ví dụ: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ">
                
                <label>Mã nguồn Python cho Bot (Sử dụng thư viện requests hoặc telebot):</label>
                <textarea id="botCode">import requests, time

TOKEN = "DIEN_TOKEN_VAO_DAY"
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# Code vòng lặp đơn giản hoặc xử lý bot chạy ngầm 24/7
print("Bot đang chạy...")
</textarea>
                <button onclick="deployBot()">Lưu & Chạy Bot 24/7</button>
                <div class="status" id="statusResult"></div>
            </div>

            <script>
                async function deployBot() {
                    const token = document.getElementById('botToken').value;
                    const code = document.getElementById('botCode').value;
                    const status = document.getElementById('statusResult');
                    
                    if(!token) { alert('Vui lòng nhập Token!'); return; }
                    
                    status.innerText = "Đang khởi tạo và kích hoạt bot...";
                    
                    const res = await fetch('/api/deploy', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({token: token, code: code})
                    });
                    const data = await res.json();
                    status.innerText = data.message;
                }
            </script>
        </body>
        </html>
    """)

@app.route('/api/deploy', methods=['POST'])
def deploy():
    data = request.json
    token = data.get('token')
    code = data.get('code')
    
    if not token:
        return jsonify({"message": "Thiếu Token bot!"})
    
    # Tạo tên file riêng cho bot dựa vào token (lấy phần đầu token làm tên)
    bot_id = token.split(':')[0]
    bot_file_path = os.path.join(BOTS_DIR, f"bot_{bot_id}.py")
    
    # Tự động thay token vào code nếu người dùng để trống
    final_code = code.replace('DIEN_TOKEN_VAO_DAY', token)
    
    with open(bot_file_path, "w", encoding="utf-8") as f:
        f.write(final_code)
        
    # Nếu bot này đang chạy trước đó, tắt nó đi để cập nhật bản mới
    if bot_id in running_bots:
        try:
            running_bots[bot_id].terminate()
        except:
            pass
            
    # Chạy ngầm tiến trình Python mới cho bot này (hoạt động 24/7 trên server)
    process = subprocess.Popen(["python", bot_file_path])
    running_bots[bot_id] = process
    
    return jsonify({
        "message": f" thành công! Bot đang chạy ngầm 24/7. Link quản lý: t.me/{bot_id} (kiểm tra trên Telegram)"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
