const timeline = document.getElementById('timeline');
const timelineScroll = document.getElementById('timeline-scroll');
const timelineStatus = document.getElementById('timeline-status');
const zoomControl = document.getElementById('timeline-zoom');
const dayMilliseconds = 24 * 60 * 60 * 1000;
const projectColors = ['#217c78', '#b56a2c', '#8b4f6f', '#4b6b9a'];
const isAdmin = document.querySelector('.home-page').dataset.admin === 'true';
const timelinePaddingDays = 14;

let projectData = [];
let timelineStart;
let timelineEnd;

function parseDate(date) {
    return new Date(`${date}T00:00:00`);
}

function dayOffset(date) {
    return Math.round((parseDate(date) - timelineStart) / dayMilliseconds);
}

function dayCount(start, end) {
    return Math.max(1, Math.round((parseDate(end) - parseDate(start)) / dayMilliseconds) + 1);
}

function formatDate(date) {
    return date.toLocaleDateString(undefined, {month: 'short', day: 'numeric'});
}

function shiftDate(dateString, days) {
    const date = parseDate(dateString);
    date.setDate(date.getDate() + days);
    return date.toISOString().slice(0, 10);
}

function updateBar(task, type) {
    const bar = document.querySelector(
        `[data-task-id="${task.id}"][data-bar-type="${type}"]`,
    );
    if (!bar) return;
    const start = type === 'budget' ? task.start_date : task.actual_start_date;
    const end = type === 'budget' ? task.end_date : task.actual_end_date;
    const dayWidth = Number(zoomControl.value);
    bar.style.left = `${dayOffset(start) * dayWidth}px`;
    bar.style.width = `${dayCount(start, end) * dayWidth}px`;
}

function updateProjectBudgetBar(project, budgetBar, previewTasks) {
    const taskDates = project.tasks.map((task) => previewTasks.get(task.id) || task);
    const startDate = taskDates.reduce(
        (earliest, task) => task.start_date < earliest ? task.start_date : earliest,
        taskDates[0].start_date,
    );
    const endDate = taskDates.reduce(
        (latest, task) => task.end_date > latest ? task.end_date : latest,
        taskDates[0].end_date,
    );
    project.start_date = startDate;
    project.end_date = endDate;
    const dayWidth = Number(zoomControl.value);
    budgetBar.style.left = `${dayOffset(startDate) * dayWidth}px`;
    budgetBar.style.width = `${dayCount(startDate, endDate) * dayWidth}px`;
}

function createResizeHandle(task, bar, edge, dates, adjacentTask, project, budgetBar) {
    if (!isAdmin) return;
    const adjacentDates = adjacentTask && (
        dates.type === 'budget' ||
        (adjacentTask.actual_start_date && adjacentTask.actual_end_date)
    )
        ? {
            type: dates.type,
            start: dates.type === 'budget' ? adjacentTask.start_date : adjacentTask.actual_start_date,
            end: dates.type === 'budget' ? adjacentTask.end_date : adjacentTask.actual_end_date,
        }
        : null;
    const handle = document.createElement('button');
    handle.className = `resize-handle ${edge}`;
    handle.type = 'button';
    handle.title = `Drag to change ${dates.type} ${edge} date`;
    handle.addEventListener('pointerdown', (event) => {
        event.preventDefault();
        handle.setPointerCapture(event.pointerId);
        const startX = event.clientX;
        const originalStart = dates.start;
        const originalEnd = dates.end;
        const dayWidth = Number(zoomControl.value);

        function move(moveEvent) {
            const dayDelta = Math.round((moveEvent.clientX - startX) / dayWidth);
            if (edge === 'start') {
                dates.start = shiftDate(originalStart, dayDelta);
                if (dates.start > dates.end) dates.start = dates.end;
                if (adjacentDates && dates.start <= adjacentDates.start) {
                    dates.start = shiftDate(adjacentDates.start, 1);
                }
                if (adjacentDates) adjacentDates.end = shiftDate(dates.start, -1);
            } else {
                dates.end = shiftDate(originalEnd, dayDelta);
                if (dates.end < dates.start) dates.end = dates.start;
                if (adjacentDates && dates.end >= adjacentDates.end) {
                    dates.end = shiftDate(adjacentDates.end, -1);
                }
                if (adjacentDates) adjacentDates.start = shiftDate(dates.end, 1);
            }
            const currentTask = {...task};
            if (dates.type === 'budget') {
                currentTask.start_date = dates.start;
                currentTask.end_date = dates.end;
            } else {
                currentTask.actual_start_date = dates.start;
                currentTask.actual_end_date = dates.end;
            }
            let updatedAdjacent = null;
            updateBar(currentTask, dates.type);
            if (adjacentTask && adjacentDates) {
                updatedAdjacent = {...adjacentTask};
                if (dates.type === 'budget') {
                    updatedAdjacent.start_date = adjacentDates.start;
                    updatedAdjacent.end_date = adjacentDates.end;
                } else {
                    updatedAdjacent.actual_start_date = adjacentDates.start;
                    updatedAdjacent.actual_end_date = adjacentDates.end;
                }
                updateBar(updatedAdjacent, dates.type);
            }
            if (dates.type === 'budget') {
                const previewTasks = new Map([
                    [task.id, currentTask],
                    ...(adjacentTask && adjacentDates
                        ? [[adjacentTask.id, updatedAdjacent]]
                        : []),
                ]);
                updateProjectBudgetBar(project, budgetBar, previewTasks);
            }
        }

        async function finish() {
            handle.removeEventListener('pointermove', move);
            handle.removeEventListener('pointerup', finish);
            handle.releasePointerCapture(event.pointerId);
            if (dates.type === 'budget') {
                task.start_date = dates.start;
                task.end_date = dates.end;
            } else {
                task.actual_start_date = dates.start;
                task.actual_end_date = dates.end;
            }
            if (adjacentTask && adjacentDates) {
                if (dates.type === 'budget') {
                    adjacentTask.start_date = adjacentDates.start;
                    adjacentTask.end_date = adjacentDates.end;
                } else {
                    adjacentTask.actual_start_date = adjacentDates.start;
                    adjacentTask.actual_end_date = adjacentDates.end;
                }
            }
            await saveTaskDates(task, adjacentTask && adjacentDates ? adjacentTask : null);
        }

        handle.addEventListener('pointermove', move);
        handle.addEventListener('pointerup', finish, {once: true});
    });
    bar.appendChild(handle);
}

async function saveTaskDates(task, adjacentTask) {
    const tasks = [task, ...(adjacentTask ? [adjacentTask] : [])].map((item) => ({
        id: item.id,
        start_date: item.start_date,
        end_date: item.end_date,
        actual_start_date: item.actual_start_date || '',
        actual_end_date: item.actual_end_date || '',
    }));
    const response = await fetch(`/api/admin/tasks/${task.id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tasks}),
    });
    if (!response.ok) {
        await loadProjects();
        return;
    }
    await loadProjects();
}

function dateLabelInterval(dayWidth) {
    if (dayWidth >= 36) return 1;
    if (dayWidth >= 28) return 3;
    if (dayWidth >= 20) return 7;
    return 14;
}

function buildTimeline() {
    timeline.replaceChildren();
    const dayWidth = Number(zoomControl.value);
    const totalDays = dayCount(
        timelineStart.toISOString().slice(0, 10),
        timelineEnd.toISOString().slice(0, 10),
    );
    timeline.style.setProperty('--day-width', `${dayWidth}px`);
    timeline.style.setProperty('--timeline-width', `${totalDays * dayWidth}px`);
    const labelInterval = dateLabelInterval(dayWidth);

    const dateHeader = document.createElement('div');
    dateHeader.className = 'timeline-date-header';
    dateHeader.innerHTML = '<div class="project-label">Project</div>';
    const dates = document.createElement('div');
    dates.className = 'date-track';
    for (let index = 0; index < totalDays; index += 1) {
        const date = new Date(timelineStart.getTime() + index * dayMilliseconds);
        const label = document.createElement('span');
        label.textContent = index % labelInterval === 0 ? formatDate(date) : '';
        dates.appendChild(label);
    }
    dateHeader.appendChild(dates);
    timeline.appendChild(dateHeader);

    projectData.forEach((project, projectIndex) => {
        const row = document.createElement('div');
        row.className = 'project-row';
        row.style.setProperty('--project-color', projectColors[projectIndex % projectColors.length]);

        const label = document.createElement('div');
        label.className = 'project-label';
        const projectTitle = document.createElement(isAdmin ? 'a' : 'strong');
        projectTitle.textContent = project.name;
        if (isAdmin) projectTitle.href = `/admin/projects/${project.id}/edit`;
        label.appendChild(projectTitle);
        const dates = document.createElement('small');
        dates.textContent = `${project.start_date} to ${project.end_date}`;
        label.appendChild(dates);
        row.appendChild(label);

        const track = document.createElement('div');
        track.className = 'project-track';
        const budgetBar = document.createElement('div');
        budgetBar.className = 'project-budget-bar';
        budgetBar.style.left = `${dayOffset(project.start_date) * dayWidth}px`;
        budgetBar.style.width = `${dayCount(project.start_date, project.end_date) * dayWidth}px`;
        budgetBar.title = `Budgeted project: ${project.start_date} to ${project.end_date}`;
        track.appendChild(budgetBar);

            project.tasks.forEach((task, taskIndex) => {
                const previousTask = project.tasks[taskIndex - 1];
                const nextTask = project.tasks[taskIndex + 1];
            const budgetTask = document.createElement('div');
            budgetTask.className = 'budget-task-marker';
                budgetTask.dataset.taskId = task.id;
                budgetTask.dataset.barType = 'budget';
            budgetTask.style.left = `${dayOffset(task.start_date) * dayWidth}px`;
            budgetTask.style.width = `${dayCount(task.start_date, task.end_date) * dayWidth}px`;
            budgetTask.title = taskDetails(task, 'Budgeted');
            budgetTask.textContent = task.title;
            createResizeHandle(task, budgetTask, 'start', {
                type: 'budget',
                start: task.start_date,
                end: task.end_date,
            }, previousTask, project, budgetBar);
            createResizeHandle(task, budgetTask, 'end', {
                type: 'budget',
                start: task.start_date,
                end: task.end_date,
            }, nextTask, project, budgetBar);
            track.appendChild(budgetTask);

            if (task.actual_start_date && task.actual_end_date) {
                const actualBar = document.createElement('div');
            actualBar.className = `task-bar actual-bar ${task.completed ? 'completed' : 'incomplete'}`;
                actualBar.dataset.taskId = task.id;
                actualBar.dataset.barType = 'actual';
                actualBar.style.left = `${dayOffset(task.actual_start_date) * dayWidth}px`;
                actualBar.style.width = `${dayCount(task.actual_start_date, task.actual_end_date) * dayWidth}px`;
                actualBar.title = taskDetails(task, 'Actual');
                actualBar.textContent = `Actual: ${task.title}`;
                createResizeHandle(task, actualBar, 'start', {
                    type: 'actual',
                    start: task.actual_start_date,
                    end: task.actual_end_date,
                }, previousTask, project, budgetBar);
                createResizeHandle(task, actualBar, 'end', {
                    type: 'actual',
                    start: task.actual_start_date,
                    end: task.actual_end_date,
                }, nextTask, project, budgetBar);
                track.appendChild(actualBar);
            }
        });
        row.appendChild(track);
        timeline.appendChild(row);
    });
}

function taskDetails(task, dateType) {
    const actualDates = task.actual_start_date && task.actual_end_date
        ? `\nActual: ${task.actual_start_date} to ${task.actual_end_date}`
        : '\nActual dates: Not recorded';
    return [
        task.title,
        `Budgeted: ${task.start_date} to ${task.end_date}`,
        `Labor: ${task.labor_hours} hours`,
        `Materials: $${Number(task.material_cost).toFixed(2)}`,
        `Subcontractor: $${Number(task.subcontractor_cost).toFixed(2)}`,
        `Status: ${task.completed ? 'Complete' : 'In progress'}`,
        dateType === 'Actual' ? actualDates.trim() : actualDates.trim(),
    ].join('\n');
}

async function loadProjects() {
    const response = await fetch('/api/projects');
    if (!response.ok) {
        timelineStatus.textContent = 'Unable to load projects.';
        return;
    }
    const data = await response.json();
    projectData = data.projects;
    if (!projectData.length) {
        timelineStatus.textContent = 'No projects yet.';
        return;
    }

    const dates = projectData.flatMap((project) => [
        project.start_date,
        project.end_date,
        ...project.tasks.flatMap((task) => [
            task.start_date,
            task.end_date,
            ...(task.actual_start_date && task.actual_end_date
                ? [task.actual_start_date, task.actual_end_date]
                : []),
        ]),
    ]).map(parseDate);
    timelineStart = new Date(Math.min(...dates) - timelinePaddingDays * dayMilliseconds);
    timelineEnd = new Date(Math.max(...dates) + timelinePaddingDays * dayMilliseconds);
    timelineStatus.hidden = true;
    timelineScroll.hidden = false;
    buildTimeline();
}

zoomControl.addEventListener('input', buildTimeline);
window.refreshProjects = loadProjects;
loadProjects();