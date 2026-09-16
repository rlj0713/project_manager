const timeline = document.getElementById('timeline');
const timelineScroll = document.getElementById('timeline-scroll');
const timelineStatus = document.getElementById('timeline-status');
const zoomControl = document.getElementById('timeline-zoom');
const dayMilliseconds = 24 * 60 * 60 * 1000;
const projectColors = ['#217c78', '#b56a2c', '#8b4f6f', '#4b6b9a'];

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

function buildTimeline() {
    timeline.replaceChildren();
    const dayWidth = Number(zoomControl.value);
    const totalDays = dayCount(
        timelineStart.toISOString().slice(0, 10),
        timelineEnd.toISOString().slice(0, 10),
    );
    timeline.style.setProperty('--day-width', `${dayWidth}px`);
    timeline.style.setProperty('--timeline-width', `${totalDays * dayWidth}px`);

    const dateHeader = document.createElement('div');
    dateHeader.className = 'timeline-date-header';
    dateHeader.innerHTML = '<div class="project-label">Project</div>';
    const dates = document.createElement('div');
    dates.className = 'date-track';
    for (let index = 0; index < totalDays; index += 1) {
        const date = new Date(timelineStart.getTime() + index * dayMilliseconds);
        const label = document.createElement('span');
        label.textContent = index % 7 === 0 ? formatDate(date) : '';
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
        label.innerHTML = `<strong>${project.name}</strong><small>${project.start_date} to ${project.end_date}</small>`;
        row.appendChild(label);

        const track = document.createElement('div');
        track.className = 'project-track';
        project.tasks.forEach((task) => {
            const taskBar = document.createElement('div');
            taskBar.className = `task-bar ${task.completed ? 'completed' : 'incomplete'}`;
            taskBar.style.left = `${dayOffset(task.start_date) * dayWidth}px`;
            taskBar.style.width = `${dayCount(task.start_date, task.end_date) * dayWidth}px`;
            taskBar.title = `${task.title}: ${task.start_date} to ${task.end_date}`;
            taskBar.textContent = task.title;
            track.appendChild(taskBar);
        });
        row.appendChild(track);
        timeline.appendChild(row);
    });
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
        ...project.tasks.flatMap((task) => [task.start_date, task.end_date]),
    ]).map(parseDate);
    timelineStart = new Date(Math.min(...dates));
    timelineEnd = new Date(Math.max(...dates));
    timelineStatus.hidden = true;
    timelineScroll.hidden = false;
    buildTimeline();
}

zoomControl.addEventListener('input', buildTimeline);
window.refreshProjects = loadProjects;
loadProjects();