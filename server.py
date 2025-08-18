from flask import Flask, render_template, jsonify 
from flask_sqlalchemy import SQLAlchemy 
import uuid
from flask import request
import os
import json
from werkzeug.security import generate_password_hash
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
USDA_API_KEY = "BQazS4IWGw7VKfBNHFbEJfLPab1wz1ROSZf1xS6K"
db = SQLAlchemy(app)

def fetch_usda_meals(category_keywords, user_allergies, wanted_count=5):
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

def extract_nutrition(food):
    macros = {'protein': None, 'fat': None, 'calories': None}
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
        meals = fetch_usda_meals(keywords, allergies, wanted_count=5)
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
    return render_template('exercise.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

# To run this server, use the command:
# python -m flask --app server run