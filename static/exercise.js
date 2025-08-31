function calculateCalories(type, duration, intensity) {
    // Simple MET-based estimation 
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
            user_id: window.currentUserId, // Make sure this is set in your exercise.html
            activityType: document.getElementById('activityType').value,
            duration: parseInt(document.getElementById('duration').value),
            intensity: parseInt(document.getElementById('intensity').value),
            calories: parseInt(document.getElementById('calories').value),
            dateTime: document.getElementById('dateTime').value
        };
        fetch('/api/activity', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(entry)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderHistory();
                this.reset();
                document.getElementById('intensityValue').textContent = 2;
                document.getElementById('calories').value = '';
                // IMMEDIATE DASHBOARD REFRESH:
                window.location.href = "/dashboard?user_id=" + window.currentUserId;
            } else {
                alert('Failed to save activity: ' + (data.error || 'Unknown error'));
            }
        });
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

    // Fetch activity history from backend
    let url = `/api/activity?user_id=${window.currentUserId}`;
    if (from) url += `&from=${from}`;
    if (to) url += `&to=${to}`;
    if (type) url += `&type=${encodeURIComponent(type)}`;

    fetch(url)
        .then(res => res.json())
        .then(filtered => {
            let html = '';
            if (!filtered || filtered.length === 0) {
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
                                <td>${e.activityType}</td>
                                <td>${e.duration}</td>
                                <td>${e.intensity}</td>
                                <td>${e.calories}</td>
                                <td>${e.dateTime.replace('T', ' ').replace('Z','')}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>`;
            }
            document.getElementById('historyTable').innerHTML = html;
        });
}