import os
import sys
import pytest
import json
import io
from werkzeug.datastructures import FileStorage

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入应用相关函数
from app import get_breed_characteristics, get_breed_personality, get_breed_care, get_daily_breed_recommendation


class TestRecognition:
    """猫品种识别和相关功能测试"""
    
    def test_predict_endpoint(self, authenticated_client, mock_db, mock_model, sample_image, mock_listdir):
        """测试猫咪品种识别端点"""
        # 创建模拟文件上传
        file = FileStorage(
            stream=sample_image,
            filename='test_cat.jpg',
            content_type='image/jpeg'
        )
        
        # 发送预测请求
        response = authenticated_client.post(
            '/predict',
            data={'file': file},
            content_type='multipart/form-data'
        )
        
        # 验证响应
        assert response.status_code == 200
        
        # 解析JSON响应
        data = json.loads(response.data)
        
        # 验证返回的预测结果格式正确
        assert 'predictions' in data
        assert isinstance(data['predictions'], list)
        assert len(data['predictions']) > 0
        assert 'breed' in data['predictions'][0]
        assert 'probability' in data['predictions'][0]
        
        # 验证品种信息存在
        assert 'breed_info' in data
        assert 'name' in data['breed_info']
        assert 'characteristics' in data['breed_info']
        assert 'personality' in data['breed_info']
        assert 'care' in data['breed_info']
        
        # 验证历史记录被保存
        assert any("INSERT INTO histories" in q[0] for q in mock_db.cursor_obj.executed_queries)
    
    def test_predict_error_no_file(self, authenticated_client, mock_listdir):
        """测试预测端点无文件错误处理"""
        # 发送没有文件的预测请求
        response = authenticated_client.post('/predict', data={})
        
        # 验证响应
        assert response.status_code == 400
        
        # 解析JSON响应
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file uploaded' in data['error']
    
    def test_predict_error_invalid_file_format(self, authenticated_client, mock_listdir):
        """测试预测端点无效文件格式错误处理"""
        # 创建模拟文本文件
        text_file = FileStorage(
            stream=io.BytesIO(b'This is not an image'),
            filename='test.txt',
            content_type='text/plain'
        )
        
        # 发送无效文件格式的预测请求
        response = authenticated_client.post(
            '/predict',
            data={'file': text_file},
            content_type='multipart/form-data'
        )
        
        # 验证响应
        assert response.status_code == 400
        
        # 解析JSON响应
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Unsupported file format' in data['error']
    
    def test_get_breed_characteristics(self):
        """测试获取品种特征信息"""
        # 测试已知品种
        abyssinian_char = get_breed_characteristics('Abyssinian')
        assert isinstance(abyssinian_char, dict)
        assert 'size' in abyssinian_char
        assert 'coat' in abyssinian_char
        assert 'color' in abyssinian_char
        assert 'lifespan' in abyssinian_char
        assert 'origin' in abyssinian_char
        
        # 测试未知品种返回默认值
        unknown_char = get_breed_characteristics('Unknown Breed')
        assert isinstance(unknown_char, dict)
        assert 'size' in unknown_char
        assert unknown_char['size'] == 'Varies'
    
    def test_get_breed_personality(self):
        """测试获取品种性格信息"""
        # 测试已知品种
        siamese_pers = get_breed_personality('Siamese')
        assert isinstance(siamese_pers, list)
        assert len(siamese_pers) > 0
        assert 'Vocal' in siamese_pers
        
        # 测试未知品种返回默认值
        unknown_pers = get_breed_personality('Unknown Breed')
        assert isinstance(unknown_pers, list)
        assert len(unknown_pers) > 0
        assert 'Varies by individual cat' in unknown_pers
    
    def test_get_breed_care(self):
        """测试获取品种护理信息"""
        # 测试已知品种
        persian_care = get_breed_care('Persian')
        assert isinstance(persian_care, dict)
        assert 'grooming' in persian_care
        assert 'exercise' in persian_care
        assert 'health_concerns' in persian_care
        assert 'diet' in persian_care
        
        # 测试未知品种返回默认值
        unknown_care = get_breed_care('Unknown Breed')
        assert isinstance(unknown_care, dict)
        assert 'grooming' in unknown_care
        assert unknown_care['grooming'] == 'Varies based on coat type'
    
    def test_daily_breed_recommendation(self, monkeypatch, mock_listdir):
        """测试每日品种推荐功能"""
        # 模拟os.listdir函数已通过mock_listdir处理
        
        # 测试推荐功能
        recommendation = get_daily_breed_recommendation()
        
        # 验证推荐结果格式正确
        assert recommendation is not None
        assert 'id' in recommendation
        assert 'name' in recommendation
        assert 'image_filename' in recommendation
        assert 'characteristics' in recommendation
        assert 'personality' in recommendation 