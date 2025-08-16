 document.addEventListener('DOMContentLoaded', function() {
    
    // gathering input values
    const form = document.getElementById('healthForm');
    const outputSection = document.getElementById('outputSection');
    // gathering name input
    const displayName = document.getElementById('displayName');
    const fnameInput = document.getElementById('fname');
    const lnameInput = document.getElementById('lname');
    // gathering weight input
    const weightInput = document.getElementById('weight');
    const displayWeight = document.getElementById('displayWeight');
    // gathering height input
    const heightInput = document.getElementById('height');
    const displayHeight = document.getElementById('displayHeight');
    // gathering password input
    const passwordInput = document.getElementById('password');
    const displayPassword = document.getElementById('displayPassword');
    // gathering confirm password input
    const password2Input = document.getElementById('confirmPassword');
    const displayPassword2 = document.getElementById('displayPassword2');

    // gathering gender input
    const genderInput = document.getElementById('gender');
    const displayGender = document.getElementById('displayGender');

    //gathering dietary preference input
    const dietaryRestrictionInput = document.getElementById('dietaryRestrictions');
    const displaydietaryRestriction = document.getElementById('displayDietaryRestrictions');

    // gathering activity level input
    const activityLevelInput = document.getElementById('activityLevel');
    const displayActivityLevel = document.getElementById('displayActivityLevel');

    // gathering health goal input 
    const goalInput = document.getElementById('goal');
    const displayGoal = document.getElementById('displayGoal');

    // gathering allergies input
    const allergiesInput = document.getElementById('allergies');
    const displayAllergies = document.getElementById('displayAllergies');

    // gathering food preferences input
    const foodPreferencesInput = document.getElementById('foodPreferences');
    const displayFoodPreferences = document.getElementById('displayFoodPreferences');

    // displaying content 
    form.addEventListener('dashboard', function(event) {
        event.preventDefault();
        // trimming input values 
        const fname = document.getElementById('fname').value.trim();
        const lname = document.getElementById('lname').value.trim();
        const weight = document.getElementById('weight').value.trim();
        const height = document.getElementById('height').value.trim();
        const password = document.getElementById('password').value.trim();
        const password2 = document.getElementById('confirmPassword').value.trim();
        const gender = document.getElementById('gender').value.trim();
        const dietaryRestriction = document.getElementById('dietaryRestrictions').value.trim();
        const activityLevel = document.getElementById('activityLevel').value.trim();
        const goal = document.getElementById('goal').value.trim();
        const allergies = document.getElementById('allergies').value.trim();
        const foodPreferences = document.getElementById('foodPreferences').value.trim();

        // Validate each field, prevent submission if invalid
        if (!fname || !lname) {
            alert('Please enter your first and last name.');
            event.preventDefault();
            return;
        }
        if (!weight || isNaN(weight) || parseFloat(weight) <= 15) {
            alert('Please enter a valid weight greater than 15kg.');
            event.preventDefault();
            return;
        }
        if (!height || isNaN(height) || parseFloat(height) <= 75) {
            alert('Please enter a valid height greater than 75cm.');
            event.preventDefault();
            return;
        }
        if (!password || password.length < 12 || password.length > 20) {
            alert('Please enter a valid password between 12 and 20 characters long.');
            event.preventDefault();
            return;
        }
        if (password !== password2) {
            alert('Passwords do not match. Please try again.');
            event.preventDefault();
            return;
        }
        if (!gender) {
            alert('Please select a gender.');
            event.preventDefault();
            return;
        }
        if (!dietaryRestriction) {
            alert('Please select a dietary preference.');
            event.preventDefault();
            return;
        }
        if (!activityLevel) {
            alert('Please select an activity level.');
            event.preventDefault();
            return;
        }
        if (!goal) {
            alert('Please select a health goal.');
            event.preventDefault();
            return;
        }
        if (!allergies) {
            alert('Please enter any allergies you may have.');
            event.preventDefault();
            return;
        }
        if (!foodPreferences) {
            alert('Please enter any food preferences you may have.');
            event.preventDefault();
            return;
        } 
       });
});
