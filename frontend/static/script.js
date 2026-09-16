const loginForm = document.getElementById('login-form');
const loginMessage = document.getElementById('login-message');
const sessionMessage = document.getElementById('session-message');
const adminLink = document.getElementById('admin-link');
const logoutButton = document.getElementById('logout-button');

function showSession(data) {
    sessionMessage.textContent = `Signed in as ${data.username}`;
    adminLink.hidden = !data.is_admin;
    logoutButton.hidden = false;
}

function clearSession() {
    sessionMessage.textContent = '';
    adminLink.hidden = true;
    logoutButton.hidden = true;
}

async function checkSession() {
    const response = await fetch('/api/me');
    if (response.ok) {
        showSession(await response.json());
    } else {
        clearSession();
    }
}

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
    if (response.ok) showSession(data);
});

logoutButton.addEventListener('click', async () => {
    const response = await fetch('/api/logout', {method: 'POST'});
    const data = await response.json();
    loginMessage.textContent = data.message;
    loginForm.reset();
    clearSession();
});

checkSession();