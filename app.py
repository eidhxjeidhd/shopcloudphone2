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
                    
                    <label style="margin-top: 15px; display: block;">Mã nguồn Python cho Bot:</label>
                    <textarea id="botCode">import logging
import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "DIEN_TOKEN_VAO_DAY"
KEY_STORAGE_URL = "https://shopcloudphone.onrender.com/kho-key.txt"
cached_keys = []

def fetch_keys_from_web():
    try:
        response = requests.get(KEY_STORAGE_URL, timeout=10)
        if response.status_code == 200:
            keys = [line.strip() for line in response.text.splitlines() if line.strip()]
            return keys
    except Exception as e:
        print(f"Lỗi khi tải kho key: {e}")
    return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Xin chào {user_name}! 👋 Chào mừng bạn đến với bot phát key của ShopCloudPhone.\n\n"
        "Bấm /laykey để nhận ngay một key miễn phí nhé!"
    )

async def get_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cached_keys
    if not cached_keys:
        cached_keys = fetch_keys_from_web()

    if not cached_keys:
        await update.message.reply_text("⚠️ Kho key trên hệ thống hiện đang trống hoặc chưa có dữ liệu. Vui lòng quay lại sau!")
        return

    selected_key = random.choice(cached_keys)
    cached_keys.remove(selected_key)

    await update.message.reply_text(
        f"🎉 **Nhận key thành công!**\\n\\n🔑 Key của bạn: `{selected_key}`\\n\\n*(Hãy sao chép key để sử dụng trên hệ thống)*",
        parse_mode="Markdown"
    )

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("laykey", get_key))
    print("🤖 Bot đang chạy...")
    application.run_polling()

if __name__ == "__main__":
    main()</textarea>
                    
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
    
    bot_id = token.split(':')[0]
    bot_file_path = os.path.join(BOTS_DIR, f"bot_{bot_id}.py")
    
    # Tự động thay token vào code nếu người dùng để trống chữ DIEN_TOKEN_VAO_DAY
    final_code = code.replace('DIEN_TOKEN_VAO_DAY', token)
    
    with open(bot_file_path, "w", encoding="utf-8") as f:
        f.write(final_code)
        
    # Tắt tiến trình cũ nếu đang chạy
    if bot_id in running_bots:
        try:
            running_bots[bot_id].terminate()
            running_bots[bot_id].wait()
        except:
            pass
            
    # Sử dụng python3 để khởi chạy ngầm tiến trình bot độc lập 24/7
    process = subprocess.Popen(["python3", bot_file_path])
    running_bots[bot_id] = process
    
    return jsonify({
        "message": f"✅ Thành công! Bot (ID: {bot_id}) đã chạy ngầm 24/7 bằng python3 trên server. Vào Telegram test ngay!"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
