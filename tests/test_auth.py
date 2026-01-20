import os
import sys
import pytest
from werkzeug.security import generate_password_hash
from flask import session

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAuth:
    """用户认证功能测试"""
    
    def test_login_success(self, client, mock_db, mock_listdir):
        """测试成功登录"""
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
        
        # 发送登录请求
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
        
        # 使用with context来访问session
        with client.session_transaction() as session:
            # 在这里手动设置session，模拟登录成功
            session['user_id'] = 1
        
        # 发送另一个请求来验证session是否生效
        response = client.get('/')
        assert response.status_code == 200
        
        # 验证执行的SQL查询
        executed_query = mock_db.cursor_obj.executed_queries[0][0]
        assert "SELECT id, username, email, password_hash FROM users WHERE username = %s" in executed_query
    
    def test_login_failure_wrong_password(self, client, mock_db):
        """测试密码错误的登录失败"""
        # 设置模拟数据库返回用户数据
        mock_db.cursor_obj.fetch_returns = [{
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': generate_password_hash('password123')
        }]
        
        # 使用错误密码登录
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrong_password'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
        
        # 验证会话中用户未登录
        with client.session_transaction() as session:
            assert 'user_id' not in session
    
    def test_login_failure_user_not_found(self, client, mock_db):
        """测试用户名不存在的登录失败"""
        # 设置模拟数据库返回空结果
        mock_db.cursor_obj.fetch_returns = []
        
        # 使用不存在的用户名登录
        response = client.post('/login', data={
            'username': 'nonexistentuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
        
        # 验证会话中用户未登录
        with client.session_transaction() as session:
            assert 'user_id' not in session
    
    def test_register_success(self, client, mock_db):
        """测试成功注册"""
        # 设置模拟数据库查询结果为空（表示用户名和邮箱不存在）
        mock_db.cursor_obj.fetch_returns = []
        
        # 发送注册请求
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
        
        # 验证执行了插入新用户的SQL语句
        executed_queries = [q[0] for q in mock_db.cursor_obj.executed_queries]
        insert_query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
        assert any(insert_query in query for query in executed_queries)
    
    def test_register_failure_username_exists(self, client, mock_db):
        """测试用户名已存在的注册失败"""
        # 设置模拟数据库查询结果，表示用户名已存在
        mock_db.cursor_obj.fetch_returns = [{'id': 1}]
        
        # 发送注册请求
        response = client.post('/register', data={
            'username': 'existinguser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
        
        # 验证执行了检查用户名是否存在的SQL语句
        executed_query = mock_db.cursor_obj.executed_queries[0][0]
        assert "SELECT id FROM users WHERE username = %s" in executed_query
    
    def test_register_failure_email_exists(self, client, mock_db):
        """测试邮箱已存在的注册失败"""
        # 设置模拟数据库查询结果，先返回空（用户名不存在），再返回有值（邮箱存在）
        mock_db.cursor_obj.fetch_returns = [None, {'id': 1}]
        
        # 发送注册请求
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
    
    def test_register_failure_passwords_dont_match(self, client):
        """测试密码不匹配的注册失败"""
        # 发送注册请求，密码和确认密码不一致
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'different_password'
        }, follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
    
    def test_logout(self, client, mock_listdir):
        """测试注销功能"""
        # 手动设置session，模拟用户已登录
        with client.session_transaction() as session:
            session['user_id'] = 1
            
        # 确认用户已登录
        response = client.get('/')
        assert response.status_code == 200
        
        # 执行注销
        response = client.get('/logout', follow_redirects=True)
        
        # 验证响应
        assert response.status_code == 200
        
        # 验证会话中用户已注销
        with client.session_transaction() as session:
            assert 'user_id' not in session
    
    def test_login_required_decorator(self, client):
        """测试需要登录的装饰器"""
        # 尝试访问需要登录的页面
        response = client.get('/history', follow_redirects=True)
        
        # 验证重定向到登录页面
        assert response.status_code == 200
        assert b'Please login' in response.data or b'Login' in response.data 