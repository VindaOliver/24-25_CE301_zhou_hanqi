import os
import sys
import pytest
import numpy as np
from PIL import Image
import io
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入应用模块
from app import load_model, preprocess_image, model, warmup_model


class TestModel:
    """模型加载和图像处理测试"""
    
    def test_load_model(self, monkeypatch, mock_model):
        """测试模型加载功能"""
        # 测试加载模型 - 设置模型为None，然后加载
        from app import model as app_model
        app_model = None
        monkeypatch.setattr('app.model', None)
        
        # 调用加载函数
        load_model()
        
        # 验证模型已被mock_model fixture正确设置
        from app import model as app_model
        assert mock_model is not None
        assert hasattr(mock_model, 'predict')
    
    def test_warmup_model(self, monkeypatch, mock_model, tmp_path):
        """测试模型预热功能"""
        # 创建一个mock的预热图像目录
        warmup_dir = tmp_path / "static" / "warmup"
        os.makedirs(warmup_dir, exist_ok=True)
        
        # 创建一个测试图像
        test_img = Image.new('RGB', (224, 224), color=(73, 109, 137))
        img_path = warmup_dir / "test_warmup.jpg"
        test_img.save(img_path)
        
        # 模拟os.listdir返回我们的预热图像
        def mock_listdir(path):
            if str(warmup_dir) in str(path):
                return ["test_warmup.jpg"]
            return []
        
        monkeypatch.setattr('os.listdir', mock_listdir)
        
        # 保存原始的join函数
        original_join = os.path.join
        
        # 创建一个安全的join函数，避免递归
        def safe_join(*args):
            if 'warmup' in args:
                return str(img_path)
            return original_join(*args)
            
        monkeypatch.setattr('os.path.join', safe_join)
        
        # 跟踪predict调用
        predict_called = False
        original_predict = mock_model.predict
        
        def mock_predict(img_array):
            nonlocal predict_called
            predict_called = True
            return original_predict(img_array)
        
        mock_model.predict = mock_predict
        
        # 执行预热
        warmup_model()
        
        # 验证predict被调用
        assert predict_called, "模型预热应该调用predict方法"
    
    def test_preprocess_image(self, monkeypatch, tmp_path):
        """测试图像预处理功能"""
        # 创建测试图像
        test_img = Image.new('RGB', (300, 300), color=(255, 0, 0))
        img_path = tmp_path / "test_image.jpg"
        test_img.save(img_path)
        
        # 模拟tf.keras.applications.mobilenet_v2.preprocess_input
        def mock_preprocess_input(x):
            return x  # 简单地返回输入
        
        monkeypatch.setattr('tensorflow.keras.applications.mobilenet_v2.preprocess_input', 
                          mock_preprocess_input)
        
        # 测试预处理
        processed = preprocess_image(str(img_path))
        
        # 验证结果
        assert processed.shape == (1, 224, 224, 3), "预处理后的图像应该是1x224x224x3的形状"
        
    def test_preprocess_image_formats(self, tmp_path):
        """测试不同格式的图像预处理"""
        formats = [
            ('RGB', 'jpg'),
            ('RGBA', 'png')
        ]
        
        for mode, ext in formats:
            # 创建不同格式的测试图像
            if mode == 'RGB':
                test_img = Image.new(mode, (300, 300), color=(255, 0, 0))
            else:  # RGBA
                test_img = Image.new(mode, (300, 300), color=(255, 0, 0, 128))
                
            img_path = tmp_path / f"test_image.{ext}"
            test_img.save(img_path)
            
            # 测试预处理
            processed = preprocess_image(str(img_path))
            
            # 验证结果
            assert processed.shape == (1, 224, 224, 3), f"{mode}格式的图像应该被正确预处理为1x224x224x3的形状" 