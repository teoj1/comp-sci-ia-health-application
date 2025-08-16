document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('generateMealsBtn').addEventListener('click', loadMeals);
});

function loadMeals() {
    fetch('/recommend?user_id=' + getCurrentUserId())
        .then(response => response.json())
        .then(data => displayMeals(data));
}

function displayMeals(meals) {
    const mealSections = document.getElementById('mealSections');
    mealSections.innerHTML = '';
    ['breakfast', 'lunch', 'dinner', 'snacks'].forEach(type => {
        if (meals[type] && Array.isArray(meals[type]) && meals[type].length > 0) {
            const section = document.createElement('div');
            section.innerHTML = `<h2>${type.charAt(0).toUpperCase() + type.slice(1)}</h2>`;
            meals[type].forEach(meal => {
                section.innerHTML += `<div class="meal-card">
                    <h3>${meal.name}</h3>
                    <p>Ingredients: ${meal.ingredients.join(', ')}</p>
                    <p>Calories: ${meal.nutrition.calories} kcal</p>
                    <p>Protein: ${meal.nutrition.protein}g</p>
                    <p>Macronutrients: ${meal.nutrition.protein}g protein, ${meal.nutrition.carbs}g carbs, ${meal.nutrition.fat}g fat</p>
                </div>`;
            }).join('');
            mealSections.appendChild(section);
        }
    });
}