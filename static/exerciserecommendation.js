// Example muscle groups
const MUSCLE_GROUPS = [
    "Chest", "Back", "Shoulders", "Arms", "Legs", "Abdominals", "Glutes", "Calves"
];

let lastRecommendations = [];

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('generateExercisebtn').addEventListener('click', loadExercises);
    loadExercises(); // Load initial exercises on page load
    
});

function loadExercises() {
    fetch('/recommend_exercise?user_id=' + window.currentUserId)
        .then(response => response.json())
        .then(data => displayExercises(data));
}

document.addEventListener('DOMContentLoaded', () => {
    // Show muscle selection if goal is muscle gain
    document.getElementById('goal').addEventListener('change', function() {
        if (this.value === 'muscle_gain') {
            showMuscleSelection();
        } else {
            document.getElementById('muscleSelection').style.display = 'none';
        }
    });

    document.getElementById('getExercisesBtn').addEventListener('click', getExercises);

    // Generate muscle group checkboxes
    const muscleDiv = document.getElementById('muscleGroups');
    MUSCLE_GROUPS.forEach(muscle => {
        const label = document.createElement('label');
        label.innerHTML = `<input type="checkbox" value="${muscle}"> ${muscle}`;
        muscleDiv.appendChild(label);
    });
});

function showMuscleSelection() {
    document.getElementById('muscleSelection').style.display = '';
}

function getExercises() {
    const user_id = window.currentUserId;
    const goal = document.getElementById('goal').value;
    const level = document.getElementById('level').value;
    const gender = window.currentUserGender || 'male'; // Set this from backend/session
    const muscles = Array.from(document.querySelectorAll('#muscleGroups input:checked')).map(cb => cb.value);
    const age = window.currentUserAge; // Assuming you have this data
    const weight = window.currentUserWeight; // Assuming you have this data

    fetch('/api/exercise_recommendation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id,
            goal,
            level,
            gender,
            muscles, // array
            age,
            weight
        })
    })
    .then(res => res.json())
    .then(data => {
        lastRecommendations = data.recommendations;
        displayExercises(data.recommendations);
    });
}

function displayExercises(exercises) {
    const div = document.getElementById('exerciseResults');
    if (!exercises.length) {
        div.innerHTML = '<p>No suitable exercises found. Try selecting different muscles or lowering intensity.</p>';
        return;
    }
    div.innerHTML = exercises.map(ex => `
        <div class="exercise-card">
            <h3>${ex.name}</h3>
            <img src="${ex.imageUrl || ''}" alt="${ex.name}" style="max-width:120px;">
            <p><b>Type:</b> ${ex.exerciseType}</p>
            <p><b>Body Parts:</b> ${ex.bodyParts.join(', ')}</p>
            <p><b>Target Muscles:</b> ${ex.targetMuscles.join(', ')}</p>
            <p><b>Secondary Muscles:</b> ${ex.secondaryMuscles.join(', ')}</p>
            <p><b>Equipment:</b> ${ex.equipments.join(', ')}</p>
            <button onclick="confirmExercise('${ex.exerciseId}')">I've done this exercise</button>
        </div>
    `).join('') + `<button onclick="regenerateExercises()">Regenerate</button>`;
}

function confirmExercise(exerciseId) {
    // Log exercise for cooldown (send to backend in production)
    alert('Exercise logged!');
    // Optionally update daily stats here
}

function regenerateExercises() {
    // Optionally send a flag to backend to lower intensity
    getExercises();
}