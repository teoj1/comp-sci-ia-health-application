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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
USDA_API_KEY = "BQazS4IWGw7VKfBNHFbEJfLPab1wz1ROSZf1xS6K"
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
    User.id()
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, default=datetime.utcnow)
    calories = db.Column(db.Integer)



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

@app.route('/dashboard', methods=['POST'])
def dashboard():

    user_id=str(uuid.uuid4()) ## generating userID 
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
    data = request.json
    db.session.add(user)
    db.session.commit()
    print(user.__dict__)
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
    entry = Meal(user_id=user.id, date=datetime.strptime(data['date'], "%Y-%m-%d"), calories=data['calories'])
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": "Entry added."})


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
        recommendations[category]= [
            {
                "id": food["fdcId"],
                "description": food["description"],
                "ingredients": food.get("ingredients", "Unknown"),
                "nutrition": extract_nutrition(food)
            } for food in meals
        ]
    return jsonify(recommendations)


@app.route('/meal/<int:meal_id>')
def meal_details(meal_id):
    for meals in MEALS.values():
        for meal in meals:
            if meal['id'] == meal_id:
                return jsonify(meal)
    return jsonify({"error": "Meal not found"}), 404


@app.route('/exercise')
def exercise(): 
    user_id = request.args.get('user_id')
    return render_template('exercise.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# To run this server, use the command:
# python -m flask --app server run