const projectDialog = document.getElementById('project-dialog');
const projectForm = document.getElementById('project-form');
const taskFields = document.getElementById('task-fields');
const projectMessage = document.getElementById('project-message');

function addTaskFields() {
    const task = document.createElement('fieldset');
    task.className = 'task-fields';
    task.innerHTML = `
        <legend>Task</legend>
        <input name="title" placeholder="Task name" required>
        <label>Start date <input name="start_date" type="date" required></label>
        <label>Target end date <input name="end_date" type="date" required></label>
        <label>Budgeted labor hours <input name="labor_hours" type="number" min="0" step="0.25" required></label>
        <label>Budgeted material costs <input name="material_cost" type="number" min="0" step="0.01" required></label>
        <label>Budgeted subcontractor costs <input name="subcontractor_cost" type="number" min="0" step="0.01" required></label>
    `;
    taskFields.appendChild(task);
}

function collectTasks() {
    return [...taskFields.querySelectorAll('.task-fields')].map((task) => ({
        title: task.querySelector('[name="title"]').value,
        start_date: task.querySelector('[name="start_date"]').value,
        end_date: task.querySelector('[name="end_date"]').value,
        labor_hours: task.querySelector('[name="labor_hours"]').value,
        material_cost: task.querySelector('[name="material_cost"]').value,
        subcontractor_cost: task.querySelector('[name="subcontractor_cost"]').value,
    }));
}

document.getElementById('create-project-button').addEventListener('click', () => {
    projectDialog.showModal();
});

document.getElementById('close-project-button').addEventListener('click', () => {
    projectDialog.close();
});

document.getElementById('add-task-button').addEventListener('click', addTaskFields);

projectForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    projectMessage.textContent = 'Creating project...';
    const name = document.getElementById('project-name').value.trim();
    const startDate = document.getElementById('project-start-date').value;
    const tasks = collectTasks();
    if (!name || !startDate || !tasks.length) {
        projectMessage.textContent = 'Project name, start date, and at least one task are required.';
        return;
    }
    try {
        const response = await fetch('/api/admin/projects', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name,
                start_date: startDate,
                tasks,
            }),
        });
        const data = await response.json();
        if (!response.ok) {
            projectMessage.textContent = data.message;
            return;
        }

        projectDialog.close();
        projectForm.reset();
        taskFields.replaceChildren();
        addTaskFields();
        await window.refreshProjects();
    } catch (error) {
        projectMessage.textContent = 'Unable to create project.';
    }
});

addTaskFields();