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
from datetime import datetime, date 
import pandas as pd
import matplotlib.pyplot as plt
import http.client
import random
from functools import lru_cache
from datetime import timedelta

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
        "pageSize": 20,  # Lowered for speed
        "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"]
    }
    resp = requests.post(url, json=payload)
    foods = resp.json().get('foods', [])
    safe_foods = []
    for food in foods:
        text = (food.get('description', '') + ' ' + food.get('ingredients', '')).lower()
        if any(a.lower() in text for a in user_allergies):
            continue  # Skip foods with allergies
        # Only fetch details if it passes allergy check
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

    # Add food preferences to keywords if present
    for category in meal_keywords:
        if food_preferences:
            meal_keywords[category] += food_preferences

    recommendations = {}
    for category, keywords in meal_keywords.items():
        # Shuffle keywords for variety
        random.shuffle(keywords)
        meals = fetch_usda_meals(keywords, allergies, wanted_count=6)
        # Shuffle meals for variety
        random.shuffle(meals)
        recs = []
        macro_target = {k: round(v * proportions[category]) for k, v in daily_macros.items()}
        for food in meals:
            # Allergy and preference check
            ingredients = food.get("ingredients", "Unknown")
            description = food.get("description", "").lower()
            if any(a in (ingredients.lower() + description) for a in allergies):
                continue
            if food_preferences and not any(fp in description or fp in ingredients.lower() for fp in food_preferences):
                continue  # Skip meals the user dislikes
            # Nutrition
            nutrition = extract_nutrition(food)
            # Only include meals within ±30% of macro target for the category
            within_macros = all(
                abs(nutrition[k] - macro_target[k]) <= macro_target[k] * 0.3
                for k in macro_target
            )
            if not within_macros:
                continue
            recs.append({
                "id": food.get("fdcId"),
                "description": food.get("description"),
                "ingredients": ingredients,
                "nutrition": nutrition,
                "macro_target": macro_target
            })
            if len(recs) == 3:  # 3 meals per category
                break
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
    goal = data.get('goal')
    level = data.get('level')
    gender = data.get('gender')
    selected_muscles = data.get('muscles', [])
    age = data.get('age', 25)
    weight = data.get('weight', 70)
    lower_intensity = data.get('lower_intensity', False)

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

    # --- FIX: Always output cardio/stretching regardless of API structure ---
    if goal in ["weight_loss", "endurance"]:
        # Accept any exercise with 'cardio' in type, or fallback to name keywords
        cardio_exs = [ex for ex in exercises if "cardio" in (str(ex.get("exerciseType", "")) + str(ex.get("type", "")) + str(ex.get("category", ""))).lower()]
        if not cardio_exs:
            cardio_keywords = ["run", "walk", "cycle", "jump", "cardio", "aerobic", "row", "swim", "burpee"]
            cardio_exs = [ex for ex in exercises if any(kw in ex.get("name", "").lower() for kw in cardio_keywords)]
        # If still empty, fallback to first 5 exercises
        if not cardio_exs and exercises:
            cardio_exs = exercises[:5]
        exercises = cardio_exs

    if goal == "flexibility":
        # Accept any exercise with 'stretch' or 'stretching' in type/category
        stretch_exs = [ex for ex in exercises if "stretch" in (str(ex.get("exerciseType", "")) + str(ex.get("type", "")) + str(ex.get("category", ""))).lower()]
        # If muscle groups selected, filter by bodyParts
        if selected_muscles:
            stretch_exs = [ex for ex in stretch_exs if any(muscle.lower() in " ".join(ex.get("bodyParts", [])).lower() for muscle in selected_muscles)]
        # If still empty, fallback to first 5 exercises
        if not stretch_exs and exercises:
            stretch_exs = exercises[:5]
        exercises = stretch_exs

    # Lower intensity filter
    if lower_intensity:
        exercises = [ex for ex in exercises if ex.get("intensity", 1) <= 2]

    recommendations = exercises[:5] if exercises else []
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

@lru_cache(maxsize=32)
def get_cached_stats(user_id):
    return get_user_stats(user_id)

@app.route('/api/dashboard_stats')
def dashboard_stats():
    user_id = request.args.get('user_id')
    stats = get_cached_stats(user_id)
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
# To run this server, use the command:
# python -m flask --app server run

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# To run this server, use the command:
# python -m flask --app server run