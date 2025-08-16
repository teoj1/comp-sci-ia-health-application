from flask import Flask, render_template, jsonify 
from flask_sqlalchemy import SQLAlchemy 
import uuid
from flask import request
import os
import json
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)


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
    return render_template('dashboard.html', user=user)

with open('meals.json', 'r') as f:
    MEALS = json.load(f)

@app.route('/food')
def food():
    return render_template('food.html')


@app.route('/recommend')
def recommend():
    with open('meals.json', 'r') as f:
        meals = json.load(f)
    recommendations = {}
    for category in ['breakfast', 'lunch', 'dinner', 'snacks']:
        recommendations[category] = meals.get(category, [])[:3]
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