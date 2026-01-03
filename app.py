from flask import Flask, render_template, redirect, url_for, request, session, flash
import joblib
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the model
model = joblib.load('model_joblib_gr')

# Conversion rate (1 USD to INR)
usd_to_inr = 83.00

# Database connection
def connect_db():
    conn = sqlite3.connect('users.db')
    return conn

# Create Users Table
def create_users_table():
    with connect_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')

create_users_table()

# Landing page route
@app.route('/')
def landing():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('landing.html')

# Login page route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with connect_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user and check_password_hash(user[2], password):
                session['username'] = username
                return redirect(url_for('index'))
            else:
                flash('Invalid Credentials', 'danger')

    return render_template('login.html')

# Signup page route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        with connect_db() as conn:
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                flash('Registration Successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists!', 'danger')

    return render_template('signup.html')

# Prediction page route (home page after login)
@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Prediction processing route
@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        age = float(request.form['age'])
        sex = float(request.form['sex'])
        bmi = float(request.form['bmi'])
        children = float(request.form['children'])
        smoker = float(request.form['smoker'])
        region = float(request.form['region'])

        # Create a DataFrame for the input
        input_data = pd.DataFrame([[age, sex, bmi, children, smoker, region]], 
                                  columns=['age', 'sex', 'bmi', 'children', 'smoker', 'region'])

        # Make a prediction
        prediction_usd = model.predict(input_data)

        # Convert the prediction to INR
        prediction_inr = prediction_usd[0] * usd_to_inr

        # Return the prediction text in INR
        return render_template('index.html', prediction_text=f'Estimated Insurance Cost: ₹{prediction_inr:.2f}')
    except Exception as e:
        print("Error:", e)
        return render_template('index.html', prediction_text="An error occurred. Please check your input values.")

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
