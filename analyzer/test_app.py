from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Hello World! 中文新聞爬蟲系統測試</h1><p>如果您看到這個頁面，說明 Flask 應用程式運行正常！</p>'

if __name__ == '__main__':
    print("正在啟動 Flask 應用程式...")
    print("請訪問: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
