const editProjectForm = document.getElementById('edit-project-form');
const editProjectMessage = document.getElementById('edit-project-message');
const projectId = editProjectForm.dataset.projectId;

function collectTasks() {
    return [...document.querySelectorAll('.edit-task')].map((task) => ({
        id: task.dataset.taskId,
        actual_start_date: task.querySelector('[name="actual_start_date"]').value,
        actual_end_date: task.querySelector('[name="actual_end_date"]').value,
    }));
}

editProjectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const response = await fetch(`/api/admin/projects/${projectId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            name: editProjectForm.elements.namedItem('name').value.trim(),
            start_date: editProjectForm.elements.namedItem('start_date').value,
            end_date: editProjectForm.elements.namedItem('end_date').value,
            tasks: collectTasks(),
        }),
    });
    const data = await response.json();
    editProjectMessage.textContent = data.message;
    if (response.ok) window.location.href = '/';
});