document.getElementById('logout-button').addEventListener('click', async () => {
    await fetch('/api/logout', {method: 'POST'});
    window.location.href = '/login';
});