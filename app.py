import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import pymysql
from pymysql.cursors import DictCursor
from functools import wraps
import tensorflow as tf
import numpy as np
from PIL import Image
import time
import random
from shutil import copyfile
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = '2d9c6d8940c64e7aa0f167a4879d4e9cb2c7f0d62c4b4ef3a6f2c5e8b7a9d1f3'  # Use a strong randomly generated key

# MySQL database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'db': 'cat_breed',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['AVATARS_FOLDER'] = 'static/avatars'  # Directory for user avatars
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB max file size

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['AVATARS_FOLDER'], exist_ok=True)  # Ensure avatars directory exists
os.makedirs('static/warmup', exist_ok=True)  # Ensure warmup images directory exists

# Global variable to store the model
model = None

# Load model
def load_model():
    global model
    if model is None:
        model_files = [f for f in os.listdir('model') if f.endswith('.h5')]
        if not model_files:
            raise FileNotFoundError("Model file not found")
        model_path = os.path.join('model', model_files[0])
        model = tf.keras.models.load_model(model_path)

# Warm up model
def warmup_model():
    """
    Use a sample image to warm up the model, avoiding delay on first recognition
    """
    if model is None:
        return
    
    # Check if there are warm-up images
    warmup_dir = 'static/warmup'
    warmup_images = [f for f in os.listdir(warmup_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # If no warm-up images, create a simple image
    if not warmup_images:
        # Create a simple colored image
        img = Image.new('RGB', (224, 224), color=(73, 109, 137))
        warmup_path = os.path.join(warmup_dir, 'warmup_image.jpg')
        img.save(warmup_path)
    else:
        warmup_path = os.path.join(warmup_dir, warmup_images[0])
    
    start_time = time.time()
    
    try:
        # Preprocess image and make prediction
        processed_image = preprocess_image(warmup_path)
        _ = model.predict(processed_image)  # Discard result, just for warming up
        
    except Exception as e:
        print(f"Error during model warmup: {str(e)}")

# Preprocess image
def preprocess_image(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize((224, 224))  # Adjust based on your model input size
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# Get database connection
def get_db():
    return pymysql.connect(**DB_CONFIG)

# Login verification decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Get current user information
def get_current_user():
    if 'user_id' not in session:
        return None
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            sql = "SELECT id, username, email, avatar_path, bio, phone FROM users WHERE id = %s"
            cursor.execute(sql, (session['user_id'],))
            return cursor.fetchone()
    finally:
        conn.close()

# Allowed image formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed avatar formats

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_avatar_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS

# 随机推荐品种函数
def get_daily_breed_recommendation():
    # 获取所有品种
    breed_labels = [
        'Abyssinian', 'American Curl', 'American Shorthair', 'Bengal', 'Birman',
        'Bombay', 'British Shorthair', 'Egyptian Mau', 'Exotic Shorthair',
        'Himalayan', 'Maine Coon', 'Manx', 'Munchkin', 'Norwegian Forest',
        'Persian', 'Ragdoll', 'Russian Blue', 'Scottish Fold', 'Siamese', 'Sphynx'
    ]
    
    # 检查每个品种是否有图片，只保留有图片的品种
    breeds_with_images = []
    breeds_dir = os.path.join('static', 'images', 'breeds')
    
    for breed_name in breed_labels:
        breed_files = [f for f in os.listdir(breeds_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png')) 
                      and breed_name.lower().replace(' ', '_') in f.lower()]
        
        if breed_files:
            breeds_with_images.append(breed_name)
    
    # 如果没有找到任何有图片的品种，返回None
    if not breeds_with_images:
        return None
    
    # 随机选择一个品种
    selected_breed = random.choice(breeds_with_images)
    
    # 获取品种特征
    characteristics = get_breed_characteristics(selected_breed)
    personality = get_breed_personality(selected_breed)
    
    # 获取该品种的图片
    breed_files = [f for f in os.listdir(breeds_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png')) 
                  and selected_breed.lower().replace(' ', '_') in f.lower()]
    
    image_filename = breed_files[0]  # 现在我们确信至少有一张图片
    
    # 创建推荐对象
    recommendation = {
        'id': selected_breed,
        'name': selected_breed,
        'image_filename': image_filename,
        'characteristics': characteristics,
        'personality': personality
    }
    
    return recommendation

# Route: Main page (recognition page)
@app.route('/')
@login_required
def index():
    # Get current user
    current_user = get_current_user()
    
    # Get daily breed recommendation
    daily_recommendation = get_daily_breed_recommendation()
    
    # Process recommended breed to have the expected structure
    if daily_recommendation:
        recommended_breed = {
            'breed': daily_recommendation['name'],
            'image_url': url_for('static', filename=f"images/breeds/{daily_recommendation['image_filename']}"),
            'characteristics': daily_recommendation['characteristics'],
            'personality': daily_recommendation['personality']
        }
    else:
        # 如果没有找到推荐品种，提供一个默认值
        recommended_breed = {
            'breed': 'No breeds available',
            'image_url': url_for('static', filename='images/placeholder.jpg'),
            'characteristics': {},
            'personality': []
        }
    
    # 获取所有有图片的品种
    breeds_with_images, breed_images = get_breeds_with_images()
    
    # 构建热门品种列表（提供了最完整的数据和图片的品种）
    popular_breeds = []
    for breed_name in breeds_with_images[:8]:  # 最多显示8个
        popular_breeds.append({
            'name': breed_name,
            'image': breed_images[breed_name]['path']
        })
    
    return render_template('index.html', 
                          current_user=current_user, 
                          recommended_breed=recommended_breed,
                          popular_breeds=popular_breeds)

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to main page
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = get_db()
            with conn.cursor() as cursor:
                sql = "SELECT id, username, email, password_hash FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                user_data = cursor.fetchone()
                
                if user_data and check_password_hash(user_data['password_hash'], password):
                    session['user_id'] = user_data['id']
                    # Load model after successful login
                    try:
                        if model is None:
                            load_model()
                        # Warm up model after successful login
                        warmup_model()
                    except Exception as e:
                        print(f"Warning: Failed to load or warmup model: {str(e)}")
                    return redirect(url_for('index'))
                else:
                    flash('Username or password incorrect')
        finally:
            conn.close()

    return render_template('login.html')

# Route: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to main page
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            flash('Please fill in all required fields')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))

        try:
            conn = get_db()
            with conn.cursor() as cursor:
                # Check if username already exists
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash('Username already exists')
                    return redirect(url_for('register'))

                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash('Email already registered')
                    return redirect(url_for('register'))

                # Create new user
                sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, email, generate_password_hash(password)))
                conn.commit()

                flash('Registration successful, please login')
                return redirect(url_for('login'))
        finally:
            conn.close()

    return render_template('register.html')

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Route: History
@app.route('/history')
@login_required
def history():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            sql = """
                SELECT id, image_path, predictions, 
                       DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
                FROM histories 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (session['user_id'],))
            history_records = cursor.fetchall()
            
            # Process predictions field (convert from JSON string to Python object)
            for record in history_records:
                try:
                    record['predictions'] = json.loads(record['predictions'])
                    # Ensure there is at least one prediction result
                    if not record['predictions']:
                        record['predictions'] = [{
                            "breed": "Unknown",
                            "probability": 100.0
                        }]
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, use default value
                    record['predictions'] = [{
                        "breed": "Unknown",
                        "probability": 100.0
                    }]
                
            return render_template('history.html', history=history_records, current_user=get_current_user())
    finally:
        conn.close()

# Route: Delete single history record
@app.route('/delete_history/<int:record_id>', methods=['POST'])
@login_required
def delete_history(record_id):
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Ensure record belongs to current user
            check_sql = "SELECT image_path FROM histories WHERE id = %s AND user_id = %s"
            cursor.execute(check_sql, (record_id, session['user_id']))
            record = cursor.fetchone()
            
            if not record:
                flash('Record does not exist or you do not have permission to delete it', 'danger')
                return redirect(url_for('history'))
            
            # Delete physical image file (if exists)
            try:
                image_path = os.path.join('static', record['image_path'])
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                # If file deletion fails, log error but continue with database record deletion
                print(f"Failed to delete image file: {str(e)}")
            
            # Delete database record
            delete_sql = "DELETE FROM histories WHERE id = %s AND user_id = %s"
            cursor.execute(delete_sql, (record_id, session['user_id']))
            conn.commit()
            
            flash('History record successfully deleted', 'success')
            return redirect(url_for('history'))
    finally:
        conn.close()

# Route: Clear all history records
@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Get all image paths for the user's history records
            get_paths_sql = "SELECT image_path FROM histories WHERE user_id = %s"
            cursor.execute(get_paths_sql, (session['user_id'],))
            records = cursor.fetchall()
            
            # Try to delete all image files
            for record in records:
                try:
                    image_path = os.path.join('static', record['image_path'])
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    # If file deletion fails, log error but continue
                    print(f"Failed to delete image file: {str(e)}")
            
            # Delete all database records
            delete_sql = "DELETE FROM histories WHERE user_id = %s"
            cursor.execute(delete_sql, (session['user_id'],))
            conn.commit()
            
            flash('All history records successfully cleared', 'success')
            return redirect(url_for('history'))
    finally:
        conn.close()

# Route: History details
@app.route('/detail/<int:record_id>')
@login_required
def detail(record_id):
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Get specific history record by ID
            sql = """
                SELECT id, image_path, predictions, 
                       DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
                FROM histories 
                WHERE id = %s AND user_id = %s
            """
            cursor.execute(sql, (record_id, session['user_id']))
            record = cursor.fetchone()
            
            if not record:
                flash('Record not found')
                return redirect(url_for('history'))
            
            # Process predictions field
            try:
                record['predictions'] = json.loads(record['predictions'])
                if not record['predictions']:
                    record['predictions'] = [{
                        "breed": "Unknown",
                        "probability": 100.0
                    }]
            except (json.JSONDecodeError, TypeError):
                record['predictions'] = [{
                    "breed": "Unknown",
                    "probability": 100.0
                }]
            
            # Get breed information
            breed_info = {
                "name": record['predictions'][0]["breed"],
                "characteristics": get_breed_characteristics(record['predictions'][0]["breed"]),
                "personality": get_breed_personality(record['predictions'][0]["breed"]),
                "care": get_breed_care(record['predictions'][0]["breed"])
            }
            
            return render_template('detail.html', record=record, breed_info=breed_info, current_user=get_current_user())
    finally:
        conn.close()

# Route: Predict
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file format'}), 400

    try:
        # Save uploaded image
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Ensure upload directory exists
        upload_path = os.path.join('static', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)

        # Preprocess image and make prediction
        processed_image = preprocess_image(filepath)
        predictions_array = model.predict(processed_image)

        # Get class labels (based on your dataset)
        breed_labels = [
            'Abyssinian', 'American Curl', 'American Shorthair', 'Bengal', 'Birman',
            'Bombay', 'British Shorthair', 'Egyptian Mau', 'Exotic Shorthair',
            'Himalayan', 'Maine Coon', 'Manx', 'Munchkin', 'Norwegian Forest',
            'Persian', 'Ragdoll', 'Russian Blue', 'Scottish Fold', 'Siamese', 'Sphynx'
        ]

        # Get the top two highest probability predictions
        predictions = []
        # Get sorted indices (by probability from high to low)
        sorted_indices = predictions_array[0].argsort()[::-1]
        
        # Only take the top two highest probability predictions
        for idx in sorted_indices[:2]:
            if idx < len(breed_labels):  # Ensure index is within valid range
                breed = breed_labels[idx]
                probability = float(predictions_array[0][idx] * 100)
                if probability > 1.0:  # Only add predictions with probability greater than 1%
                    predictions.append({
                        "breed": breed,
                        "probability": probability
                    })

        # If no prediction results, add a default prediction
        if not predictions:
            predictions.append({
                "breed": "Unknown",
                "probability": 100.0
            })

        # Get breed information
        breed_info = {
            "name": predictions[0]["breed"],
            "characteristics": get_breed_characteristics(predictions[0]["breed"]),
            "personality": get_breed_personality(predictions[0]["breed"]),
            "care": get_breed_care(predictions[0]["breed"])
        }

        # Save prediction history to MySQL
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO histories (user_id, image_path, predictions) 
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (
                    session['user_id'],
                    os.path.join('uploads', filename),  # Store relative path
                    json.dumps(predictions)
                ))
                conn.commit()
        finally:
            conn.close()

        return jsonify({
            'predictions': predictions,
            'breed_info': breed_info
        })

    except Exception as e:
        print(f"Error in predict: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Get cat breed characteristics information
def get_breed_characteristics(breed):
    characteristics = {
        'Abyssinian': {
            'size': 'Medium',
            'coat': 'Short, fine, close-lying',
            'color': 'Ruddy, red, blue, fawn',
            'lifespan': '12-16 years',
            'origin': 'Egypt/Ethiopia'
        },
        'American Curl': {
            'size': 'Small to medium',
            'coat': 'Short to semi-long, silky',
            'color': 'All colors and patterns',
            'lifespan': '12-16 years',
            'origin': 'United States'
        },
        'American Shorthair': {
            'size': 'Medium to large',
            'coat': 'Short, thick, dense',
            'color': 'Over 80 colors and patterns',
            'lifespan': '15-20 years',
            'origin': 'United States'
        },
        'Bengal': {
            'size': 'Medium to large',
            'coat': 'Short, dense, luxurious',
            'color': 'Brown spotted/marbled, snow spotted/marbled, silver spotted/marbled',
            'lifespan': '12-16 years',
            'origin': 'United States'
        },
        'Birman': {
            'size': 'Medium to large',
            'coat': 'Medium-long, silky',
            'color': 'Point colors with white gloves',
            'lifespan': '12-16 years',
            'origin': 'Burma (Myanmar)'
        },
        'Bombay': {
            'size': 'Medium',
            'coat': 'Short, fine, satin-like',
            'color': 'Black',
            'lifespan': '12-16 years',
            'origin': 'United States'
        },
        'British Shorthair': {
            'size': 'Medium to large',
            'coat': 'Short, dense, plush',
            'color': 'Many colors, blue (gray) most common',
            'lifespan': '12-17 years',
            'origin': 'United Kingdom'
        },
        'Egyptian Mau': {
            'size': 'Medium',
            'coat': 'Short, fine, silky',
            'color': 'Silver, bronze, smoke',
            'lifespan': '12-15 years',
            'origin': 'Egypt'
        },
        'Exotic Shorthair': {
            'size': 'Medium to large',
            'coat': 'Short, thick, plush',
            'color': 'All colors and patterns',
            'lifespan': '12-14 years',
            'origin': 'United States'
        },
        'Himalayan': {
            'size': 'Medium to large',
            'coat': 'Long, thick, silky',
            'color': 'Point colors',
            'lifespan': '9-15 years',
            'origin': 'United States/United Kingdom'
        },
        'Maine Coon': {
            'size': 'Large to very large',
            'coat': 'Medium to long, shaggy',
            'color': 'Over 75 color combinations',
            'lifespan': '12-15 years',
            'origin': 'United States'
        },
        'Manx': {
            'size': 'Medium',
            'coat': 'Double coat, medium-long to short',
            'color': 'Many colors and patterns',
            'lifespan': '8-14 years',
            'origin': 'Isle of Man'
        },
        'Munchkin': {
            'size': 'Small to medium',
            'coat': 'Short to long',
            'color': 'All colors and patterns',
            'lifespan': '12-15 years',
            'origin': 'United States'
        },
        'Norwegian Forest': {
            'size': 'Large',
            'coat': 'Long, dense, water-resistant double coat',
            'color': 'Many colors and patterns',
            'lifespan': '14-16 years',
            'origin': 'Norway'
        },
        'Persian': {
            'size': 'Medium to large',
            'coat': 'Long, thick, luxurious',
            'color': 'Many colors and patterns',
            'lifespan': '10-17 years',
            'origin': 'Persia (Iran)'
        },
        'Ragdoll': {
            'size': 'Large to very large',
            'coat': 'Semi-long, silky, plush',
            'color': 'Point colors',
            'lifespan': '12-17 years',
            'origin': 'United States'
        },
        'Russian Blue': {
            'size': 'Medium',
            'coat': 'Short, dense, plush double coat',
            'color': 'Blue-gray with silver sheen',
            'lifespan': '15-20 years',
            'origin': 'Russia'
        },
        'Scottish Fold': {
            'size': 'Medium',
            'coat': 'Short to medium-long',
            'color': 'All colors and patterns',
            'lifespan': '11-14 years',
            'origin': 'Scotland'
        },
        'Siamese': {
            'size': 'Medium',
            'coat': 'Short, fine, glossy',
            'color': 'Point colors',
            'lifespan': '12-20 years',
            'origin': 'Thailand (formerly Siam)'
        },
        'Sphynx': {
            'size': 'Medium',
            'coat': 'Hairless (actually fine down)',
            'color': 'All colors and patterns (skin)',
            'lifespan': '8-14 years',
            'origin': 'Canada'
        }
    }
    
    return characteristics.get(breed, {
        'size': 'Varies',
        'coat': 'Varies',
        'color': 'Various colors and patterns',
        'lifespan': '12-15 years average',
        'origin': 'Unknown'
    })

# Get cat breed personality information
def get_breed_personality(breed):
    personalities = {
        'Abyssinian': ['Active', 'Intelligent', 'Curious', 'Playful', 'Attention-seeking'],
        'American Curl': ['Affectionate', 'Playful', 'Adaptable', 'People-oriented', 'Curious'],
        'American Shorthair': ['Adaptable', 'Gentle', 'Playful', 'Calm', 'Good with children'],
        'Bengal': ['Active', 'Energetic', 'Intelligent', 'Playful', 'Curious'],
        'Birman': ['Gentle', 'Affectionate', 'Quiet', 'Patient', 'Playful'],
        'Bombay': ['Affectionate', 'Playful', 'Attention-seeking', 'Intelligent', 'Social'],
        'British Shorthair': ['Easygoing', 'Calm', 'Independent', 'Loyal', 'Reserved'],
        'Egyptian Mau': ['Active', 'Agile', 'Intelligent', 'Loyal', 'Moderately vocal'],
        'Exotic Shorthair': ['Gentle', 'Calm', 'Playful', 'Affectionate', 'Loyal'],
        'Himalayan': ['Sweet', 'Gentle', 'Quiet', 'Affectionate', 'Playful'],
        'Maine Coon': ['Gentle', 'Friendly', 'Intelligent', 'Playful', 'Dog-like'],
        'Manx': ['Playful', 'Intelligent', 'Affectionate', 'Dog-like', 'Social'],
        'Munchkin': ['Outgoing', 'Intelligent', 'Playful', 'People-oriented', 'Curious'],
        'Norwegian Forest': ['Gentle', 'Friendly', 'Independent', 'Intelligent', 'Adaptable'],
        'Persian': ['Sweet', 'Gentle', 'Quiet', 'Affectionate', 'Relaxed'],
        'Ragdoll': ['Gentle', 'Relaxed', 'Affectionate', 'Friendly', 'Quiet'],
        'Russian Blue': ['Gentle', 'Quiet', 'Intelligent', 'Playful', 'Reserved'],
        'Scottish Fold': ['Sweet', 'Adaptable', 'Intelligent', 'Playful', 'Affectionate'],
        'Siamese': ['Vocal', 'Intelligent', 'Affectionate', 'Social', 'Demanding'],
        'Sphynx': ['Energetic', 'Mischievous', 'Inquisitive', 'Affectionate', 'Friendly']
    }
    
    return personalities.get(breed, ['Varies by individual cat', 'Unique personality traits', 'May be influenced by upbringing'])

# Get cat breed care information
def get_breed_care(breed):
    care_info = {
        'Abyssinian': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'High - needs plenty of play and activity',
            'health_concerns': 'Dental disease, renal amyloidosis',
            'diet': 'High-quality protein-rich diet'
        },
        'American Curl': {
            'grooming': 'Low to moderate, weekly brushing',
            'exercise': 'Moderate - enjoys interactive play',
            'health_concerns': 'Generally healthy, few breed-specific issues',
            'diet': 'Balanced diet appropriate for age and activity level'
        },
        'American Shorthair': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'Moderate - enjoys play but also relaxation',
            'health_concerns': 'Hypertrophic cardiomyopathy, obesity',
            'diet': 'Controlled portions to prevent obesity'
        },
        'Bengal': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'Very high - needs extensive play and climbing opportunities',
            'health_concerns': 'Hypertrophic cardiomyopathy, progressive retinal atrophy',
            'diet': 'High-quality protein-rich diet'
        },
        'Birman': {
            'grooming': 'Moderate, regular brushing to prevent matting',
            'exercise': 'Moderate - enjoys play but not hyperactive',
            'health_concerns': 'Hypertrophic cardiomyopathy, kidney disease',
            'diet': 'Balanced diet with attention to kidney health'
        },
        'Bombay': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'Moderate to high - enjoys interactive play',
            'health_concerns': 'Craniofacial defects, hypertrophic cardiomyopathy',
            'diet': 'Balanced diet appropriate for age and activity level'
        },
        'British Shorthair': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'Low to moderate - not very active',
            'health_concerns': 'Hypertrophic cardiomyopathy, obesity',
            'diet': 'Controlled portions to prevent obesity'
        },
        'Egyptian Mau': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'High - very active and athletic',
            'health_concerns': 'Leukodystrophy, hypertrophic cardiomyopathy',
            'diet': 'High-quality protein-rich diet'
        },
        'Exotic Shorthair': {
            'grooming': 'Moderate, regular brushing',
            'exercise': 'Low - generally sedentary',
            'health_concerns': 'Brachycephalic issues, polycystic kidney disease',
            'diet': 'Controlled portions to prevent obesity'
        },
        'Himalayan': {
            'grooming': 'High maintenance, daily brushing',
            'exercise': 'Low - generally sedentary',
            'health_concerns': 'Brachycephalic issues, polycystic kidney disease',
            'diet': 'Balanced diet with attention to kidney health'
        },
        'Maine Coon': {
            'grooming': 'Moderate to high, regular brushing',
            'exercise': 'Moderate - playful but not hyperactive',
            'health_concerns': 'Hypertrophic cardiomyopathy, hip dysplasia',
            'diet': 'High-quality diet appropriate for large breed'
        },
        'Manx': {
            'grooming': 'Moderate, regular brushing',
            'exercise': 'Moderate - enjoys play and exploration',
            'health_concerns': 'Manx syndrome, arthritis',
            'diet': 'Balanced diet appropriate for age and activity level'
        },
        'Munchkin': {
            'grooming': 'Low to moderate, depending on coat length',
            'exercise': 'Moderate - surprisingly agile despite short legs',
            'health_concerns': 'Lordosis, pectus excavatum',
            'diet': 'Balanced diet appropriate for age and activity level'
        },
        'Norwegian Forest': {
            'grooming': 'High maintenance, regular brushing especially during shedding seasons',
            'exercise': 'Moderate - enjoys climbing and exploration',
            'health_concerns': 'Glycogen storage disease, hypertrophic cardiomyopathy',
            'diet': 'High-quality diet appropriate for large breed'
        },
        'Persian': {
            'grooming': 'Very high maintenance, daily brushing',
            'exercise': 'Low - generally sedentary',
            'health_concerns': 'Brachycephalic issues, polycystic kidney disease',
            'diet': 'Balanced diet with attention to kidney health'
        },
        'Ragdoll': {
            'grooming': 'Moderate, regular brushing',
            'exercise': 'Low to moderate - not very active',
            'health_concerns': 'Hypertrophic cardiomyopathy, bladder stones',
            'diet': 'Balanced diet with attention to urinary health'
        },
        'Russian Blue': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'Moderate - enjoys play but also relaxation',
            'health_concerns': 'Generally healthy, bladder issues',
            'diet': 'Balanced diet with attention to urinary health'
        },
        'Scottish Fold': {
            'grooming': 'Low to moderate, depending on coat length',
            'exercise': 'Moderate - enjoys play but not hyperactive',
            'health_concerns': 'Osteochondrodysplasia, degenerative joint disease',
            'diet': 'Balanced diet with joint supplements may be beneficial'
        },
        'Siamese': {
            'grooming': 'Low maintenance, weekly brushing',
            'exercise': 'High - very active and vocal',
            'health_concerns': 'Respiratory issues, amyloidosis',
            'diet': 'High-quality protein-rich diet'
        },
        'Sphynx': {
            'grooming': 'High maintenance, weekly bathing',
            'exercise': 'High - very active and playful',
            'health_concerns': 'Hypertrophic cardiomyopathy, skin issues',
            'diet': 'High-calorie diet to maintain body temperature'
        }
    }
    
    return care_info.get(breed, {
        'grooming': 'Varies based on coat type',
        'exercise': 'Regular play and enrichment recommended',
        'health_concerns': 'Regular veterinary check-ups recommended',
        'diet': 'High-quality balanced diet appropriate for age and activity level'
    })

# Route: Statistics page
@app.route('/statistics')
@login_required
def statistics():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            # Get personal statistics
            personal_stats = get_personal_statistics(cursor, session['user_id'])
            
            # Get platform statistics
            platform_stats = get_platform_statistics(cursor)
            
            return render_template('statistics.html', 
                                  personal_stats=personal_stats, 
                                  platform_stats=platform_stats, 
                                  current_user=get_current_user())
    finally:
        conn.close()

# Get personal statistics
def get_personal_statistics(cursor, user_id):
    # Get total recognition count
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM histories
        WHERE user_id = %s
    """, (user_id,))
    total_recognitions = cursor.fetchone()['total']
    
    # Get recognized breed statistics
    cursor.execute("""
        SELECT h.id, h.predictions
        FROM histories h
        WHERE h.user_id = %s
        ORDER BY h.created_at DESC
    """, (user_id,))
    
    history_records = cursor.fetchall()
    
    # Process breed statistics
    breed_counts = {}
    
    for record in history_records:
        # Process breed data
        try:
            predictions = json.loads(record['predictions'])
            if predictions and len(predictions) > 0:
                top_breed = predictions[0]['breed']
                if top_breed in breed_counts:
                    breed_counts[top_breed] += 1
                else:
                    breed_counts[top_breed] = 1
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    
    # Get most recognized breed
    most_recognized = "None"
    if breed_counts:
        most_recognized = max(breed_counts.items(), key=lambda x: x[1])[0]
    
    # Sort breed statistics
    sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
    top_breeds = []
    
    # Calculate percentages
    for breed, count in sorted_breeds[:10]:  # Only take top 10
        percentage = (count / total_recognitions) * 100 if total_recognitions > 0 else 0
        top_breeds.append({
            'name': breed,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    # Prepare chart data
    chart_data = {
        'breed_labels': [breed['name'] for breed in top_breeds],
        'breed_counts': [breed['count'] for breed in top_breeds],
    }
    
    # Get date range for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Use SQL directly to query daily personal recognition count
    cursor.execute("""
        SELECT 
            DATE_FORMAT(created_at, '%%Y-%%m-%%d') as date,
            COUNT(*) as count
        FROM 
            histories
        WHERE 
            user_id = %s AND created_at >= %s
        GROUP BY 
            DATE_FORMAT(created_at, '%%Y-%%m-%%d')
        ORDER BY 
            date
    """, (user_id, start_date))
    
    # Convert query results to dictionary for easy processing
    daily_counts = {}
    for row in cursor.fetchall():
        daily_counts[row['date']] = row['count']
    
    # Prepare activity chart data (past 30 days)
    dates = []
    counts = []
    
    # Fill in data for each day, if no record then 0
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        dates.append(date_str)
        counts.append(daily_counts.get(date_str, 0))
        current_date += timedelta(days=1)
    
    chart_data['activity_labels'] = dates
    chart_data['activity_counts'] = counts
    
    return {
        'total_recognitions': total_recognitions,
        'unique_breeds': len(breed_counts),
        'most_recognized': most_recognized,
        'top_breeds': top_breeds,
        'chart_data': chart_data
    }

# Get platform statistics
def get_platform_statistics(cursor):
    # Get total recognition count
    cursor.execute("SELECT COUNT(*) as total FROM histories")
    total_recognitions = cursor.fetchone()['total']
    
    # Get total user count
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()['total']
    
    # Get platform breed statistics
    cursor.execute("""
        SELECT h.predictions
        FROM histories h
        ORDER BY h.created_at DESC
    """)
    
    history_records = cursor.fetchall()
    
    # Process breed statistics
    breed_counts = {}
    
    for record in history_records:
        # Process breed data
        try:
            predictions = json.loads(record['predictions'])
            if predictions and len(predictions) > 0:
                top_breed = predictions[0]['breed']
                if top_breed in breed_counts:
                    breed_counts[top_breed] += 1
                else:
                    breed_counts[top_breed] = 1
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    
    # Get most popular breed
    most_popular = "None"
    if breed_counts:
        most_popular = max(breed_counts.items(), key=lambda x: x[1])[0]
    
    # Sort breed statistics
    sorted_breeds = sorted(breed_counts.items(), key=lambda x: x[1], reverse=True)
    top_breeds = []
    
    # Calculate percentages
    for breed, count in sorted_breeds[:10]:  # Only take top 10
        percentage = (count / total_recognitions) * 100 if total_recognitions > 0 else 0
        top_breeds.append({
            'name': breed,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    # Prepare chart data
    chart_data = {
        'breed_labels': [breed['name'] for breed in top_breeds],
        'breed_counts': [breed['count'] for breed in top_breeds],
    }
    
    # Get date range for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Use SQL directly to query daily recognition count
    cursor.execute("""
        SELECT 
            DATE_FORMAT(created_at, '%%Y-%%m-%%d') as date,
            COUNT(*) as count
        FROM 
            histories
        WHERE 
            created_at >= %s
        GROUP BY 
            DATE_FORMAT(created_at, '%%Y-%%m-%%d')
        ORDER BY 
            date
    """, (start_date,))
    
    # Convert query results to dictionary for easy processing
    daily_counts = {}
    for row in cursor.fetchall():
        daily_counts[row['date']] = row['count']
    
    # Prepare activity chart data (past 30 days)
    dates = []
    counts = []
    
    # Fill in data for each day, if no record then 0
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        dates.append(date_str)
        counts.append(daily_counts.get(date_str, 0))
        current_date += timedelta(days=1)
    
    chart_data['activity_labels'] = dates
    chart_data['activity_counts'] = counts
    
    return {
        'total_recognitions': total_recognitions,
        'total_users': total_users,
        'most_popular': most_popular,
        'top_breeds': top_breeds,
        'chart_data': chart_data
    }

# Route: Update personal information
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        bio = request.form.get('bio')
        phone = request.form.get('phone')
        
        # Get current user information
        current_user = get_current_user()
        
        # Check if username and email are already used by other users
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                # Check username
                if username != current_user['username']:
                    cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, current_user['id']))
                    if cursor.fetchone():
                        flash('Username already in use')
                        return redirect(url_for('index'))
                
                # Check email
                if email != current_user['email']:
                    cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, current_user['id']))
                    if cursor.fetchone():
                        flash('Email already in use')
                        return redirect(url_for('index'))
                
                # Handle avatar upload
                avatar_path = current_user['avatar_path']
                if 'avatar' in request.files:
                    avatar_file = request.files['avatar']
                    if avatar_file and avatar_file.filename != '' and allowed_avatar_file(avatar_file.filename):
                        # Generate safe filename
                        filename = secure_filename(avatar_file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"avatar_{current_user['id']}_{timestamp}_{filename}"
                        
                        # Save file
                        filepath = os.path.join(app.config['AVATARS_FOLDER'], filename)
                        avatar_file.save(filepath)
                        
                        # Update avatar path - only store filename, not 'avatars/' prefix
                        avatar_path = filename
                
                # Update user information
                sql = """
                    UPDATE users 
                    SET username = %s, email = %s, bio = %s, phone = %s, avatar_path = %s
                    WHERE id = %s
                """
                cursor.execute(sql, (username, email, bio, phone, avatar_path, current_user['id']))
                conn.commit()
                
                flash('Profile updated successfully')
                return redirect(url_for('index'))
        finally:
            conn.close()
    
    return redirect(url_for('index'))

# Route: Change password
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify new password
        if new_password != confirm_password:
            flash('New password and confirmation do not match')
            return redirect(url_for('index'))
        
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                # Get current user's password hash
                cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
                user_data = cursor.fetchone()
                
                # Verify current password
                if not check_password_hash(user_data['password_hash'], current_password):
                    flash('Current password is incorrect')
                    return redirect(url_for('index'))
                
                # Update password
                password_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", 
                              (password_hash, session['user_id']))
                conn.commit()
                
                flash('Password updated successfully')
                return redirect(url_for('index'))
        finally:
            conn.close()
    
    return redirect(url_for('index'))

# 添加一个路由来提供dataset目录下的图片
@app.route('/dataset/<path:filename>')
@login_required
def dataset_files(filename):
    return send_from_directory('.', os.path.join('dataset', filename))

# 生成品种评分
def generate_breed_ratings(breed_name):
    # 不同品种的默认评分
    breed_ratings = {
        'Abyssinian': {'friendliness': 5, 'activity_level': 5, 'grooming_needs': 2, 'intelligence': 5},
        'American Curl': {'friendliness': 5, 'activity_level': 4, 'grooming_needs': 3, 'intelligence': 4},
        'American Shorthair': {'friendliness': 4, 'activity_level': 3, 'grooming_needs': 2, 'intelligence': 3},
        'Bengal': {'friendliness': 4, 'activity_level': 5, 'grooming_needs': 2, 'intelligence': 5},
        'Birman': {'friendliness': 5, 'activity_level': 3, 'grooming_needs': 3, 'intelligence': 4},
        'Bombay': {'friendliness': 5, 'activity_level': 4, 'grooming_needs': 2, 'intelligence': 4},
        'British Shorthair': {'friendliness': 4, 'activity_level': 2, 'grooming_needs': 2, 'intelligence': 3},
        'Egyptian Mau': {'friendliness': 3, 'activity_level': 5, 'grooming_needs': 2, 'intelligence': 5},
        'Exotic Shorthair': {'friendliness': 5, 'activity_level': 2, 'grooming_needs': 3, 'intelligence': 3},
        'Himalayan': {'friendliness': 4, 'activity_level': 2, 'grooming_needs': 5, 'intelligence': 3},
        'Maine Coon': {'friendliness': 5, 'activity_level': 4, 'grooming_needs': 4, 'intelligence': 4},
        'Manx': {'friendliness': 5, 'activity_level': 4, 'grooming_needs': 3, 'intelligence': 4},
        'Munchkin': {'friendliness': 5, 'activity_level': 4, 'grooming_needs': 3, 'intelligence': 4},
        'Norwegian Forest': {'friendliness': 4, 'activity_level': 3, 'grooming_needs': 4, 'intelligence': 4},
        'Persian': {'friendliness': 4, 'activity_level': 1, 'grooming_needs': 5, 'intelligence': 3},
        'Ragdoll': {'friendliness': 5, 'activity_level': 2, 'grooming_needs': 3, 'intelligence': 3},
        'Russian Blue': {'friendliness': 3, 'activity_level': 3, 'grooming_needs': 2, 'intelligence': 4},
        'Scottish Fold': {'friendliness': 5, 'activity_level': 3, 'grooming_needs': 3, 'intelligence': 4},
        'Siamese': {'friendliness': 4, 'activity_level': 5, 'grooming_needs': 2, 'intelligence': 5},
        'Sphynx': {'friendliness': 5, 'activity_level': 5, 'grooming_needs': 3, 'intelligence': 5}
    }
    
    # 返回品种评分，如果没有默认评分则返回一个中等评分
    return breed_ratings.get(breed_name, {'friendliness': 4, 'activity_level': 3, 'grooming_needs': 3, 'intelligence': 4})

# 获取所有有图片的猫咪品种
def get_breeds_with_images():
    # 从训练数据集目录获取品种
    dataset_dir = os.path.join('dataset', 'train')
    
    # 获取所有猫咪品种（从训练目录的文件夹名称）
    breed_labels = []
    for item in os.listdir(dataset_dir):
        if os.path.isdir(os.path.join(dataset_dir, item)):
            breed_labels.append(item)
    
    breeds_with_images = []
    breed_images = {}
    
    for breed_name in breed_labels:
        # 为每个品种从训练数据集中随机选择一张图片
        breed_dir = os.path.join(dataset_dir, breed_name)
        image_files = [f for f in os.listdir(breed_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if image_files:
            # 处理品种名称映射（Bristish -> British, Regdoll -> Ragdoll）
            corrected_name = breed_name
            if breed_name == "Bristish Shorthair":
                corrected_name = "British Shorthair"
            elif breed_name == "Regdoll":
                corrected_name = "Ragdoll"
            
            breeds_with_images.append(corrected_name)
            
            # 随机选择一张图片而不是使用第一张
            random_image = random.choice(image_files)
            breed_images[corrected_name] = {
                'file': random_image,
                'path': os.path.join('dataset', 'train', breed_name, random_image)
            }
    
    return breeds_with_images, breed_images

if __name__ == '__main__':
    # Load model when starting
    load_model()
    # Warm up model
    warmup_model()
    app.run(debug=True) 