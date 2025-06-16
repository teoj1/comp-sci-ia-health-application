document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    document.body.addEventListener('click', handleClickEvents);
    // Add event for the generate button
    const generateBtn = document.getElementById('generateMealsBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', loadRecommendations);
    }
}
// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    loadRecommendations();
    setupEventListeners();
});

// Set up all event listeners
function setupEventListeners() {
    // Use event delegation for dynamic buttons
    document.body.addEventListener('click', handleClickEvents);
}

// Handle all click events in the document
function handleClickEvents(event) {
    const target = event.target;
    
    // Handle View Details buttons
    if (target.classList.contains('details-btn')) {
        const mealId = parseInt(target.dataset.id);
        showDetails(mealId);
    }
    
    // Handle modal close button
    if (target.classList.contains('modal-close')) {
        closeModal();
    }
    
    // Close modal when clicking outside content
    if (target.classList.contains('modal')) {
        closeModal();
    }
}

// Load meal recommendations from backend
async function loadRecommendations() {
    try {
        const response = await fetch('/recommend');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const recommendations = await response.json();
        renderMeals(recommendations);
    } catch (error) {
        console.error('Failed to load recommendations:', error);
        showErrorMessage('Failed to load meals. Please try again later.');
    }
}

// Render meals to the DOM
function renderMeals(recommendations) {
    const container = document.getElementById('mealSections');
    container.innerHTML = '';

    for (const [category, meals] of Object.entries(recommendations)) {
        if (meals.length === 0) continue;
        
        const sectionHTML = `
        <div class="meal-section">
            <h2>${category.charAt(0).toUpperCase() + category.slice(1)}</h2>
            <div class="meal-options">
                ${meals.map(meal => createMealCard(meal)).join('')}
            </div>
        </div>
        `;
        container.innerHTML += sectionHTML;
    }
}

// Create meal card HTML
function createMealCard(meal) {
    return `
    <div class="meal-card">
        <h3>${meal.name}</h3>
        <div class="nutrition-grid">
            <span>Calories: ${meal.nutrition.calories}</span>
            <span>Protein: ${meal.nutrition.protein}g</span>
            <span>Carbs: ${meal.nutrition.carbs}g</span>
            <span>Fat: ${meal.nutrition.fat}g</span>
        </div>
        <p><strong>Dietary:</strong> ${meal.diet.join(', ')}</p>
        <p><strong>Ready in:</strong> ${meal.cook_time} minutes</p>
        <button class="details-btn" data-id="${meal.id}">View Details</button>
    </div>
    `;
}

// Show meal details modal
async function showDetails(mealId) {
    try {
        const response = await fetch(`/meal/${mealId}`);
        if (!response.ok) throw new Error('Meal not found');
        
        const meal = await response.json();
        renderModal(meal);
    } catch (error) {
        console.error('Failed to load meal details:', error);
        showErrorMessage('Failed to load meal details. Please try again.');
    }
}

// Render modal to the DOM
function renderModal(meal) {
    const modalContainer = document.getElementById('modalContainer');
    
    const modalHTML = `
    <div class="modal">
        <div class="modal-content">
            <button class="modal-close">&times;</button>
            <h2>${meal.name}</h2>
            <p><strong>Cooking Time:</strong> ${meal.cook_time} minutes</p>
            <p><strong>Dietary:</strong> ${meal.diet.join(', ')}</p>
            
            <h3>Nutritional Information</h3>
            <div class="nutrition-grid">
                <span>Calories: ${meal.nutrition.calories}</span>
                <span>Protein: ${meal.nutrition.protein}g</span>
                <span>Carbs: ${meal.nutrition.carbs}g</span>
                <span>Fat: ${meal.nutrition.fat}g</span>
            </div>
            
            <h3>Ingredients</h3>
            <ul>${meal.ingredients.map(i => `<li>${i}</li>`).join('')}</ul>
        </div>
    </div>
    `;
    
    modalContainer.innerHTML = modalHTML;
    
    // Add keyboard support
    document.addEventListener('keydown', handleKeyDown);
}

// Close modal
function closeModal() {
    const modalContainer = document.getElementById('modalContainer');
    modalContainer.innerHTML = '';
    
    // Clean up keyboard listener
    document.removeEventListener('keydown', handleKeyDown);
}

// Handle Escape key to close modal
function handleKeyDown(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
}

// Show error message
function showErrorMessage(message) {
    const container = document.getElementById('mealSections');
    container.innerHTML = `
        <div class="error-message">
            <p>${message}</p>
            <button onclick="location.reload()">Reload Page</button>
        </div>
    `;
}