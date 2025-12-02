from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import secrets
import bcrypt
import re
from datetime import datetime, timedelta

app = Flask(__name__)
# Get secret key from environment variable, otherwise generate a random one
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Session security configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

# Security Manager Class
class SecurityManager:
    @staticmethod
    def hash_password(password):
        """Hash password"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_]+$', username))
    
    @staticmethod
    def validate_password(password):
        """Validate password format"""
        return password and len(password) >= 6
    
    @staticmethod
    def validate_food_name(food_name):
        """Validate food name"""
        if not food_name or len(food_name) > 50:
            return False
        return bool(re.match(r'^[a-zA-Z0-9\s\-]+$', food_name))
    
    @staticmethod
    def sanitize_input(input_str):
        """Sanitize user input"""
        if not input_str:
            return ""
        # Remove dangerous characters, keep basic characters
        cleaned = re.sub(r'[<>"\'&;]', '', str(input_str))
        return cleaned.strip()
    
    @staticmethod
    def safe_float_convert(value, min_val=None, max_val=None):
        """Safely convert to float"""
        try:
            if value is None or value == '':
                return None
            num = float(value)
            if min_val is not None and num < min_val:
                return min_val
            if max_val is not None and num > max_val:
                return max_val
            return num
        except (ValueError, TypeError):
            return None

# Food Database
food_database = {
    'Chicken Breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6, 'sugar': 0},
    'Brown Rice': {'calories': 216, 'protein': 4.5, 'carbs': 45, 'fat': 1.8, 'sugar': 0.4},
    'Broccoli': {'calories': 34, 'protein': 2.8, 'carbs': 6.6, 'fat': 0.4, 'sugar': 1.7},
    'Salmon': {'calories': 208, 'protein': 22, 'carbs': 0, 'fat': 13, 'sugar': 0},
    'Avocado': {'calories': 160, 'protein': 2, 'carbs': 8.5, 'fat': 14.7, 'sugar': 0.7},
    'Whole Wheat Bread': {'calories': 250, 'protein': 9, 'carbs': 45, 'fat': 3},
    'Eggs': {'calories': 140, 'protein': 13, 'carbs': 1, 'fat': 10},
    'Milk': {'calories': 60, 'protein': 3, 'carbs': 5, 'fat': 3},
    'Oatmeal': {'calories': 380, 'protein': 13, 'carbs': 68, 'fat': 7},
    'Nuts': {'calories': 600, 'protein': 20, 'carbs': 20, 'fat': 50},
    'Tofu': {'calories': 76, 'protein': 8, 'carbs': 1.9, 'fat': 4.8},
    'Banana': {'calories': 89, 'protein': 1.1, 'carbs': 22.8, 'fat': 0.3, 'sugar': 12.2},
    'Apple': {'calories': 52, 'protein': 0.3, 'carbs': 13.8, 'fat': 0.2, 'sugar': 10.4},
    'Orange': {'calories': 47, 'protein': 0.9, 'carbs': 11.8, 'fat': 0.1, 'sugar': 9.4},
    'Carrot': {'calories': 41, 'protein': 0.9, 'carbs': 9.6, 'fat': 0.2, 'sugar': 4.7}
}

# Diet Plan Templates
diet_plan_templates = {
    'weight-loss': [
        {'name': 'Breakfast', 'calories': 400, 'protein': 20, 'carbs': 40, 'fat': 15},
        {'name': 'Lunch', 'calories': 500, 'protein': 30, 'carbs': 50, 'fat': 20},
        {'name': 'Dinner', 'calories': 400, 'protein': 25, 'carbs': 30, 'fat': 15}
    ],
    'muscle-gain': [
        {'name': 'Breakfast', 'calories': 600, 'protein': 40, 'carbs': 60, 'fat': 20},
        {'name': 'Lunch', 'calories': 700, 'protein': 50, 'carbs': 70, 'fat': 25},
        {'name': 'Dinner', 'calories': 600, 'protein': 45, 'carbs': 50, 'fat': 20}
    ],
    'maintenance': [
        {'name': 'Breakfast', 'calories': 500, 'protein': 25, 'carbs': 50, 'fat': 20},
        {'name': 'Lunch', 'calories': 600, 'protein': 35, 'carbs': 60, 'fat': 25},
        {'name': 'Dinner', 'calories': 500, 'protein': 30, 'carbs': 40, 'fat': 20}
    ]
}

class UserManager:
    def __init__(self):
        self.data_dir = 'data'
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self._ensure_data_dir()
        self.users = self.load_users()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_users(self):
        """Safely load user data"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    if not isinstance(users, list):
                        print("Warning: User data format error, reset to empty list")
                        return []
                    return users
            return []
        except Exception as e:
            print(f"Failed to load user data: {e}")
            return []
    
    def save_users(self):
        """Safely save user data"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save user data: {e}")
            return False
    
    def register(self, username, password, nickname="", height=None, weight=None, target_weight=None):
        """Secure user registration"""
        try:
            # Input validation
            if not SecurityManager.validate_username(username):
                return False, "Invalid username format (3-20 characters: letters, numbers, underscore)"
            
            if not SecurityManager.validate_password(password):
                return False, "Password must be at least 6 characters"
            
            # Check if username already exists
            for user in self.users:
                if user['username'] == username:
                    return False, "Username already exists"
            
            # Sanitize input
            nickname = SecurityManager.sanitize_input(nickname)
            height = SecurityManager.safe_float_convert(height, 100, 250)
            weight = SecurityManager.safe_float_convert(weight, 30, 200)
            target_weight = SecurityManager.safe_float_convert(target_weight, 30, 200)
            
            # Create new user (password hashing)
            new_user = {
                'username': username,
                'password': SecurityManager.hash_password(password),
                'nickname': nickname,
                'height': height,
                'weight': weight,
                'target_weight': target_weight,
                'goal': 'maintenance',
                'register_time': datetime.now().isoformat()
            }
            
            self.users.append(new_user)
            if self.save_users():
                return True, "Registration successful"
            else:
                return False, "Registration failed: data save error"
                
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def login(self, username, password):
        """Secure user login"""
        try:
            for user in self.users:
                if user['username'] == username:
                    if SecurityManager.verify_password(password, user['password']):
                        # Don't return password field
                        user_data = user.copy()
                        user_data.pop('password', None)
                        return True, user_data
            return False, "Incorrect username or password"
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def update_profile(self, username, **kwargs):
        """Securely update user profile"""
        try:
            for user in self.users:
                if user['username'] == username:
                    # Validate and sanitize input
                    if 'nickname' in kwargs:
                        kwargs['nickname'] = SecurityManager.sanitize_input(kwargs['nickname'])
                    if 'height' in kwargs:
                        kwargs['height'] = SecurityManager.safe_float_convert(kwargs['height'], 100, 250)
                    if 'weight' in kwargs:
                        kwargs['weight'] = SecurityManager.safe_float_convert(kwargs['weight'], 30, 200)
                    if 'target_weight' in kwargs:
                        kwargs['target_weight'] = SecurityManager.safe_float_convert(kwargs['target_weight'], 30, 200)
                    if 'goal' in kwargs and kwargs['goal'] not in ['weight-loss', 'muscle-gain', 'maintenance']:
                        return False, "Invalid goal type"
                    
                    for key, value in kwargs.items():
                        if value is not None:
                            user[key] = value
                    
                    if self.save_users():
                        return True, "Profile updated successfully"
                    else:
                        return False, "Profile update failed: data save error"
            return False, "User does not exist"
        except Exception as e:
            return False, f"Profile update failed: {str(e)}"

class DietPlanGenerator:
    def __init__(self):
        self.food_database = food_database
    
    def calculate_daily_calories(self, user_data):
        """Calculate daily required calories"""
        try:
            height = user_data.get('height') or 170
            weight = user_data.get('weight') or 65
            goal = user_data.get('goal', 'maintenance')
            
            # Basal metabolic rate calculation
            base_calories = 10 * weight + 6.25 * height - 5 * 25 + 5
            
            # Adjust based on goal
            if goal == 'weight-loss':
                base_calories -= 400
            elif goal == 'muscle-gain':
                base_calories += 300
            
            return max(1200, int(base_calories))  # Minimum 1200 calories
        except Exception:
            return 2000  # Default value
    
    def generate_diet_plan(self, user_data):
        """Generate diet plan"""
        try:
            daily_calories = self.calculate_daily_calories(user_data)
            goal = user_data.get('goal', 'maintenance')
            
            # Use template
            template = diet_plan_templates.get(goal, diet_plan_templates['maintenance'])
            total_template_calories = sum(meal['calories'] for meal in template)
            calorie_ratio = daily_calories / total_template_calories
            
            # Generate plan based on template
            basic_plan = []
            for meal in template:
                basic_plan.append({
                    'name': meal['name'],
                    'calories': max(100, round(meal['calories'] * calorie_ratio)),
                    'protein': max(5, round(meal['protein'] * calorie_ratio)),
                    'carbs': max(10, round(meal['carbs'] * calorie_ratio)),
                    'fat': max(5, round(meal['fat'] * calorie_ratio))
                })
            
            return basic_plan
        except Exception:
            return []
    
    def analyze_food(self, food_name, amount=100):
        """Safely analyze food nutrition"""
        try:
            # Validate input
            if not SecurityManager.validate_food_name(food_name):
                return False, "Invalid food name"
            
            amount = SecurityManager.safe_float_convert(amount, 1, 10000) or 100
            
            if food_name in self.food_database:
                food = self.food_database[food_name]
                ratio = amount / 100
                
                analysis = {
                    'calories': max(0, round(food['calories'] * ratio)),
                    'protein': max(0, round(food['protein'] * ratio * 10) / 10),
                    'carbs': max(0, round(food['carbs'] * ratio * 10) / 10),
                    'fat': max(0, round(food['fat'] * ratio * 10) / 10),
                    'sugar': max(0, round(food.get('sugar', 0) * ratio * 10) / 10)
                }
                
                return True, analysis
            else:
                return False, "Sorry, this food was not found in the database"
        except Exception as e:
            return False, f"Analysis failed: {str(e)}"
    
    def calculate_bmi(self, height, weight):
        """Calculate BMI"""
        try:
            if not height or not weight:
                return None
            
            height_in_meters = height / 100
            bmi = weight / (height_in_meters * height_in_meters)
            return max(10, min(50, round(bmi, 1)))  # Limit range
        except Exception:
            return None
    
    def get_bmi_status(self, bmi):
        """Get BMI status"""
        if bmi is None:
            return "Height and weight not set"
        
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 24:
            return "Normal weight"
        elif bmi < 28:
            return "Overweight"
        else:
            return "Obese"

# Initialize managers
user_manager = UserManager()
diet_generator = DietPlanGenerator()

# Error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    print(f"Unhandled exception: {error}")
    return render_template('error.html', error=str(error)), 500

# Route definitions
@app.route('/')
def index():
    try:
        if 'user' in session:
            user = session['user']
            # Calculate BMI for homepage display
            bmi = diet_generator.calculate_bmi(user.get('height'), user.get('weight'))
            bmi_status = diet_generator.get_bmi_status(bmi)
            
            return render_template('index.html', 
                                 user=user, 
                                 bmi=bmi, 
                                 bmi_status=bmi_status,
                                 diet_generator=diet_generator)
        return redirect(url_for('login'))
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = SecurityManager.sanitize_input(request.form.get('username', ''))
            password = request.form.get('password', '')
            
            if not username or not password:
                return render_template('login.html', error="Please enter username and password")
            
            success, result = user_manager.login(username, password)
            if success:
                session.permanent = True
                session['user'] = result
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error=result)
        
        return render_template('login.html')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = SecurityManager.sanitize_input(request.form.get('username', ''))
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            nickname = SecurityManager.sanitize_input(request.form.get('nickname', ''))
            
            if not username or not password:
                return render_template('register.html', error="Please enter username and password")
            
            if password != confirm_password:
                return render_template('register.html', error="Passwords do not match")
            
            # Handle optional fields
            height = request.form.get('height')
            weight = request.form.get('weight')
            target_weight = request.form.get('target_weight')
            
            success, message = user_manager.register(
                username, password, nickname, height, weight, target_weight
            )
            
            if success:
                return redirect(url_for('login'))
            else:
                return render_template('register.html', error=message)
        
        return render_template('register.html')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/logout')
def logout():
    try:
        session.pop('user', None)
        return redirect(url_for('login'))
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    try:
        if 'user' not in session:
            return redirect(url_for('login'))
        
        message = None
        
        if request.method == 'POST':
            username = session['user']['username']
            nickname = request.form.get('nickname')
            height = request.form.get('height')
            weight = request.form.get('weight')
            target_weight = request.form.get('target_weight')
            goal = request.form.get('goal')
            
            # Prepare update data
            update_data = {}
            if nickname is not None:
                update_data['nickname'] = nickname
            if height:
                update_data['height'] = height
            if weight:
                update_data['weight'] = weight
            if target_weight:
                update_data['target_weight'] = target_weight
            if goal:
                update_data['goal'] = goal
            
            success, message = user_manager.update_profile(username, **update_data)
            if success:
                # Update user info in session
                for user in user_manager.users:
                    if user['username'] == username:
                        user_data = user.copy()
                        user_data.pop('password', None)
                        session['user'] = user_data
                        break
        
        # Calculate BMI for display
        user_data = session['user']
        bmi = diet_generator.calculate_bmi(user_data.get('height'), user_data.get('weight'))
        bmi_status = diet_generator.get_bmi_status(bmi)
        
        return render_template('profile.html', 
                             user=session['user'], 
                             message=message,
                             bmi=bmi,
                             bmi_status=bmi_status,
                             diet_generator=diet_generator)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/diet-plan')
def diet_plan():
    try:
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user = session['user']
        plan = diet_generator.generate_diet_plan(user)
        
        # Calculate BMI
        bmi = diet_generator.calculate_bmi(user.get('height'), user.get('weight'))
        bmi_status = diet_generator.get_bmi_status(bmi)
        
        return render_template('diet_plan.html', 
                             user=user, 
                             plan=plan, 
                             bmi=bmi, 
                             bmi_status=bmi_status,
                             diet_generator=diet_generator)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/nutrition-analysis', methods=['GET', 'POST'])
def nutrition_analysis():
    try:
        if 'user' not in session:
            return redirect(url_for('login'))
        
        analysis_result = None
        error = None
        
        if request.method == 'POST':
            food_name = SecurityManager.sanitize_input(request.form.get('food_name', ''))
            amount = request.form.get('amount', '100')
            
            if not food_name:
                error = "Please enter food name"
            else:
                success, result = diet_generator.analyze_food(food_name, amount)
                
                if success:
                    analysis_result = {
                        'food_name': food_name,
                        'amount': float(amount),
                        'nutrition': result
                    }
                else:
                    error = result
        
        return render_template('nutrition.html', 
                             user=session['user'],
                             analysis_result=analysis_result,
                             error=error,
                             diet_generator=diet_generator,
                             food_database=food_database)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

if __name__ == '__main__':
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)