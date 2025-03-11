# coding:utf-8

from app import create_app
import logging
import os

# 配置日志
log_dir = '/var/log/authbase'
log_file = os.path.join(log_dir, 'debug.log')

# 确保日志目录存在
if not os.path.exists(log_dir):
    os.makedirs(log_dir, mode=0o755, exist_ok=True)

# 配置日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

app = create_app('development')

if __name__ == '__main__':
    # 启用远程调试
    app.run(
        host='0.0.0.0',  # 允许远程访问
        port=5120,
        debug=True,
        use_reloader=True,
        threaded=True
    )