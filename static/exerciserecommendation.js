// muscle groups
const MUSCLE_GROUPS = [
    "Chest", "Back", "Shoulders", "Arms", "Legs", "Abdominals", "Glutes", "Calves"
];

let lastRecommendations = [];

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('goal').addEventListener('change', function() {
        if (this.value === 'muscle_gain' || this.value === 'flexibility') {
            showMuscleSelection();
        } else {
            document.getElementById('muscleSelection').style.display = 'none';
        }
    });

    document.getElementById('generateExerciseBtn').addEventListener('click', function() {
        getExercises();
    });

    document.getElementById('getExercisesBtn').addEventListener('click', function() {
        getExercises();
    });

    // Generate muscle group checkboxes
    const muscleDiv = document.getElementById('muscleGroups');
    MUSCLE_GROUPS.forEach(muscle => {
        const label = document.createElement('label');
        label.innerHTML = `<input type="checkbox" value="${muscle}"> ${muscle}`;
        muscleDiv.appendChild(label);
    });

    // Auto-refresh exercises when muscle group selection changes
    muscleDiv.addEventListener('change', function() {
        const goal = document.getElementById('goal').value;
        if (goal === 'muscle_gain' || goal === 'flexibility') {
            getExercises();
        }
    });
});

function showMuscleSelection() {
    document.getElementById('muscleSelection').style.display = '';
}

function getExercises(lowerIntensity = false) {
    const user_id = window.currentUserId;
    const goal = document.getElementById('goal').value;
    
    const levelSelect = document.getElementById('level');
    const level = (levelSelect && levelSelect.value) ? levelSelect.value : undefined;
    const gender = window.currentUserGender || 'male';
    const muscles = Array.from(document.querySelectorAll('#muscleGroups input:checked')).map(cb => cb.value);
    const age = window.currentUserAge;
    const weight = window.currentUserWeight;

    const payload = {
        user_id,
        goal,
        gender,
        muscles,
        age,
        weight,
        lower_intensity: lowerIntensity
    };
    if (level !== undefined) payload.level = level; 

    fetch('/api/exercise_recommendation', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
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
    div.innerHTML = exercises.map(ex => {
        let details = `
            <h3>${ex.name}</h3>
            <img src="${ex.imageUrl || ''}" alt="${ex.name}" style="max-width:120px;">
            <p><b>Type:</b> ${ex.exerciseType}</p>
        `;
        if (ex.exerciseType === "strength") {
            details += `
                <p><b>Body Parts:</b> ${ex.bodyParts ? ex.bodyParts.join(', ') : ''}</p>
                <p><b>Target Muscles:</b> ${ex.targetMuscles ? ex.targetMuscles.join(', ') : ''}</p>
                <p><b>Equipment:</b> ${ex.equipments ? ex.equipments.join(', ') : ''}</p>
            `;
        } else if (ex.exerciseType === "cardio") {
            details += `
                <p><b>Estimated Calories Burned:</b> ${ex.caloriesBurned || 'N/A'}</p>
                <p><b>Duration:</b> ${ex.duration || 'N/A'} min</p>
            `;
        } else if (ex.exerciseType === "stretching") {
            details += `
                <p><b>Flexibility Focus:</b> ${ex.bodyParts ? ex.bodyParts.join(', ') : ''}</p>
                <p><b>Instructions:</b> ${ex.instructions || 'See link for details.'}</p>
            `;
        }
        details += `<button onclick="confirmExercise('${ex.exerciseId}')">I've done this exercise</button>`;
        return `<div class="exercise-card">${details}</div>`;
    }).join('') + `<button onclick="regenerateExercises()">Regenerate</button>`;
}

function confirmExercise(exerciseId) {
    alert('Exercise logged!');
    
}

function regenerateExercises() {
    getExercises(true); // Pass true to indicate lower intensity
}