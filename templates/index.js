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
    });
});
