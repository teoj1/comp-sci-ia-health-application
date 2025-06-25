document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('generateMealsBtn').addEventListener('click', loadMeals);
});

function loadMeals() {
    fetch('/recommend')
        .then(response => response.json())
        .then(data => displayMeals(data));
}

function displayMeals(meals) {
    const mealSections = document.getElementById('mealSections');
    mealSections.innerHTML = '';
    ['breakfast', 'lunch', 'dinner'].forEach(type => {
        if (meals[type]) {
            const section = document.createElement('div');
            section.innerHTML = `<h2>${type.charAt(0).toUpperCase() + type.slice(1)}</h2>`;
            meals[type].forEach(meal => {
                section.innerHTML += `<div class="meal-card">
                    <h3>${meal.name}</h3>
                    <p>Ingredients: ${meal.ingredients.join(', ')}</p>
                </div>`;
            });
            mealSections.appendChild(section);
        }
    });
}