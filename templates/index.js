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
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        // trimming input values 
        const fname = fnameInput.value.trim();
        const lname = lnameInput.value.trim();
        const weight = weightInput.value.trim();
        const height = heightInput.value.trim();
        const password = passwordInput.value.trim();
        const password2 = password2Input.value.trim();
        const gender = genderInput.value.trim();
        const dietaryRestriction = dietaryRestrictionInput.value.trim();
        const activityLevel = activityLevelInput.value.trim();
        const goal = goalInput.value.trim();
        const allergies = allergiesInput.value.trim();
        const foodPreferences = foodPreferencesInput.value.trim();
        // checking for first and last name input
        if (fname && lname) {
            displayName.textContent = fname + ' ' + lname;
            outputSection.classList.remove('hidden');
        } else {
            displayName.textContent = '';
            outputSection.classList.add('hidden');
            alert('Please fill out both fields.');
        }

        // Checking for weight input
        if (weight) {
            const weightValue = parseFloat(weight);
            if (isNaN(weightValue) || weightValue <= 15) {
                alert('Please enter a valid weight greater than 15kg');
                return;
            } else {
                displayWeight.textContent = weightValue;
                outputSection.classList.remove('hidden');
            }  
        }

        // checking for height input
        if (height) {
            const heightValue = parseFloat(height);
            if(isNaN(heightValue) || heightValue <= 75) {
                alert('Please enter a valid height greater than 75cm');
                return;
            } else {
                displayHeight.textContent = heightValue;
                outputSection.classList.remove('hidden');
            }
        }

        // checking for password input
        if (password) {
            if (password.length < 12 || password.length > 20) { // https://www.google.com/search?client=opera-gx&q=criteria+for+a+strong+password&sourceid=opera&ie=UTF-8&oe=UTF-8
                alert('Please enter a valid password between 12 and 20 characters long');
                return;
            }
            else {
                if (password === password2) {
                    displayPassword.textContent = password;
                    outputSection.classList.remove('hidden');
                } else {
                    alert('Passwords do not match. Please try again.');
                    return;
                }
                
            }
        }
        
        // checking for gender input (whether a dropdown has been selected or not)
        if (gender) {
            displayGender.textContent = gender;
            outputSection.classList.remove('hidden')
        } else {
            alert('Please select a gender')
            return;
        }

        // checking for dietary preference input

        if (dietaryRestriction) {
            displaydietaryRestriction.textContent = dietaryRestriction;
            outputSection.classList.remove('hidden');
        } else {
            alert('Please select a dietary preference');
            return;
        }

        // checking for activity level input 
        if (activityLevel) {
            displayActivityLevel.textContent = activityLevel;
            outputSection.classList.remove('hidden');
        } else {
            alert('Please select an activity level');
            return;
        }

        if (goal) {
            displayGoal.textContent = goal;
            outputSection.classList.remove('hidden');

        } else {
            alert('Please select a health goal');
            return;
        }
        
        if (allergies) {
            displayAllergies.textContent = allergies;
            outputSection.classList.remove('hidden');
        }
        else {
            alert('Please enter any allergies you may have');
            return;
        }

        if (foodPreferences) {
            displayFoodPreferences.textContent = foodPreferences;
            outputSection.classList.remove('hidden');
        } else {
            alert('Please enter any food preferences you may have');
            return;
        }
    });
});
