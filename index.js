document.addEventListener('DOMContentLoaded', function() {
    const button = document.getElementById('myButton');
    const message = document.getElementById('message');
    button.addEventListener('click', function() {
        alert('Button clicked!');
    });
    
    // Additional functionality can be added here
    console.log('Document is ready and script is running.');
    button.addEventListener('click', function() {
        message.textContent = "Button was clicked!";
        message.style.color = "green";

        setTimeout(() => { 
            message.textContent = "";
        }, 2000);
    })
});
