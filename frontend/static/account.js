const homeLink = document.getElementById('home-link');
const adminLink = document.getElementById('admin-link');
const registerLink = document.getElementById('register-link');
const logoutButton = document.getElementById('logout-button');

function updateAccount(data) {
    const authenticated = data.authenticated ?? true;
    homeLink.hidden = false;
    if (adminLink) adminLink.hidden = !authenticated || !data.is_admin;
    registerLink.hidden = authenticated;
    logoutButton.hidden = !authenticated;
}

async function refreshAccount() {
    const response = await fetch('/api/me');
    if (response.ok) {
        updateAccount(await response.json());
    } else {
        updateAccount({authenticated: false});
    }
}

logoutButton.addEventListener('click', async () => {
    await fetch('/api/logout', {method: 'POST'});
    window.location.href = '/login';
});

window.refreshAccount = refreshAccount;
refreshAccount();