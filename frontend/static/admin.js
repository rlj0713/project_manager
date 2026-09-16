const createUserForm = document.getElementById('create-user-form');
const adminMessage = document.getElementById('admin-message');
const userList = document.getElementById('user-list');
const logoutButton = document.getElementById('logout-button');
const logoutMessage = document.getElementById('logout-message');

logoutButton.addEventListener('click', async () => {
    const response = await fetch('/api/logout', {method: 'POST'});
    const data = await response.json();
    logoutMessage.textContent = data.message;
    if (response.ok) window.location.href = '/';
});

async function loadUsers() {
    const response = await fetch('/api/admin/users');
    if (!response.ok) {
        adminMessage.textContent = 'Unable to load users.';
        return;
    }

    const data = await response.json();
    userList.replaceChildren();
    data.users.forEach((user) => {
        const item = document.createElement('li');
        item.textContent = user.username;
        const editButton = document.createElement('button');
        editButton.textContent = 'Edit';
        editButton.addEventListener('click', () => editUser(user.username));
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.addEventListener('click', () => deleteUser(user.username));
        item.append(' ', editButton, ' ', deleteButton);
        userList.appendChild(item);
    });
}

createUserForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const response = await fetch('/api/admin/users', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: createUserForm.username.value,
            password: createUserForm.password.value,
        }),
    });
    const data = await response.json();
    adminMessage.textContent = data.message;
    if (response.ok) {
        createUserForm.reset();
        loadUsers();
    }
});

async function editUser(username) {
    const newUsername = window.prompt('New username:', username);
    if (!newUsername) return;
    const password = window.prompt('New password (optional):', '');
    const response = await fetch(`/api/admin/users/${encodeURIComponent(username)}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: newUsername, password}),
    });
    const data = await response.json();
    adminMessage.textContent = data.message;
    if (response.ok) loadUsers();
}

async function deleteUser(username) {
    if (!window.confirm(`Delete ${username}?`)) return;
    const response = await fetch(`/api/admin/users/${encodeURIComponent(username)}`, {
        method: 'DELETE',
    });
    const data = await response.json();
    adminMessage.textContent = data.message;
    if (response.ok) loadUsers();
}

loadUsers();