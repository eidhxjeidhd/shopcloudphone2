import os
import subprocess
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Thư mục lưu trữ code các bot
BOTS_DIR = "user_bots"
os.makedirs(BOTS_DIR, exist_ok=True)

# Từ điển lưu trữ các tiến trình bot đang chạy trên server
running_bots = {}

@app.route('/')
def home():
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Gà Gaming - Telegram Bot Hub 24/7</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
                .container { max-width: 900px; width: 100%; }
                header { text-align: center; margin-bottom: 25px; }
                .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
                input, textarea, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; font-family: sans-serif; }
                textarea { height: 250px; font-family: monospace; font-size: 13px; line-height: 1.5; resize: vertical; }
                button { background: #22c55e; font-weight: bold; cursor: pointer; border: none; font-size: 15px; }
                button:hover { background: #16a34a; }
                .status { margin-top: 15px; padding: 10px; border-radius: 6px; background: #0f172a; font-weight: bold; color: #38bdf8; text-align: center; border: 1px solid #334155; }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h2>🤖 Hệ Thống Tạo & Treo Bot Telegram 24/7</h2>
                    <p style="color: #94a3b8; font-size: 14px;">Chỉnh sửa code trực tiếp và chạy ngầm trên máy chủ</p>
                </header>

                <div class="card">
                    <h3>⚙️ Cấu Hình & Soạn Thảo Bot</h3>
                    <label>Telegram Bot Token:</label>
                    <input type="text" id="botToken" placeholder="Ví dụ: 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ">
                    
                    <label style="margin-top: 15px; display: block;">Mã nguồn Python cho Bot (Telebot):</label>
                    <textarea id="botCode">import telebot

TOKEN = "DIEN_TOKEN_VAO_DAY"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Chào bạn! Bot của tôi đang chạy 24/7 trên web server rất mượt mà!")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, f"Bạn vừa nói: {message.text}")

print("Bot đang khởi động...")
bot.infinity_polling()</textarea>
                    
                    <button onclick="deployBot()">Lưu Code & Khởi Động Bot 24/7</button>
                    <div class="status" id="statusResult">Chưa có bot nào được kích hoạt trong phiên làm việc này.</div>
                </div>
            </div>

            <script>
                async function deployBot() {
                    const token = document.getElementById('botToken').value.trim();
                    const code = document.getElementById('botCode').value;
                    const status = document.getElementById('statusResult');
                    
                    if(!token) { alert('Vui lòng nhập Telegram Bot Token!'); return; }
                    
                    status.innerText = "Đang lưu code và khởi chạy tiến trình bot trên server...";
                    
                    try {
                        const res = await fetch('/api/deploy', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({token: token, code: code})
                        });
                        const data = await res.json();
                        status.innerText = data.message;
                    } catch(e) {
                        status.innerText = "Lỗi kết nối đến máy chủ!";
                    }
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
    
    # Lấy phần đầu token làm định danh bot
    bot_id = token.split(':')[0]
    bot_file_path = os.path.join(BOTS_DIR, f"bot_{bot_id}.py")
    
    # Tự động thay token vào code nếu người dùng để trống
    final_code = code.replace('DIEN_TOKEN_VAO_DAY', token)
    
    # Ghi đè file code mới nhất
    with open(bot_file_path, "w", encoding="utf-8") as f:
        f.write(final_code)
        
    # Nếu bot này đang chạy tiến trình cũ, tiến hành tắt nó đi trước khi bật bản mới
    if bot_id in running_bots:
        try:
            running_bots[bot_id].terminate()
            running_bots[bot_id].wait()
        except:
            pass
            
    # Khởi chạy ngầm tiến trình Python độc lập cho bot
    process = subprocess.Popen(["python", bot_file_path])
    running_bots[bot_id] = process
    
    return jsonify({
        "message": f"✅ Thành công! Bot (ID: {bot_id}) đã bắt đầu chạy ngầm 24/7 trên server. Bạn có thể vào Telegram kiểm tra bot ngay!"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
