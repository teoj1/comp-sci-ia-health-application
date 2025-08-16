document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('generateMealsBtn').addEventListener('click', loadMeals);
});


function loadMeals() {
    fetch('/recommend?user_id=' + window.currentUserId)
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
            section.innerHTML += meals[type].map(meal => `
                <div class="meal-card">
                    <h3>${meal.description}</h3>
                    <p>Ingredients: ${Array.isArray(meal.ingredients) ? meal.ingredients.join(', ') : meal.ingredients}</p>
                    <p>Calories: ${meal.nutrition.calories} kcal</p>
                    <p>Protein: ${meal.nutrition.protein}g</p>
                    <p>Macronutrients: ${meal.nutrition.protein}g protein, ${meal.nutrition.carbs}g carbs, ${meal.nutrition.fat}g fat</p>
                </div>
            `).join('');
            mealSections.appendChild(section);
        }
    });
}