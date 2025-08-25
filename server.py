from flask import Flask, render_template, jsonify 
from flask_sqlalchemy import SQLAlchemy 
import uuid
from flask import request
from PIL import Image
import numpy as np
import os
import json
from werkzeug.security import generate_password_hash
import requests
from datetime import datetime 
import pandas as pd
import matplotlib.pyplot as plt
import http.client

conn = http.client.HTTPSConnection("exercisedb-api1.p.rapidapi.com")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
USDA_API_KEY = "BQazS4IWGw7VKfBNHFbEJfLPab1wz1ROSZf1xS6K"
GOOGLE_API_KEY = "AIzaSyCOGmhXar6SGEizGd2vpxznQ7ESSoIPZNA"
GOOGLE_CSE_ID = "80aa6e2c5b0e44514"
db = SQLAlchemy(app)

def fetch_usda_meals(category_keywords, user_allergies, wanted_count=3):
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
    payload = {
        "query": ", ".join(category_keywords),
        "pageSize": 60,
        "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"]
    }
    resp = requests.post(url, json=payload)
    foods = resp.json().get('foods', [])
    safe_foods = []
    for food in foods:
        text = (food.get('description', '') + ' ' + food.get('ingredients', '')).lower()
        if not any(a.lower() in text for a in user_allergies):
            # Fetch full nutrient info for this food
            fdc_id = food.get('fdcId')
            if not fdc_id:
                continue
            detail_url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={USDA_API_KEY}"
            detail_resp = requests.get(detail_url)
            if detail_resp.status_code == 200:
                food_detail = detail_resp.json()
                # Merge description and ingredients from search result for consistency
                food_detail['description'] = food.get('description', '')
                food_detail['ingredients'] = food.get('ingredients', 'Unknown')
                safe_foods.append(food_detail)
            if len(safe_foods) == wanted_count:
                break
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

@app.route('/')
def main():
    return render_template('index.html')

# @app.route('/submit', methods=['POST'])
# def submit():
#     return redirect('/dashboard')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            fname=request.form['fname'],
            lname=request.form['lname'],
            weight=request.form['weight'],
            height=request.form['height'],
            password=generate_password_hash(request.form['password']),
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
        # For GET requests, you need to get the user_id from query params or session
        user_id = request.args.get('user_id')
        user = db.session.get(User, user_id) if user_id else None
        return render_template('dashboard.html', user=user)


with open('meals.json', 'r') as f:
    MEALS = json.load(f)

@app.route('/food')
def food():
    user_id = request.args.get('user_id')  # Or get from session
    return render_template('food.html', user_id=user_id)

@app.route('/api/activity', methods=['POST'])
def save_activity():
    data = request.get_json()
    user_id = data.get('user_id')
    if not user_id or not db.session.get(User, user_id):
        return jsonify({'error': 'Invalid user'}), 400
    activity = Activity(
        user_id=user_id,
        activity_type=data.get('activityType'),
        duration=int(data.get('duration', 0)),
        intensity=int(data.get('intensity', 1)),
        calories=int(data.get('calories', 0)),
        timestamp=datetime.fromisoformat(data.get('dateTime'))
    )
    db.session.add(activity)
    db.session.commit()
    return jsonify({'success': True, 'activity_id': activity.id})

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
            'dateTime': a.timestamp.isoformat()
        } for a in activities
    ])

def extract_nutrition(food):
    macros = {'protein': None, 'fat': None, 'carbs': None, 'calories': None}
    for nut in food.get("foodNutrients", []):
        num = str(nut.get('nutrientNumber') or nut.get('nutrient', {}).get('number') or '')
        # Use 'value' if present, else fallback to 'amount'
        amt = nut.get('value', nut.get('amount', 0))
        if num == '203':  # Protein
            macros['protein'] = amt
        elif num == '204':  # Fat
            macros['fat'] = amt
        elif num == '205':  # Carbohydrates
            macros['carbs'] = amt
        elif num == '208':  # Energy (kcal)
            macros['calories'] = amt
    # Fallback to 0 if missing
    for k in macros:
        if macros[k] is None:
            macros[k] = 0
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
    allergies = user.allergies.split(',') if user.allergies else []
    food_preferences = user.food_preferences.split(',') if user.food_preferences else []
    meal_keywords = {
        'breakfast': ['eggs', 'oatmeal', 'yogurt', 'fruit', 'cereal', 'toast'],
        'lunch': ['salad', 'sandwich', 'chicken', 'rice', 'soup', 'beef'],
        'dinner': ['fish', 'steak', 'pasta', 'vegetables', 'curry'],
        'snacks': ['nuts', 'bar', 'cheese', 'fruit', 'yogurt']
    }
    recommendations = {}
    for category, keywords in meal_keywords.items():
        meals = fetch_usda_meals(keywords, allergies, wanted_count=3)
        recs = []
        for food in meals:
            ingredients = food.get("ingredients", "Unknown")
            if ingredients == "Unknown":
                # Use Google search to get ingredients
                ingredients = search_ingredients_spoonacular(food["description"])
            # Allergy check (simple, case-insensitive substring match)
            if any(a.lower() in ingredients.lower() for a in allergies):
                continue  # Skip meal if allergy found
            recs.append({
                "id": food["fdcId"],
                "description": food["description"],
                "ingredients": ingredients,
                "nutrition": extract_nutrition(food)
            })
        recommendations[category] = recs
    return jsonify(recommendations)


@app.route('/meal/<int:meal_id>')
def meal_details(meal_id):
    for meals in MEALS.values():
        for meal in meals:
            if meal['id'] == meal_id:
                return jsonify(meal)
    return jsonify({"error": "Meal not found"}), 404


@app.route('/activitylog')
def exercise(): 
    user_id = request.args.get('user_id')
    return render_template('exercise.html')

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

@app.route('/api/exercise_recommendation', methods=['POST'])
def api_exercise_recommendation():
    data = request.json
    user_id = data.get('user_id')
    goal = data.get('goal')
    level = data.get('level')
    gender = data.get('gender')
    selected_muscles = data.get('muscles', [])  # Only for muscle gain
    age = data.get('age', 25)  # Optional: add age if available
    weight = data.get('weight', 70)  # Optional: add weight if available

    # Example: get user's exercise history for cooldown logic
    user_history = {}  # Replace with DB lookup

    # Build API query parameters
    params = {
        "limit": 20,
        "goal": goal,
        "activityLevel": level,
        "gender": gender,
        "age": age,
        "weight": weight,
        "bodyParts": ",".join(selected_muscles) if goal == "muscle_gain" else "",
        "exerciseType": "strength" if goal == "muscle_gain" else "cardio",
        "equipment": "",  # Optionally filter by equipment
        "intensity": "",  # Optionally filter by intensity
        # Add more params as needed for your API
    }
    headers = {
        "X-RapidAPI-Key": "59a253f828msh019e8f4b915bb68p16511fjsn8bb17ce03e4e",
        "X-RapidAPI-Host": "exercisedb-api1.p.rapidapi.com"
    }
    # Call the exercise API (replace with your actual endpoint) Source code: https://rapidapi.com/ascendapi/api/exercisedb-api1/playground/apiendpoint_0b84e1f7-179a-4848-9be4-680e344feb9a
    conn.request("GET", "/api/v1/exercises?name=Bench%20Press&keywords=chest%20workout%2Cbarbell&limit=10", headers=headers)
    res = conn.getresponse()
    data_bytes = res.read()
    data_str = data_bytes.decode("utf-8")
    data_json= json.loads(data_str)
    exercises = data_json.get("data", [])

    # Filter out exercises done in the last 7 days
    import time
    now = time.time()
    cooldown = 7 * 24 * 3600  # 1 week in seconds
    filtered = [
        ex for ex in exercises
        if ex["exerciseId"] not in user_history or now - user_history[ex["exerciseId"]] > cooldown
    ]

    # Pick top 3 (or however many you want)
    recommendations = filtered[:3]

    return jsonify({"recommendations": recommendations})
# To run this server, use the command:
# python -m flask --app server run

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# To run this server, use the command:
# python -m flask --app server run