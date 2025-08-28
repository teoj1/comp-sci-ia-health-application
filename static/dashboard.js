function fetchStats() {
    fetch('/api/dashboard_stats?user_id=' + window.currentUserId)
        .then(res => res.json())
        .then(stats => updateDashboard(stats));
}

// Real-time auto-refresh every 30s
setInterval(fetchStats, 30000);

document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchDailySummary();
});

function updateDashboard(stats) {
    // Diet summary
    document.getElementById('dietStats').innerHTML = `
        <b>Today's Calories:</b> ${stats.total_calories} / ${stats.recommended_calories} kcal<br>
        <b>Protein:</b> ${stats.macros.protein}g<br>
        <b>Carbs:</b> ${stats.macros.carbs}g<br>
        <b>Fat:</b> ${stats.macros.fat}g
    `;
    // Exercise summary
    document.getElementById('exerciseStats').innerHTML = `
        <b>Minutes:</b> ${stats.exercise.minutes} min<br>
        <b>Calories Burned:</b> ${stats.exercise.calories} kcal
    `;
    // Macronutrient progress bars (Chart.js doughnut)
    new Chart(document.getElementById('macroChart'), {
        type: 'doughnut',
        data: {
            labels: ['Protein', 'Carbs', 'Fat'],
            datasets: [{
                data: [
                    stats.macros.protein,
                    stats.macros.carbs,
                    stats.macros.fat
                ],
                backgroundColor: ['#2980b9', '#bfa100', '#27ae60']
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom' } }
        }
    });
    // Weekly calorie trend (line)
    new Chart(document.getElementById('calorieTrendChart'), {
        type: 'line',
        data: {
            labels: Array.from({length: 7}, (_, i) => `Day ${i+1}`),
            datasets: [{
                label: 'Calories',
                data: stats.calories_7d,
                borderColor: '#e74c3c',
                fill: false
            }]
        }
    });
    // Weekly exercise trend (line)
    new Chart(document.getElementById('exerciseTrendChart'), {
        type: 'line',
        data: {
            labels: Array.from({length: 7}, (_, i) => `Day ${i+1}`),
            datasets: [{
                label: 'Minutes',
                data: stats.ex_minutes_7d,
                borderColor: '#2d5cff',
                fill: false
            }, {
                label: 'Calories Burned',
                data: stats.ex_calories_7d,
                borderColor: '#27ae60',
                fill: false
            }]
        }
    });
    // Intensity pie chart
    new Chart(document.getElementById('intensityPieChart'), {
        type: 'pie',
        data: {
            labels: ['Low', 'Moderate', 'High'],
            datasets: [{
                data: [
                    stats.intensity_dist.Low,
                    stats.intensity_dist.Moderate,
                    stats.intensity_dist.High
                ],
                backgroundColor: ['#e3f0ff', '#ffe6e6', '#ffe6ff']
            }]
        }
    });
    // Progress nudges
    let nudge = '';
    if (stats.total_calories < stats.recommended_calories) {
        nudge += 'Try increasing your calorie intake by ' + (stats.recommended_calories - stats.total_calories) + ' kcal.<br>';
    }
    if (stats.macros.protein < stats.macros.target.protein) {
        nudge += 'Increase protein by ' + (stats.macros.target.protein - stats.macros.protein) + 'g.<br>';
    }
    if (stats.exercise.minutes < 30) {
        nudge += 'Aim for at least 30 minutes of exercise today.<br>';
    }
    document.getElementById('dailySuggestions').innerHTML = nudge || 'Great job! Keep it up!';
}

function fetchDailySummary() {
    fetch('/api/daily_summary?user_id=' + window.currentUserId)
        .then(res => res.json())
        .then(data => {
            if (data.error) return;
            document.getElementById('dailyMacros').innerHTML = `
                <b>Calories:</b> ${data.macronutrients.calories} kcal<br>
                <b>Protein:</b> ${data.macronutrients.protein}g<br>
                <b>Carbs:</b> ${data.macronutrients.carbs}g<br>
                <b>Fat:</b> ${data.macronutrients.fat}g
            `;
            document.getElementById('dailyExercise').innerHTML = `
                <b>Minutes:</b> ${data.exercise.minutes} min<br>
                <b>Calories Burned:</b> ${data.exercise.calories_burned} kcal<br>
                <b>Activities:</b><br>
                <ul>
                    ${data.exercise.activities.map(a => `<li>${a.type} (${a.duration} min, Intensity ${a.intensity}, ${a.calories} kcal)</li>`).join('')}
                </ul>
            `;
        });
}