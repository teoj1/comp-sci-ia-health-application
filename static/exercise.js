// --- Demo data storage (replace with AJAX/Flask for real app) ---
let activityHistory = JSON.parse(localStorage.getItem('activityHistory') || "[]");

function calculateCalories(type, duration, intensity) {
    // Simple MET-based estimation (for demo)
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
    // Assume 70kg user for demo
    const met = METS[type] || 5;
    return Math.round(met * intensity * duration * 0.0175 * 70);
}

function updateCalories() {
    const type = document.getElementById('activityType').value;
    const duration = parseInt(document.getElementById('duration').value) || 0;
    const intensity = parseInt(document.getElementById('intensity').value) || 1;
    const calories = (type && duration) ? calculateCalories(type, duration, intensity) : 0;
    document.getElementById('calories').value = calories;
}

document.addEventListener('DOMContentLoaded', () => {
    // Intensity slider label
    const intensitySlider = document.getElementById('intensity');
    const intensityValue = document.getElementById('intensityValue');
    intensitySlider.addEventListener('input', () => {
        intensityValue.textContent = intensitySlider.value;
        updateCalories();
    });

    // Update calories on activity type or duration change
    document.getElementById('activityType').addEventListener('input', updateCalories);
    document.getElementById('duration').addEventListener('input', updateCalories);

    // Form submission
    document.getElementById('activityForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const entry = {
            type: document.getElementById('activityType').value,
            duration: parseInt(document.getElementById('duration').value),
            intensity: parseInt(document.getElementById('intensity').value),
            calories: parseInt(document.getElementById('calories').value),
            dateTime: document.getElementById('dateTime').value
        };
        activityHistory.push(entry);
        localStorage.setItem('activityHistory', JSON.stringify(activityHistory));
        renderHistory();
        this.reset();
        document.getElementById('intensityValue').textContent = 2;
        document.getElementById('calories').value = '';
    });

    // Filters
    document.getElementById('applyFilters').addEventListener('click', renderHistory);

    renderHistory();
    updateCalories();
});

function renderHistory() {
    const from = document.getElementById('filterFrom').value;
    const to = document.getElementById('filterTo').value;
    const type = document.getElementById('filterType').value;
    let filtered = activityHistory.slice();

    if (from) filtered = filtered.filter(e => e.dateTime >= from);
    if (to) filtered = filtered.filter(e => e.dateTime <= to + "T23:59");
    if (type) filtered = filtered.filter(e => e.type === type);

    let html = '';
    if (filtered.length === 0) {
        html = '<p style="color:#888;">No activity records found for the selected filter.</p>';
    } else {
        html = `<table class="activity-table">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Duration (min)</th>
                    <th>Intensity</th>
                    <th>Calories</th>
                    <th>Date & Time</th>
                </tr>
            </thead>
            <tbody>
                ${filtered.map(e => `
                    <tr>
                        <td>${e.type}</td>
                        <td>${e.duration}</td>
                        <td>${e.intensity}</td>
                        <td>${e.calories}</td>
                        <td>${e.dateTime.replace('T', ' ')}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>`;
    }
    document.getElementById('historyTable').innerHTML = html;
}