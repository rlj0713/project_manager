const registerForm = document.getElementById('register-form');
const registerMessage = document.getElementById('register-message');

registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    registerMessage.textContent = 'Creating account...';

    const response = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: registerForm.username.value,
            password: registerForm.password.value,
        }),
    });
    const data = await response.json();
    registerMessage.textContent = data.message;
    if (response.ok) {
        registerForm.reset();
    }
});