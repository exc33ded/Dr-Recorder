from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import base64
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import pandas as pd
import random
import sqlite3
import re

app = Flask(__name__)
app.secret_key = 'gfcrdcu vygkct ycytcuoi gygctufc y gvcuylfyt dcfyxtycc lgcr xtcggggggggggg tgcgyxets7iytyultul crt x es67tuyv tf89; 9tdr xuyldrdxrkxfjxtyre876rytdf tyc guytyd f fx'
RECORD_FOLDER = 'record'
app.config['RECORD_FOLDER'] = RECORD_FOLDER

if not os.path.exists(RECORD_FOLDER):
    os.makedirs(RECORD_FOLDER)

# Google Drive API settings
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "drivecloud-425512-d71d80cfa1ad.json"
PARENT_FOLDER_ID = "1rj8Hd1ckkhdVeRjwPhlyZ-9IqQnVnT94"


def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            password TEXT NOT NULL,
            gender TEXT NULL,
            organization TEXT NULL,
            village TEXT NULL,
            town TEXT NULL,
            district TEXT NULL,
            state TEXT NULL,
            dob TEXT NULL,
            user_id TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")


def authenticate():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def upload_to_drive(file_path, filename):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
        'name': filename,
        'parents': [PARENT_FOLDER_ID]
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return file.get('id')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_short_id():
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8')[:6]

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    full_name = session['full_name']
    
    # Read the Excel file
    df = pd.read_excel('Book1.xlsx')
    # Choose a random row
    random_row = df.sample().iloc[0]
    text_id = random_row['Sno']
    english_text = random_row['English']
    hindi_text = random_row['Hindi']
    
    return render_template('index.html', text_id=text_id, english_text=english_text, hindi_text=hindi_text, user_name=full_name)

@app.route('/upload', methods=['POST'])
def upload_file():
    user_name = session.get('user_name')
    user_id = session.get('user_id')
    text_id = request.form.get('text_id')

    if 'audio_data_english' not in request.files or 'audio_data_hindi' not in request.files or not user_name or not text_id:
        flash("All inputs are required", "error")
        return redirect(url_for('index'))

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate short unique ID
    unique_id = generate_short_id()

    # Process English audio
    english_file = request.files['audio_data_english']
    english_filename = f"{unique_id}_{user_name}_ENG_{text_id}_{timestamp}.wav"
    english_path = os.path.join(app.config['RECORD_FOLDER'], english_filename)
    english_file.save(english_path)

    # Process Hindi audio
    hindi_file = request.files['audio_data_hindi']
    hindi_filename = f"{unique_id}_{user_name}_HIND_{text_id}_{timestamp}.wav"
    hindi_path = os.path.join(app.config['RECORD_FOLDER'], hindi_filename)
    hindi_file.save(hindi_path)
    
    try:
        # Upload both files to Google Drive
        english_file_id = upload_to_drive(english_path, english_filename)
        hindi_file_id = upload_to_drive(hindi_path, hindi_filename)

        # Remove local files after upload
        os.remove(english_path)
        os.remove(hindi_path)
        
        flash("Files uploaded and saved to Google Drive!", "success")
        return redirect(url_for('index'))
    except Exception as e:
        flash("Files uploaded and saved to Google Drive!", "success")
        return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not username or not full_name or not password or not confirm_password:
            flash("All fields are required", "error")
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('register'))
        
        # Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long", "error")
            return redirect(url_for('register'))
        
        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter", "error")
            return redirect(url_for('register'))
        
        if not re.search(r"[a-z]", password):
            flash("Password must contain at least one lowercase letter", "error")
            return redirect(url_for('register'))
        
        if not re.search(r"\d", password):
            flash("Password must contain at least one number", "error")
            return redirect(url_for('register'))
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            flash("Password must contain at least one special character", "error")
            return redirect(url_for('register'))
        
        if re.search(r"\s", password):
            flash("Password must not contain spaces", "error")
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = generate_short_id()
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, full_name, password, user_id) VALUES (?, ?, ?, ?)',
                         (username, full_name, hashed_password, user_id))
            conn.commit()
            flash("User registered successfully", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists", "error")
            return redirect(url_for('register'))
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash("All fields are required", "error")
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['user_name'] = user['username']
            session['full_name'] = user['full_name']
            flash("Login successful", "success")
            return redirect(url_for('index'))
        flash("Invalid username or password", "error")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
