from flask import Flask, render_template, jsonify, request 
from flask_sqlalchemy import SQLAlchemy 
import torch
import torchvision
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import os
import json
from werkzeug.security import generate_password_hash
import requests
from datetime import datetime, date 
import pandas as pd
import matplotlib.pyplot as plt
import http.client
import random
from functools import lru_cache
from datetime import timedelta
import re
import torch
import torch.nn as nn
import torchvision
import torchvision.models as models
import uuid


# import tensorflow 
# from tensorflow import keras
# from keras import models
# from keras.models import load_model


conn = http.client.HTTPSConnection("exercisedb-api1.p.rapidapi.com")
# Initialize Flask app first
USDA_API_KEY = "BQazS4IWGw7VKfBNHFbEJfLPab1wz1ROSZf1xS6K"
GOOGLE_API_KEY = "AIzaSyCOGmhXar6SGEizGd2vpxznQ7ESSoIPZNA"
GOOGLE_CSE_ID = "80aa6e2c5b0e44514"
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['DEBUG'] = True

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
# Model constants
MODEL_PATH = "foodtrainer.h5"
CLASSES_PATH = "foodtrainer_classes.json"
food_model = None
CLASS_LABELS = []

class FoodClassifierPyTorch(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.backbone = models.efficientnet_b0(pretrained=True)
        in_features = self.backbone.classifier[1].in_features
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )
        self.backbone.classifier = self.classifier

    def forward(self, x):
        return self.backbone(x)

def ensure_model_loaded():
    """Safe model loading with error handling"""
    global food_model, CLASS_LABELS
    
    if food_model is not None:
        return True
        
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at {MODEL_PATH}")
        return False
        
    if not os.path.exists(CLASSES_PATH):
        print(f"Error: Classes file not found at {CLASSES_PATH}")
        return False
        
    try:
        # Load class labels first
        with open(CLASSES_PATH, 'r') as f:
            CLASS_LABELS = json.load(f)
            print(f"Loaded {len(CLASS_LABELS)} classes")
            
        # Create model instance
        model = FoodClassifierPyTorch(len(CLASS_LABELS))
        model.eval()  # Set to evaluation mode
        
        # Load weights
        state_dict = torch.load(MODEL_PATH, map_location='cpu')
        model.load_state_dict(state_dict)
        
        food_model = model
        print("Model loaded successfully")
        return True
        
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return False

@app.route('/api/predict_food', methods=['POST'])
def predict_food():
    if not ensure_model_loaded():
        return jsonify({"error": "Model failed to load"}), 500

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        # Load and preprocess image
        image = Image.open(file.stream).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225])
        ])
        
        input_tensor = transform(image).unsqueeze(0)
        
        # Get prediction
        with torch.no_grad():
            outputs = food_model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted = torch.max(probabilities, 0)
            
        predicted_class = CLASS_LABELS[predicted.item()]
        
        return jsonify({
            "predicted_class": predicted_class,
            "confidence": float(confidence)
        })
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

portion_map = {
    'breakfast': 2,
    'lunch': 3,
    'dinner': 3,
    'snack': 0.3
}

def load_food_model():
    """Lazy load the model only when needed"""
    global food_model
    if food_model is None and os.path.exists(MODEL_PATH):
        try:
            import tensorflow as tf
            food_model = tf.keras.models.load_model(MODEL_PATH)
            print("Food model loaded successfully")
        except Exception as e:
            print(f"Error loading food model: {e}")
            food_model = None
    return food_model

def fetch_usda_meals(category_keywords, user_allergies, wanted_count=3):
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
    payload = {
        "query": ", ".join(category_keywords),
        "pageSize": 30,  # Fetch more for variety
        "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"]
    }
    resp = requests.post(url, json=payload)
    foods = resp.json().get('foods', [])
    safe_foods = []
    # Expanded exclusion list for processed/unfresh foods
    exclusion_terms = [
        "baby", "infant", "toddler", "formula", "gerber",
        "frozen", "ready-to-heat", "ready to heat", "ready meal", "microwave",
        "prepared", "tv dinner", "meal kit", "instant", "dehydrated",
        "canned", "packaged", "convenience", "prepackaged", "pre-packaged"
    ]
    for food in foods:
        description = food.get('description', '').lower()
        # Exclude unwanted foods
        if any(ex in description for ex in exclusion_terms):
            continue
        text = (food.get('description', '') + ' ' + food.get('ingredients', '')).lower()
        if any(a.lower() in text for a in user_allergies):
            continue  # Skip foods with allergies
        fdc_id = food.get('fdcId')
        if not fdc_id:
            continue
        detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={USDA_API_KEY}"
        detail_resp = requests.get(detail_url)
        if detail_resp.status_code == 200:
            food_detail = detail_resp.json()
            food_detail['description'] = food.get('description', '')
            food_detail['ingredients'] = food.get('ingredients', 'Unknown')
            safe_foods.append(food_detail)
    # Randomly select wanted_count meals for variety
    if len(safe_foods) > wanted_count:
        import random
        return random.sample(safe_foods, wanted_count)
    return safe_foods

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID
    fname = db.Column(db.String(100))
    lname = db.Column(db.String(100))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    password = db.Column(db.String(100))
    gender = db.Column(db.String(20))
    dietary_restrictions = db.Column(db.String(100))
    activity_level = db.Column(db.String(50))
    goal = db.Column(db.String(50))
    allergies = db.Column(db.String(200))
    food_preferences = db.Column(db.String(200))
    

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    description = db.Column(db.String(200))
    ingredients = db.Column(db.String(500))



class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'))
    activity_type = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # in minutes
    intensity = db.Column(db.Integer) # 1-5
    calories = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    # new gym-specific fields
    gym_exercise = db.Column(db.String(100), nullable=True)
    lift_weight = db.Column(db.Float, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    time_per_rep = db.Column(db.Float, nullable=True)  # seconds

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def main():
    return render_template('index.html')

# @app.route('/submit', methods=['POST'])
# def submit():
#     return redirect('/dashboard')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form.get('confirmPassword')
        if password != confirm_password:
            return render_template('dashboard.html', error="Passwords do not match.", user=None)
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            fname=request.form['fname'],
            lname=request.form['lname'],
            weight=request.form['weight'],
            height=request.form['height'],
            password=generate_password_hash(password),
            gender=request.form['gender'],
            dietary_restrictions=request.form['dietaryRestrictions'],
            activity_level=request.form['activityLevel'],
            goal=request.form['goal'],
            allergies=request.form.get('allergies', ''),
            food_preferences=request.form.get('foodPreferences', '')
        )
        db.session.add(user)
        db.session.commit()
        return render_template('dashboard.html', user=user)
    else:
        user_id = request.args.get('user_id')
        user = db.session.get(User, user_id) if user_id else None
        return render_template('dashboard.html', user=user)


with open('meals.json', 'r') as f:
    MEALS = json.load(f)

@app.route('/food')
def food():
    user_id = request.args.get('user_id')  # Or get from session
    return render_template('food.html', user_id=user_id)

def compute_gym_calories(user_weight_kg, gym_exercise=None, duration_min=None, lift_weight_kg=0, intensity=2, reps=0, sets=0, time_per_rep=3.0):
    """
    Compute calories for gym strength exercise.
    Accepts either duration_min OR (reps and sets + time_per_rep) to derive duration.
    Formula: calories_per_min = MET * bodyweight(kg) * 0.0175
    Source: Compendium of Physical Activities (MET definition)
    """
    GYM_METS = {
        "squat": 6.0,
        "deadlift": 6.5,
        "bench press": 5.5,
        "overhead press": 6.0,
        "pull-up": 8.0,
        "leg presses": 6.0,
        "bicep curls": 4.0,
        "skullcrushers": 4.5,
        "one arm rows": 5.0,
        "lunges": 5.5
    }
    met = GYM_METS.get((gym_exercise or "").lower(), 5.0)
    # derive duration if not given
    if (not duration_min or float(duration_min) <= 0) and reps and sets:
        duration_min = (reps * sets * float(time_per_rep)) / 60.0
    try:
        duration_min = float(duration_min or 0)
    except Exception:
        duration_min = 0.0
    # scale by load used (small effect) capped to +50%
    load_scale = 1.0 + min(0.5, (lift_weight_kg or 0) / 200.0)
    # intensity: expected 1-5 -> convert to ~0.8-1.3
    intensity_scale = 0.8 + ((int(intensity or 2) - 1) * 0.125)
    body_w = float(user_weight_kg or 70.0)
    calories_per_min = met * body_w * 0.0175
    total = calories_per_min * duration_min * load_scale * intensity_scale
    return int(round(total)), round(duration_min)

@app.route('/api/activity', methods=['POST'])
def save_activity():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id or not db.session.get(User, user_id):
        return jsonify({'error': 'Invalid user'}), 400
    user = db.session.get(User, user_id)
    activity_type = data.get('activityType')
    # Accept either duration (minutes) or reps/sets for gym
    duration = int(data.get('duration', 0)) if data.get('duration') is not None else 0
    intensity = int(data.get('intensity', 1))
    # gym-specific fields
    gym_ex = data.get('gym_exercise')
    lift_w = float(data.get('lift_weight') or 0)
    reps = int(data.get('reps') or 0)
    sets = int(data.get('sets') or 0)
    time_per_rep = float(data.get('time_per_rep') or 3.0)

    if activity_type and activity_type.lower() == 'gym':
        computed_cal, computed_duration = compute_gym_calories(
            user.weight or 70.0,
            gym_exercise=gym_ex,
            duration_min=duration,
            lift_weight_kg=lift_w,
            intensity=intensity,
            reps=reps,
            sets=sets,
            time_per_rep=time_per_rep
        )
        calories_val = computed_cal
        duration_to_store = int(round(computed_duration))
    else:
        calories_val = int(data.get('calories', 0))
        duration_to_store = duration

    try:
        activity = Activity(
            user_id=user_id,
            activity_type=activity_type,
            duration=duration_to_store,
            intensity=intensity,
            calories=calories_val,
            timestamp=datetime.fromisoformat(data.get('dateTime')),
            gym_exercise=gym_ex,
            lift_weight=lift_w,
            reps=reps,
            sets=sets,
            time_per_rep=time_per_rep
        )
        db.session.add(activity)
        db.session.commit()
        return jsonify({'success': True, 'activity_id': activity.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activity', methods=['GET'])
def get_activity():
    ## checking if user is valid 
    user_id = request.args.get('user_id')
    if not user_id or not db.session.get(User, user_id):
        return jsonify({'error': 'Invalid user'}), 400
    query = Activity.query.filter_by(user_id=user_id)
    ### identifying variables for filtering 
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    activity_type = request.args.get('type')
    if from_date:
        query = query.filter(Activity.timestamp >= from_date)
    if to_date:
        query = query.filter(Activity.timestamp <= to_date + " 23:59:59")
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    activities = query.order_by(Activity.timestamp.desc()).all()
    return jsonify([
        {
            'id': a.id,
            'activityType': a.activity_type,
            'duration': a.duration,
            'intensity': a.intensity,
            'calories': a.calories,
            'dateTime': a.timestamp.isoformat(),
            'gymExercise': a.gym_exercise,
            'liftWeight': a.lift_weight,
            'reps': a.reps,
            'sets': a.sets,
            'timePerRep': a.time_per_rep
        } for a in activities
    ])

def extract_nutrition(food, portion_multiplier=1):
    macros = {'protein': None, 'fat': None, 'carbs': None, 'calories': None}
    for nut in food.get("foodNutrients", []):
        num = str(nut.get('nutrientNumber') or nut.get('nutrient', {}).get('number') or '')
        amt = nut.get('value', nut.get('amount', 0))
        if num == '203':  # Protein
            macros['protein'] = amt
        elif num == '204':  # Fat
            macros['fat'] = amt
        elif num == '205':  # Carbohydrates
            macros['carbs'] = amt
        elif num == '208':  # Energy (kcal)
            macros['calories'] = amt
    for k in macros:
        if macros[k] is None:
            macros[k] = 0
        macros[k] = round(macros[k] * portion_multiplier)
    return macros

@app.route('/record_calories', methods=['POST'])
def add_calories():
    data = request.json
    user_id = data.get('user_id')
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    try:
        # Handle missing or invalid date
        date_str = data.get('date', datetime.utcnow().strftime("%Y-%m-%d"))
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # <-- use .date()
        except Exception:
            date_obj = datetime.utcnow().date()  # <-- use .date()
        # Handle ingredients as string or list
        ingredients = data.get('ingredients', '')
        if isinstance(ingredients, list):
            ingredients = ', '.join(ingredients)
        entry = Meal(
            user_id=user_id,
            date=date_obj,
            calories=data.get('calories', 0),
            protein=data.get('protein', 0),
            carbs=data.get('carbs', 0),
            fat=data.get('fat', 0),
            description=data.get('description', ''),
            ingredients=ingredients
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({"message": "Entry added."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/recommend')
def recommend():
    user_id = request.args.get('user_id')
    user = db.session.get(User, user_id)
    if not user: 
        return jsonify({"error": "User not found"}), 404

    allergies = [a.strip().lower() for a in user.allergies.split(',') if a.strip()] if user.allergies else []
    food_preferences = [fp.strip().lower() for fp in user.food_preferences.split(',') if fp.strip()] if user.food_preferences else []

    # Macronutrient targets
    daily_macros = {
        "calories": 1800,
        "protein": 75,
        "carbs": 350,
        "fat": 50
    }
    # Proportions
    proportions = {
        "breakfast": 0.25,
        "lunch": 0.3,
        "dinner": 0.35,
        "snacks": random.uniform(0.05, 0.1)
    }

    meal_keywords = {
        'breakfast': ['eggs', 'oatmeal', 'yogurt', 'fruit', 'cereal', 'toast'],
        'lunch': ['salad', 'sandwich', 'chicken', 'rice', 'soup', 'beef'],
        'dinner': ['fish', 'steak', 'pasta', 'vegetables', 'curry'],
        'snacks': ['nuts', 'bar', 'cheese', 'fruit', 'yogurt']
    }

    recommendations = {}
    def get_main_word(description):
        # Extract the first significant word (not generic modifiers)
        words = re.findall(r'\b[a-zA-Z]+\b', description.lower())
        for w in words:
            if w not in {"food", "product", "prepared", "style", "type", "brand", "plain", "lowfat", "nonfat", "fatfree", "skim", "whole", "reduced", "original", "natural", "greek"}:
                return w
        return words[0] if words else ""

    for category, keywords in meal_keywords.items():
        # Shuffle keywords for variety
        random.shuffle(keywords)
        meals = fetch_usda_meals(keywords, allergies, wanted_count=20)  # Fetch more for better filtering
        # Shuffle meals for variety
        random.shuffle(meals)
        recs = []
        macro_target = {k: round(v * proportions[category]) for k, v in daily_macros.items()}
        portion_multiplier = portion_map.get(category, 1)
        used_main_words = set()
        for food in meals:
            ingredients = food.get("ingredients", "Unknown")
            description = food.get("description", "").lower()
            if any(a in (ingredients.lower() + description) for a in allergies):
                continue
            nutrition = extract_nutrition(food, portion_multiplier)
            within_macros = all(
                abs(nutrition[k] - macro_target[k]) <= macro_target[k] * 0.3
                for k in macro_target
            )
            if not within_macros:
                continue
            main_word = get_main_word(description)
            if main_word in used_main_words:
                continue  # Skip if we've already used this main type
            used_main_words.add(main_word)
            recs.append({
                "id": food.get("fdcId"),
                "description": food.get("description"),
                "ingredients": ingredients,
                "nutrition": nutrition,
                "macro_target": macro_target
            })
            if len(recs) == 3:
                break
        # Fill up to 3 if needed (with closest macros, but still unique main words)
        if len(recs) < 3:
            leftovers = []
            for food in meals:
                if any(r['id'] == food.get("fdcId") for r in recs):
                    continue
                ingredients = food.get("ingredients", "Unknown")
                description = food.get("description", "").lower()
                if any(a in (ingredients.lower() + description) for a in allergies):
                    continue
                nutrition = extract_nutrition(food, portion_multiplier)
                main_word = get_main_word(description)
                if main_word in used_main_words:
                    continue  # <-- This line ensures no duplicates
                diff = sum(abs(nutrition[k] - macro_target[k]) for k in macro_target)
                leftovers.append((diff, {
                    "id": food.get("fdcId"),
                    "description": food.get("description"),
                    "ingredients": ingredients,
                    "nutrition": nutrition,
                    "macro_target": macro_target
                }))
            leftovers.sort(key=lambda x: x[0])
            for _, meal in leftovers:
                recs.append(meal)
                used_main_words.add(get_main_word(meal["description"]))
                if len(recs) == 3:
                    break

        recommendations[category] = recs
    return jsonify(recommendations)
@app.route('/activitylog')
def exercise(): 
    user_id = request.args.get('user_id')
    return render_template('exercise.html', user_id=user_id)

@app.route('/exerciserecommendation')
def exercise_recommendation():
    user_id = request.args.get('user_id')
    user = db.session.get(User, user_id)
    return render_template('exerciserecommendation.html', user_goal = user.goal, user_level = user.activity_level)

def search_ingredients_google(meal_name):
    search_query = f"{meal_name} ingredients"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": search_query,
        "num": 1
    }
    resp = requests.get(url, params=params)
    print("Google API response:", resp.text)
    if resp.status_code == 200:
        items = resp.json().get("items", [])
        if items:
            snippet = items[0].get("snippet", "")
            if "Ingredients:" in snippet:
                ing_text = snippet.split("Ingredients:")[1]
                for stop_word in [".", "Directions", "Method"]:
                    if stop_word in ing_text:
                        ing_text = ing_text.split(stop_word)[0]
                return ing_text.strip()
            else:
                # Try to extract ingredients by splitting on commas
                parts = [p.strip() for p in snippet.split(",") if len(p.strip().split()) < 5]
                if len(parts) > 2:
                    return ", ".join(parts)
                return snippet.strip()
    return "Ingredients not found"

def search_ingredients_spoonacular(meal_name):
    SPOONACULAR_API_KEY = "9c2f3b3991c64a47bcd00d3ae163cd84"
    # Step 1: Search for the recipe
    search_url = "https://api.spoonacular.com/recipes/complexSearch"
    search_params = {
        "query": meal_name,
        "number": 1,
        "apiKey": SPOONACULAR_API_KEY
    }
    search_resp = requests.get(search_url, params=search_params)
    if search_resp.status_code == 200:
        results = search_resp.json().get("results", [])
        if results:
            recipe_id = results[0]["id"]
            # Step 2: Get recipe information
            info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
            info_params = {"apiKey": SPOONACULAR_API_KEY}
            info_resp = requests.get(info_url, params=info_params)
            if info_resp.status_code == 200:
                data = info_resp.json()
                # Get full ingredient list
                ingredients = [ing["original"] for ing in data.get("extendedIngredients", [])]
                # Remove trailing ellipsis if present
                ingredients = [i.rstrip('...').strip() for i in ingredients]
                return ", ".join(ingredients) if ingredients else "Ingredients not found"
    return "Ingredients not found"

def get_exercises_from_api(params, headers):
    base_url = "https://exercisedb-api1.p.rapidapi.com/api/v1/exercises"
    # Build query string from params
    query_params = []
    for k, v in params.items():
        if v:
            query_params.append(f"{k}={v}")
    url = base_url + "?" + "&".join(query_params)
    print("Requesting:", url)
    resp = requests.get(url, headers=headers)
    print("Exercise API response:", resp.text)
    if resp.status_code == 200:
        data_json = resp.json()
        # The structure may be a list or dict; adjust as needed
        if isinstance(data_json, dict):
            exercises = data_json.get("data", [])
        else:
            exercises = data_json
        return exercises
    return []

@app.route('/api/exercise_recommendation', methods=['POST'])
def api_exercise_recommendation():
    data = request.json
    user_id = data.get('user_id')
    user = db.session.get(User, user_id) if user_id else None

    # Prefer the explicit level sent by client; otherwise fall back to stored value from DB
    level = (data.get('level') or (user.activity_level if user else None) or "").strip().lower()
    goal = data.get('goal')
    gender = data.get('gender')
    selected_muscles = data.get('muscles', []) or []
    age = data.get('age', 25)
    weight = data.get('weight', 70)
    lower_intensity = bool(data.get('lower_intensity', False))

    # Map textual activity_level to a maximum acceptable exercise intensity (1-5)
    activity_level_to_max_intensity = {
        "sedentary": 2,
        "lightly active": 3, "lightly_active": 3, "lightlyactive": 3,
        "moderately active": 4, "moderately_active": 4, "moderatelyactive": 4,
        "very active": 5, "very_active": 5, "veryactive": 5,
        "super active": 5, "super_active": 5, "superactive": 5
    }
    # Default max intensity if unknown
    max_intensity = activity_level_to_max_intensity.get(level, 4)
    if lower_intensity:
        max_intensity = max(1, max_intensity - 1)

    # Set exerciseType and bodyParts based on goal
    if goal == "muscle_gain":
        exercise_type = "strength"
        body_parts = ",".join(selected_muscles)
    elif goal in ["weight_loss", "endurance"]:
        exercise_type = "cardio"
        body_parts = ""
    elif goal == "flexibility":
        exercise_type = "stretching"
        body_parts = ",".join(selected_muscles) if selected_muscles else ""
    else:
        exercise_type = ""
        body_parts = ""

    params = {
        "limit": 50,
        "goal": goal,
        "activityLevel": level,
        "gender": gender,
        "age": age,
        "weight": weight,
        "bodyParts": body_parts,
        "exerciseType": exercise_type,
    }
    headers = {
        "X-RapidAPI-Key": "59a253f828msh019e8f4b915bb68p16511fjsn8bb17ce03e4e",
        "X-RapidAPI-Host": "exercisedb-api1.p.rapidapi.com"
    }
    exercises = get_exercises_from_api(params, headers)

    # Heuristics / filtering based on goal (existing logic preserved)
    if goal in ["weight_loss", "endurance"]:
        cardio_exs = [ex for ex in exercises if "cardio" in (str(ex.get("exerciseType", "")) + str(ex.get("type", "")) + str(ex.get("category", ""))).lower()]
        if not cardio_exs:
            cardio_keywords = ["run", "walk", "cycle", "jump", "cardio", "aerobic", "row", "swim", "burpee"]
            cardio_exs = [ex for ex in exercises if any(kw in ex.get("name", "").lower() for kw in cardio_keywords)]
        if not cardio_exs and exercises:
            cardio_exs = exercises[:5]
        exercises = cardio_exs

    if goal == "flexibility":
        stretch_exs = [ex for ex in exercises if "stretch" in (str(ex.get("exerciseType", "")) + str(ex.get("type", "")) + str(ex.get("category", ""))).lower()]
        if selected_muscles:
            stretch_exs = [ex for ex in stretch_exs if any(muscle.lower() in " ".join(ex.get("bodyParts", [])).lower() for muscle in selected_muscles)]
        if not stretch_exs and exercises:
            stretch_exs = exercises[:5]
        exercises = stretch_exs

    # Apply intensity filtering by using exercise['intensity'] when available, otherwise try heuristics
    def exercise_intensity_value(ex):
        try:
            return int(float(ex.get('intensity', ex.get('difficulty', ex.get('level', max_intensity)))))
        except Exception:
            # Fallback heuristic: strength/cardio/stretching keywords
            name = (ex.get('name') or "").lower()
            if any(k in name for k in ['sprint', 'hiit', 'burpee', 'tabata', 'interval']):
                return 5
            if any(k in name for k in ['run', 'cycle', 'rowing', 'jump', 'cardio']):
                return 4
            if any(k in name for k in ['walk', 'stretch', 'yoga', 'mobility']):
                return 2
            return 3

    filtered_exercises = []
    for ex in exercises:
        intensity_val = exercise_intensity_value(ex)
        if intensity_val <= max_intensity:
            filtered_exercises.append(ex)

    # If filtering removed too many items, relax filter slightly (keep at least 3 suggestions)
    if len(filtered_exercises) < 3 and exercises:
        # sort by closeness to max_intensity and take top 5
        exercises_with_score = sorted(exercises, key=lambda ex: abs(exercise_intensity_value(ex) - max_intensity))
        filtered_exercises = exercises_with_score[:5]

    recommendations = filtered_exercises[:5] if filtered_exercises else []
    return jsonify({"recommendations": recommendations})

def get_user_stats(user_id):
    # Aggregate diet logs
    user = db.session.get(User, user_id)
    meals = Meal.query.filter_by(user_id=user_id).order_by(Meal.date.desc()).all()
    activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.timestamp.desc()).all()
    user = db.session.get(User, user_id)
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=6)
    # Diet stats
    daily_meals = [m for m in meals if m.date == today]
    weekly_meals = [m for m in meals if m.date >= week_ago]
    total_calories = sum(m.calories for m in daily_meals)
    total_protein = sum(m.protein for m in daily_meals)
    total_carbs = sum(m.carbs for m in daily_meals)
    total_fat = sum(m.fat for m in daily_meals)
    # Exercise stats
    daily_activities = [a for a in activities if a.timestamp.date() == today]
    weekly_activities = [a for a in activities if a.timestamp.date() >= week_ago]
    total_ex_minutes = sum(a.duration for a in daily_activities)
    total_ex_calories = sum(a.calories for a in daily_activities)
    # Trends
    calories_7d = []
    ex_minutes_7d = []
    ex_calories_7d = []
    for i in range(7):
        d = today - timedelta(days=i)
        calories_7d.append(sum(m.calories for m in meals if m.date == d))
        ex_minutes_7d.append(sum(a.duration for a in activities if a.timestamp.date() == d))
        ex_calories_7d.append(sum(a.calories for a in activities if a.timestamp.date() == d))
    # Intensity distribution
    intensity_counts = {'Low': 0, 'Moderate': 0, 'High': 0}
    for a in weekly_activities:
        if a.intensity <= 2:
            intensity_counts['Low'] += 1
        elif a.intensity == 3:
            intensity_counts['Moderate'] += 1
        else:
            intensity_counts['High'] += 1
    # Recommended calories (simple example)
    recommended_calories = 1800 if user.goal == "weight_loss" else 2200
    return {
        "today": str(today),
        "total_calories": total_calories,
        "recommended_calories": recommended_calories,
        "macros": {
            "protein": total_protein,
            "carbs": total_carbs,
            "fat": total_fat,
            "target": {"protein": 75, "carbs": 350, "fat": 50}
        },
        "exercise": {
            "minutes": total_ex_minutes,
            "calories": total_ex_calories
        },
        "calories_7d": calories_7d[::-1],
        "ex_minutes_7d": ex_minutes_7d[::-1],
        "ex_calories_7d": ex_calories_7d[::-1],
        "intensity_dist": intensity_counts
    }

def get_cached_stats(user_id):
    return get_user_stats(user_id)

@app.route('/api/dashboard_stats')
def dashboard_stats():
    user_id = request.args.get('user_id')
    stats = get_user_stats(user_id)
    return jsonify(stats)

@app.route('/api/daily_summary')
def daily_summary():
    user_id = request.args.get('user_id')
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    today = date.today()
    # Aggregate meals
    meals = Meal.query.filter_by(user_id=user_id, date=today).all()
    total_macros = {
        "calories": sum(m.calories for m in meals),
        "protein": sum(m.protein for m in meals),
        "carbs": sum(m.carbs for m in meals),
        "fat": sum(m.fat for m in meals)
    }
    # Aggregate activities
    activities = Activity.query.filter(
        Activity.user_id == user_id,
        Activity.timestamp >= datetime.combine(today, datetime.min.time()),
        Activity.timestamp <= datetime.combine(today, datetime.max.time())
    ).all()
    total_exercise = {
        "minutes": sum(a.duration for a in activities),
        "calories_burned": sum(a.calories for a in activities),
        "activities": [
            {
                "type": a.activity_type,
                "duration": a.duration,
                "intensity": a.intensity,
                "calories": a.calories,
                "timestamp": a.timestamp.isoformat()
            } for a in activities
        ]
    }
    return jsonify({
        "date": str(today),
        "macronutrients": total_macros,
        "exercise": total_exercise
    })
@app.route('/api/meal_history', methods=['GET'])
def get_meal_history():
    user_id = request.args.get('user_id')
    if not user_id or not db.session.get(User, user_id):
        return jsonify({'error': 'Invalid user'}), 400
    query = Meal.query.filter_by(user_id=user_id)
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    if from_date:
        query = query.filter(Meal.date >= from_date)
    if to_date:
        query = query.filter(Meal.date <= to_date)
    meals = query.order_by(Meal.date.desc()).all()
    return jsonify([
        {
            'id': m.id,
            'date': m.date.isoformat(),
            'description': m.description,
            'ingredients': m.ingredients,
            'calories': m.calories,
            'protein': m.protein,
            'carbs': m.carbs,
            'fat': m.fat
        } for m in meals
    ])

def get_spoonacular_estimate(meal_name):
    """Return ingredients, per_serving and per_100g nutrition (calories, protein, carbs, fat) if available."""
    SPOONACULAR_API_KEY = "9c2f3b3991c64a47bcd00d3ae163cd84"
    try:
        search_url = "https://api.spoonacular.com/recipes/complexSearch"
        sresp = requests.get(search_url, params={"query": meal_name, "number": 1, "apiKey": SPOONACULAR_API_KEY}, timeout=8)
        if sresp.status_code != 200:
            return {"error": "search_failed", "status": sresp.status_code}
        results = sresp.json().get("results", [])
        if not results:
            # Try Google Custom Search as a fallback
            google_ingredients = search_ingredients_google(meal_name)
            if google_ingredients and google_ingredients != "Ingredients not found":
                return {
                    "ingredients": google_ingredients,
                    "per_100g": None,
                    "per_serving": None
                }
            return {"error": "no_recipe_found", "ingredients": "Ingredients not found"}

        recipe_id = results[0]["id"]
        info_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        iresp = requests.get(info_url, params={"includeNutrition": "true", "apiKey": SPOONACULAR_API_KEY}, timeout=8)
        if iresp.status_code != 200:
            return {"error": "info_failed", "status": iresp.status_code}
        info = iresp.json()

        ingredients = ", ".join([ing.get("original", "").strip() for ing in info.get("extendedIngredients", [])]) or "Ingredients not found"

        nut_map = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        for n in info.get("nutrition", {}).get("nutrients", []):
            name = (n.get("name") or "").lower()
            amt = float(n.get("amount", 0) or 0)
            if "calorie" in name:
                nut_map["calories"] = amt
            elif "protein" in name:
                nut_map["protein"] = amt
            elif "fat" in name:
                nut_map["fat"] = amt
            elif "carb" in name:
                nut_map["carbs"] = amt

        servings = info.get("servings") or 1
        weight_per_serv = info.get("weightPerServing")
        weight_g = None
        if isinstance(weight_per_serv, dict):
            weight_g = weight_per_serv.get("amount")  # spoonacular uses amount in grams often
        # per_serving = nut_map already indicates amounts per serving
        per_serving = {k: round(v, 2) for k, v in nut_map.items()}

        per_100g = None
        if weight_g and weight_g > 0:
            factor = 100.0 / float(weight_g)
            per_100g = {k: round(v * factor, 2) for k, v in per_serving.items()}
        else:
            # fallback: assume per_serving corresponds to 100g if nothing else available (best-effort)
            per_100g = {k: round(v, 2) for k, v in per_serving.items()}

        return {
            "ingredients": ingredients,
            "servings": servings,
            "weight_per_serv_g": weight_g,
            "per_serving": per_serving,
            "per_100g": per_100g
        }
    except Exception as e:
        return {"error": "exception", "message": str(e)}


@app.route('/api/predict_and_estimate', methods=['POST'])
def predict_and_estimate():
    """Predict class from image, query Spoonacular, estimate per-portion macros using portion_map."""
    if not ensure_model_loaded():
        return jsonify({"error": "Model failed to load"}), 500

    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    meal_type = request.form.get('meal_type', 'lunch')  # breakfast/lunch/dinner/snack

    try:
        image = Image.open(file.stream).convert('RGB')
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
        tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            outputs = food_model(tensor)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted = torch.max(probs, 0)

        predicted_class = CLASS_LABELS[predicted.item()] if CLASS_LABELS else str(predicted.item())

        sp = get_spoonacular_estimate(predicted_class)
        if sp.get("error"):
            return jsonify({
                "predicted_class": predicted_class,
                "confidence": float(confidence),
                "ingredients": sp.get("message", sp.get("error")),
                "per_100g": None,
                "estimated_portion": None,
                "portion_multiplier": portion_map.get(meal_type, 1)
            })

        per100 = sp.get("per_100g") or {}
        portion_multiplier = portion_map.get(meal_type, 1)
        estimated = {
            "calories": round(float(per100.get("calories", 0)) * portion_multiplier, 1),
            "protein": round(float(per100.get("protein", 0)) * portion_multiplier, 1),
            "carbs": round(float(per100.get("carbs", 0)) * portion_multiplier, 1),
            "fat": round(float(per100.get("fat", 0)) * portion_multiplier, 1)
        }

        return jsonify({
            "predicted_class": predicted_class,
            "confidence": float(confidence),
            "ingredients": sp.get("ingredients"),
            "per_100g": per100,
            "estimated_portion": estimated,
            "portion_multiplier": portion_multiplier,
            "note": "You can POST this estimated_portion to /record_calories with user_id to save."
        })

    except Exception as e:
        print(f"predict_and_estimate error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__== '__main__':
    app.run(debug=True)