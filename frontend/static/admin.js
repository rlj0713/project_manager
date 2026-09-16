const createUserForm = document.getElementById('create-user-form');
const adminMessage = document.getElementById('admin-message');
const userList = document.getElementById('user-list');

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
        item.append(user.username, user.is_admin ? ' (admin) ' : ' ');
        const profileLink = document.createElement('a');
        profileLink.href = `/profile?username=${encodeURIComponent(user.username)}`;
        profileLink.textContent = 'Edit profile';
        item.append(profileLink);
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

loadUsers();