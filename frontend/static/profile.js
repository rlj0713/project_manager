const profileForm = document.getElementById('profile-form');
const profileMessage = document.getElementById('profile-message');
const profileOwner = document.getElementById('profile-owner');
const profileUsername = profileForm.dataset.username;
const deleteUserButton = document.getElementById('delete-user-button');
const deleteMessage = document.getElementById('delete-message');

function setProfileFields(profile) {
    profileForm.first_name.value = profile.first_name;
    profileForm.last_name.value = profile.last_name;
    profileForm.email.value = profile.email;
    profileForm.start_date.value = profile.start_date;
    profileForm.title.value = profile.title;
    profileForm.pay_rate.value = profile.pay_rate;
    profileOwner.textContent = `Profile for ${profile.username}`;
}

async function loadProfile() {
    const response = await fetch(`/api/profile/${encodeURIComponent(profileUsername)}`);
    const data = await response.json();
    if (!response.ok) {
        profileMessage.textContent = data.message;
        return;
    }
    setProfileFields(data.profile);
}

profileForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const response = await fetch(`/api/profile/${encodeURIComponent(profileUsername)}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            first_name: profileForm.first_name.value,
            last_name: profileForm.last_name.value,
            email: profileForm.email.value,
            start_date: profileForm.start_date.value,
            title: profileForm.title.value,
            pay_rate: profileForm.pay_rate.value,
        }),
    });
    const data = await response.json();
    profileMessage.textContent = data.message;
    if (response.ok) setProfileFields(data.profile);
});

if (deleteUserButton) {
    deleteUserButton.addEventListener('click', async () => {
        if (!window.confirm(`Delete ${profileUsername}?`)) return;
        const response = await fetch(
            `/api/admin/users/${encodeURIComponent(profileUsername)}`,
            {method: 'DELETE'},
        );
        const data = await response.json();
        deleteMessage.textContent = data.message;
        if (response.ok) window.location.href = '/admin';
    });
}

loadProfile();