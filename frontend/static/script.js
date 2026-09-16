const loginForm = document.getElementById('login-form');
const loginMessage = document.getElementById('login-message');

loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    loginMessage.textContent = 'Signing in...';

    const response = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: loginForm.username.value,
            password: loginForm.password.value,
        }),
    });
    const data = await response.json();
    loginMessage.textContent = data.message;
});