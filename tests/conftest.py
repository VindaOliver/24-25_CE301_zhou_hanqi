import os
import sys
import pytest
import tempfile
import json
import numpy as np
from PIL import Image
from werkzeug.security import generate_password_hash
import io
import tensorflow as tf
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入应用模块 (确保在添加路径后进行导入)
from app import app, DB_CONFIG


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # 使用临时目录作为上传文件夹
    with tempfile.TemporaryDirectory() as temp_dir:
        app.config['UPLOAD_FOLDER'] = os.path.join(temp_dir, 'uploads')
        app.config['AVATARS_FOLDER'] = os.path.join(temp_dir, 'avatars')
        
        # 确保必要的目录结构存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['AVATARS_FOLDER'], exist_ok=True)
        
        # 创建breeds目录
        breeds_dir = os.path.join(temp_dir, 'images', 'breeds')
        os.makedirs(breeds_dir, exist_ok=True)
        
        # 创建一个示例品种图片
        test_img = Image.new('RGB', (224, 224), color=(73, 109, 137))
        for breed in ['Abyssinian', 'Bengal', 'Siamese']:
            img_path = os.path.join(breeds_dir, f"{breed.lower()}_1.jpg")
            test_img.save(img_path)
        
        # 修改测试时的静态路径指向临时目录
        original_static_folder = app.static_folder
        app.static_folder = temp_dir
        
        with app.test_client() as client:
            yield client
            
        # 恢复原始静态文件夹配置
        app.static_folder = original_static_folder


@pytest.fixture
def mock_db(monkeypatch):
    """模拟数据库连接和操作"""
    
    class MockCursor:
        def __init__(self):
            self.executed_queries = []
            self.fetch_returns = []
            
        def execute(self, query, params=None):
            self.executed_queries.append((query, params))
            return True
            
        def fetchone(self):
            if self.fetch_returns and len(self.fetch_returns) > 0:
                return self.fetch_returns[0]
            return None
            
        def fetchall(self):
            return self.fetch_returns
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    class MockConnection:
        def __init__(self):
            self.cursor_obj = MockCursor()
            
        def cursor(self):
            return self.cursor_obj
            
        def commit(self):
            pass
            
        def close(self):
            pass
    
    # 创建mock连接对象
    mock_conn = MockConnection()
    
    # 模拟get_db函数，返回mock连接
    def mock_get_db():
        return mock_conn
    
    # 应用mock
    monkeypatch.setattr('app.get_db', mock_get_db)
    
    return mock_conn


@pytest.fixture
def mock_model(monkeypatch):
    """模拟模型加载和预测"""
    
    class MockModel:
        def __init__(self):
            self.prediction_results = []
            
        def predict(self, image_array):
            # 返回mock预测结果 (20个品种的概率数组)
            if not self.prediction_results:
                # 默认预测: 第一个品种概率最高
                result = np.zeros((1, 20))
                result[0, 0] = 0.8  # 第一个品种预测概率为80%
                result[0, 1] = 0.2  # 第二个品种预测概率为20%
                return result
            return self.prediction_results.pop(0)
    
    # 创建模型实例
    model_obj = MockModel()
    
    # 模拟load_model和warmup_model函数
    def mock_load_model():
        app.model = model_obj
        
    def mock_warmup_model():
        pass
    
    # 应用mock
    monkeypatch.setattr('app.load_model', mock_load_model)
    monkeypatch.setattr('app.warmup_model', mock_warmup_model)
    monkeypatch.setattr('app.model', model_obj)
    
    return model_obj


@pytest.fixture
def sample_image():
    """创建一个样本测试图像"""
    # 创建一个简单的RGB测试图像
    img = Image.new('RGB', (224, 224), color=(73, 109, 137))
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return img_io


@pytest.fixture
def authenticated_client(client, mock_db):
    """创建一个已认证的客户端会话"""
    # 设置模拟数据库返回用户数据
    mock_db.cursor_obj.fetch_returns = [{
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': generate_password_hash('password123'),
        'avatar_path': 'default-avatar.jpg',  # 添加默认头像路径
        'bio': 'Test bio',
        'phone': '1234567890'
    }]
    
    # 登录
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    # 验证用户已登录 (session中有user_id)
    with client.session_transaction() as session:
        session['user_id'] = 1
    
    return client


@pytest.fixture
def mock_listdir(monkeypatch):
    """模拟目录列表，确保breeds目录测试可用"""
    
    original_listdir = os.listdir
    
    def mock_listdir_fn(path):
        if 'breeds' in str(path):
            return ['abyssinian_1.jpg', 'bengal_1.jpg', 'siamese_1.jpg']
        return original_listdir(path)
    
    monkeypatch.setattr('os.listdir', mock_listdir_fn)
    
    return mock_listdir_fn 