import os
import glob
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory, request

app = Flask(__name__)

# 配置图片目录 - 请修改为您的实际图片目录
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')

# 访问统计文件
STATS_FILE = 'visitor_stats.json'

# 支持的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# 初始化访问统计
def init_visitor_stats():
    """初始化访问统计"""
    if not os.path.exists(STATS_FILE):
        stats = {
            'total_visits': 0,
            'unique_visitors': 0,
            'visitor_ips': [],
            'last_reset': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_visitor_stats(stats)
    return load_visitor_stats()

def load_visitor_stats():
    """加载访问统计"""
    try:
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return init_visitor_stats()

def save_visitor_stats(stats):
    """保存访问统计"""
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=4)

def update_visitor_stats(ip_address):
    """更新访问统计"""
    stats = load_visitor_stats()
    
    # 增加总访问次数
    stats['total_visits'] += 1
    
    # 如果是新访客，增加唯一访客数
    if ip_address not in stats['visitor_ips']:
        stats['visitor_ips'].append(ip_address)
        stats['unique_visitors'] += 1
    
    save_visitor_stats(stats)
    return stats

def get_image_files():
    """获取图片目录中的所有图片文件"""
    images = []
    
    # 确保目录存在
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        return images
    
    # 遍历所有支持的图片格式
    for ext in ALLOWED_EXTENSIONS:
        pattern = os.path.join(IMAGE_DIR, f'*.{ext}')
        for file_path in glob.glob(pattern):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_size_str = format_file_size(file_size)
            
            images.append({
                'name': file_name,
                'path': file_name,  # 相对于图片目录的路径
                'size': file_size_str,
                'full_path': file_path
            })
    
    # 按文件名排序
    images.sort(key=lambda x: x['name'])
    return images

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

@app.route('/')
def index():
    """主页面"""
    # 获取访问者IP
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip_address = request.environ['REMOTE_ADDR']
    else:
        ip_address = request.environ['HTTP_X_FORWARDED_FOR']
    
    # 更新访问统计
    stats = update_visitor_stats(ip_address)
    
    return render_template('index.html', 
                          total_visits=stats['total_visits'],
                          unique_visitors=stats['unique_visitors'])

@app.route('/api/images')
def api_images():
    """API: 获取图片列表"""
    images = get_image_files()
    return jsonify({
        'success': True,
        'count': len(images),
        'images': images
    })

@app.route('/api/visitor_stats')
def api_visitor_stats():
    """API: 获取访问统计"""
    stats = load_visitor_stats()
    return jsonify({
        'success': True,
        'total_visits': stats['total_visits'],
        'unique_visitors': stats['unique_visitors']
    })

@app.route('/images/<path:filename>')
def serve_image(filename):
    """提供图片文件访问"""
    return send_from_directory(IMAGE_DIR, filename)

if __name__ == '__main__':
    # 初始化访问统计
    init_visitor_stats()
    
    # 创建图片目录（如果不存在）
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        print(f"已创建图片目录: {IMAGE_DIR}")
    
    print(f"服务器启动，图片目录: {IMAGE_DIR}")
    print("请将图片文件放入该目录，然后访问 http://localhost:3636")
    app.run(debug=True, host='0.0.0.0', port=3636)