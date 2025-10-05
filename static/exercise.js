/*
  Exercise form frontend
  - Handles normal activities (duration in minutes)
  - Handles gym entries (sets, reps, time per rep, restBetween, load)
  - Uses MET formula: calories/min = MET * bodyweight(kg) * 0.0175
  - Gym calories are scaled by load relative to bodyweight and an intensity multiplier
*/

// MET-based simple calculator for cardio/other
function calculateCalories(type, durationMin, intensity) {
    const METS = {
        "Running": 9.8,
        "Cycling": 7.5,
        "Swimming": 8.0,
        "Walking": 3.5,
        "Yoga": 2.5,
        "Strength Training": 6.0,
        "Rowing": 7.0,
        "Dancing": 5.5
    };
    const met = METS[type] || 5.0;
    const userBodyWeightKg = window.currentUserWeightKg || 70;
    // Map intensity 1-5 to scale ~0.9-1.4
    const intensityScale = 0.9 + ((Number(intensity || 2) - 1) * 0.125);
    const caloriesPerMin = met * userBodyWeightKg * 0.0175;
    return Math.round(caloriesPerMin * Number(durationMin || 0) * intensityScale);
}

// Gym calculator: accepts either durationMin OR (sets,reps,timePerRep + restBetween)
const GYM_METS = {
    "squat": 6.0,
    "deadlift": 6.5,
    "bench press": 5.5,
    "overhead press": 6.0,
    "pull-up": 8.0,
    "leg presses": 6.0,
    "bicep curls": 4.0,
    "skullcrushers": 4.5,
    "one arm rows": 5.0,
    "lunges": 5.5
};

function calculateGymCalories({ durationMin=0, intensity=2, userBodyWeightKg=70, liftWeightKg=0, exerciseKey='squat', sets=0, reps=0, timePerRep=3, restBetween=60 }) {
    // derive duration from reps/sets if duration not provided
    let derivedDurationMin = Number(durationMin) || 0;
    const totalReps = Number(sets || 0) * Number(reps || 0);
    if ((!derivedDurationMin || derivedDurationMin <= 0) && totalReps > 0) {
        const totalWorkSeconds = totalReps * Number(timePerRep || 3);
        const totalRestSeconds = Math.max(0, (Number(sets || 0) - 1)) * Number(restBetween || 60);
        derivedDurationMin = (totalWorkSeconds + totalRestSeconds) / 60.0;
    }

    const met = GYM_METS[(exerciseKey || '').toLowerCase()] || 5.0;
    const body_w = Number(userBodyWeightKg || 70);

    const caloriesPerMin = met * body_w * 0.0175;

    // scale load relative to bodyweight (modest effect), capped
    const loadRatio = Number(liftWeightKg || 0) / Math.max(1, body_w);
    const loadScale = 1.0 + Math.min(0.8, loadRatio * 0.25);

    const intensityScale = 0.9 + ((Number(intensity || 2) - 1) * 0.125);

    const totalCalories = caloriesPerMin * derivedDurationMin * loadScale * intensityScale;
    return {
        calories: Math.round(totalCalories),
        durationMin: Math.round(derivedDurationMin * 10) / 10
    };
}

// UI helpers - create and manage gym inputs
function ensureGymContainer() {
    const containerId = 'gymOptionsContainer';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'gym-options';
        container.innerHTML = `
            <label for="gymExercise">Gym exercise</label>
            <select id="gymExercise" class="input">
                <option value="squat">Squat</option>
                <option value="deadlift">Deadlift</option>
                <option value="bench press">Bench Press</option>
                <option value="overhead press">Overhead Press</option>
                <option value="pull-up">Pull-up</option>
                <option value="leg presses">Leg Presses</option>
                <option value="bicep curls">Bicep Curls</option>
                <option value="skullcrushers">Skullcrushers</option>
                <option value="one arm rows">One Arm Rows</option>
                <option value="lunges">Lunges</option>
            </select>

            <label for="liftWeight">Load used (kg)</label>
            <input id="liftWeight" type="number" min="0" step="1" class="input" placeholder="e.g. 80">

            <label for="gymSets">Sets</label>
            <input id="gymSets" type="number" min="1" step="1" class="input" value="2">

            <label for="gymReps">Reps (per set)</label>
            <input id="gymReps" type="number" min="1" step="1" class="input" value="10">

            <label for="timePerRep">Avg seconds per rep (optional)</label>
            <input id="timePerRep" type="number" min="0.5" step="0.1" class="input" value="3">

            <label for="restBetween">Rest between sets (sec)</label>
            <input id="restBetween" type="number" min="0" step="1" class="input" value="60">
        `;
        const parent = document.getElementById('activityForm') || document.body;
        parent.insertBefore(container, parent.firstChild);
    }
    return container;
}

function onActivityTypeChange() {
    const activityTypeEl = document.getElementById('activityType');
    if (!activityTypeEl) return;
    const activityType = activityTypeEl.value || '';
    const container = document.getElementById('gymOptionsContainer');
    if (activityType.toLowerCase() === 'gym') {
        const c = ensureGymContainer();
        c.style.display = 'block';
    } else if (container) {
        container.style.display = 'none';
    }
}

// Recalculate calories for current inputs
function updateCalories() {
    const activityTypeEl = document.getElementById('activityType');
    if (!activityTypeEl) return;
    const type = activityTypeEl.value || '';
    const intensityEl = document.getElementById('intensity');
    const intensity = intensityEl ? parseInt(intensityEl.value || '2') : 2;
    const caloriesEl = document.getElementById('calories');
    const durationEl = document.getElementById('duration');

    if (type.toLowerCase() === 'gym') {
        const gymExercise = (document.getElementById('gymExercise')?.value) || 'squat';
        const liftWeight = parseFloat(document.getElementById('liftWeight')?.value) || 0;
        const sets = parseInt(document.getElementById('gymSets')?.value) || 0;
        const reps = parseInt(document.getElementById('gymReps')?.value) || 0;
        const timePerRep = parseFloat(document.getElementById('timePerRep')?.value) || 3;
        const restBetween = parseFloat(document.getElementById('restBetween')?.value) || 60;

        const userBodyWeightKg = window.currentUserWeightKg || 70;
        const result = calculateGymCalories({
            durationMin: parseFloat(durationEl?.value) || 0,
            intensity,
            userBodyWeightKg,
            liftWeightKg: liftWeight,
            exerciseKey: gymExercise,
            sets,
            reps,
            timePerRep,
            restBetween
        });

        if (durationEl) durationEl.value = result.durationMin;
        if (caloriesEl) caloriesEl.value = result.calories;
    } else {
        const durationMin = parseFloat(durationEl?.value) || 0;
        const calories = calculateCalories(type, durationMin, intensity);
        if (caloriesEl) caloriesEl.value = calories;
    }
}

// Submit handler - collect fields and post to backend
function submitActivityForm(e) {
    e.preventDefault();
    const activityTypeVal = document.getElementById('activityType')?.value || '';
    const dateTimeVal = document.getElementById('dateTime')?.value || new Date().toISOString();
    const intensityVal = parseInt(document.getElementById('intensity')?.value || '2');
    const durationVal = parseInt(document.getElementById('duration')?.value || '0');
    const caloriesVal = parseInt(document.getElementById('calories')?.value || '0');

    const payload = {
        user_id: window.currentUserId,
        activityType: activityTypeVal,
        duration: durationVal,
        intensity: intensityVal,
        calories: caloriesVal,
        dateTime: dateTimeVal
    };

    if (activityTypeVal.toLowerCase() === 'gym') {
        payload.gymExercise = document.getElementById('gymExercise')?.value || '';
        payload.liftWeight = parseFloat(document.getElementById('liftWeight')?.value || '0');
        payload.sets = parseInt(document.getElementById('gymSets')?.value || '0');
        payload.reps = parseInt(document.getElementById('gymReps')?.value || '0');
        payload.timePerRep = parseFloat(document.getElementById('timePerRep')?.value || '3');
        payload.restBetween = parseFloat(document.getElementById('restBetween')?.value || '60');
        // duration was updated by updateCalories to reflect derived minutes
        payload.duration = parseInt(document.getElementById('duration')?.value || payload.duration);
    }

    fetch('/api/activity', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            if (typeof renderHistory === 'function') try { renderHistory(); } catch {}
            // optional redirect to dashboard
            if (window.currentUserId) {
                window.location.href = "/dashboard?user_id=" + window.currentUserId;
            }
        } else {
            alert('Failed to save activity: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(err => {
        console.error('Submit activity error', err);
        alert('Failed to save activity.');
    });
}

// Attach listeners safely
document.addEventListener('DOMContentLoaded', () => {
    const intensitySlider = document.getElementById('intensity');
    const intensityValue = document.getElementById('intensityValue');
    if (intensitySlider && intensityValue) {
        intensitySlider.addEventListener('input', () => {
            intensityValue.textContent = intensitySlider.value;
            updateCalories();
        });
    }

    const activityTypeEl = document.getElementById('activityType');
    if (activityTypeEl) {
        activityTypeEl.addEventListener('input', () => {
            onActivityTypeChange();
            updateCalories();
        });
    }

    const durationEl = document.getElementById('duration');
    if (durationEl) durationEl.addEventListener('input', updateCalories);

    // delegate input changes from dynamic gym inputs
    document.addEventListener('input', (e) => {
        const ids = ['gymExercise','liftWeight','gymSets','gymReps','timePerRep','restBetween','intensity','duration','activityType'];
        if (e.target && ids.includes(e.target.id)) updateCalories();
    });

    const form = document.getElementById('activityForm');
    if (form) form.addEventListener('submit', submitActivityForm);

    // initial UI setup
    onActivityTypeChange();
    updateCalories();
});