// Student Dashboard JavaScript

function loadMyProjects() {
    const container = document.querySelector('#my-projects .projects-container');
    if (!container) return;
    fetch('/api/student/projects')
        .then(response => response.json())
        .then(projects => {
            container.innerHTML = '';
            if (projects.length === 0) {
                container.innerHTML = '<p>You have not joined or created any projects yet.</p>';
                return;
            }
            projects.forEach(project => {
                const statusClass = `status-${project.status.toLowerCase().replace(' ', '-')}`;
                const projectCard = `
                    <div class="project-card">
                        <h3>${project.title}</h3>
                        <p>Department: ${project.department}</p>
                        <p>Faculty: ${project.faculty_name}</p>
                        ${project.submission_date ? `<p><strong>Deadline:</strong> ${project.submission_date}</p>` : ''}
                        
                        <div class="project-progress">
                            <div class="progress-bar">
                                <div class="progress" style="width: ${project.progress_percentage}%"></div>
                            </div>
                            <span>${project.progress_percentage}% Complete</span>
                        </div>

                        <div class="project-status ${statusClass}">${project.status.replace('_', ' ')}</div>
                        <div class="project-actions">
                            <button class="btn btn-small view-details-btn" data-project-id="${project.id}">View Details</button>
                        </div>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', projectCard);
            });
        });
}

function openDetailsModal(projectId) {
    const modal = document.getElementById('viewDetailsModal');
    fetch(`/api/project/${projectId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) { alert(data.message); return; }
            const project = data.project;
            document.getElementById('details-title').textContent = project.title;
            document.getElementById('details-department').textContent = project.department;
            document.getElementById('details-faculty').textContent = project.faculty_name;
            document.getElementById('details-status').textContent = project.status;
            document.getElementById('details-description').textContent = project.description;
            
            const taskList = document.getElementById('details-task-list');
            taskList.innerHTML = '';
            if (data.tasks.length > 0) {
                data.tasks.forEach(task => {
                    let actionButton = '';
            // CORRECTED: Allow submission for 'assigned' or 'rejected' tasks
            if (task.status === 'assigned' || task.status === 'rejected') {
                const buttonText = task.status === 'rejected' ? 'Resubmit Work' : 'Submit Work';
                actionButton = `<button class="btn btn-primary btn-small submit-work-btn" data-task-id="${task.id}" data-task-title="${task.title}">${buttonText}</button>`;
            }
                    const taskItem = document.createElement('div');
                    taskItem.className = 'task-item';
                    taskItem.innerHTML = `
                        <p><strong>${task.title}</strong> (${task.percentage_value}%) - <span class="status-${task.status}">${task.status.replace('_', ' ')}</span></p>
                        <p>${task.description}</p>
                        <div class="task-actions">${actionButton}</div>
                    `;
                    taskList.appendChild(taskItem);
                });
            } else {
                taskList.innerHTML = '<p>No milestones assigned for this project yet.</p>';
            }
            modal.style.display = 'block';
        });
}

let studentChart = null; // To hold the chart instance

function loadDashboardStats() {
    fetch('/api/student/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-projects').textContent = data.total_projects;
            document.getElementById('ongoing-projects').textContent = data.ongoing_projects;
            document.getElementById('completed-projects').textContent = data.completed_projects;

            const ctx = document.getElementById('studentProjectChart').getContext('2d');

            // Destroy previous chart instance if it exists
            if (studentChart) {
                studentChart.destroy();
            }

            studentChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['Ongoing Projects', 'Completed Projects'],
                    datasets: [{
                        label: 'Project Status',
                        data: [data.ongoing_projects, data.completed_projects],
                        backgroundColor: [
                            '#0b7a6b',
                            '#3ddbc4'
                        ],
                        borderColor: [
                            '#0b7a6b',
                            '#3ddbc4'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Approved Projects Distribution'
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error loading dashboard stats:', error));
}

function loadFeedback() {
    const container = document.querySelector('#feedback .feedback-container');
    fetch('/api/student/feedback')
        .then(response => response.json())
        .then(feedbacks => {
            container.innerHTML = '';
            if (feedbacks.length === 0) { container.innerHTML = '<p>No feedback received yet.</p>'; return; }
            feedbacks.forEach(fb => {
                const feedbackCard = `
                    <div class="feedback-card">
                        <h4>${fb.project_title}</h4>
                        <p class="feedback-text">"${fb.feedback_text}"</p>
                        <p class="feedback-meta">From: ${fb.faculty_name} | Date: ${new Date(fb.created_at).toLocaleDateString()}</p>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', feedbackCard);
            });
        });
}

let deadlines = [];

function renderCalendar(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    document.getElementById('currentMonth').textContent = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const calendarGrid = document.querySelector('.calendar-grid');
    calendarGrid.innerHTML = '';

    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => {
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        dayEl.textContent = day;
        calendarGrid.appendChild(dayEl);
    });

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    for (let i = 0; i < firstDay.getDay(); i++) {
        calendarGrid.insertAdjacentHTML('beforeend', '<div class="calendar-date"></div>');
    }

    for (let day = 1; day <= lastDay.getDate(); day++) {
        const dateEl = document.createElement('div');
        dateEl.className = 'calendar-date';
        dateEl.textContent = day;
        const today = new Date();
        if (day === today.getDate() && month === today.getMonth() && year === today.getFullYear()) {
            dateEl.classList.add('today');
        }
        const currentDayStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayDeadlines = deadlines.filter(d => d.submission_date === currentDayStr);
        if (dayDeadlines.length > 0) {
            dateEl.classList.add('has-deadline');
            dateEl.title = dayDeadlines.map(d => d.title).join('\n');
        }
        calendarGrid.appendChild(dateEl);
    }
}

function fetchAndRenderCalendar(date) {
    fetch('/api/student/calendar-deadlines')
        .then(response => response.json())
        .then(data => {
            deadlines = data;
            renderCalendar(date);
            const deadlinesList = document.querySelector('.deadlines-list ul');
            deadlinesList.innerHTML = '';
            if (deadlines.length > 0) {
                deadlines.sort((a, b) => new Date(a.submission_date) - new Date(b.submission_date));
                deadlines.forEach(deadline => {
                    const li = document.createElement('li');
                    li.textContent = `${deadline.title}: ${deadline.submission_date}`;
                    deadlinesList.appendChild(li);
                });
            } else {
                deadlinesList.innerHTML = '<li>No upcoming deadlines.</li>';
            }
        });
}

function loadProfileData() {
    fetch('/api/student/profile')
        .then(response => response.json())
        .then(data => {
            document.getElementById('profile-name').textContent = data.profile.name;
            document.getElementById('profile-reg-no').textContent = `Registration No: ${data.profile.roll_no}`;
            document.getElementById('profile-department').textContent = `Department: ${data.profile.specialization}`;
            document.getElementById('profile-email').textContent = `Email: ${data.profile.email}`;
            const projectList = document.getElementById('profile-project-list');
            projectList.innerHTML = '';
            if (data.projects && data.projects.length > 0) {
                data.projects.forEach(project => {
                    const li = document.createElement('li');
                    li.textContent = `${project.title} (${project.status})`;
                    projectList.appendChild(li);
                });
            } else {
                projectList.innerHTML = '<li>No projects found.</li>';
            }
        });
}

document.addEventListener('DOMContentLoaded', function() {
    const addProjectModal = document.getElementById('addProjectModal');
    const submitWorkModal = document.getElementById('submitWorkModal');
    
    // Navigation
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active')); // Make sure all pages are hidden first
            this.classList.add('active');
            const pageId = this.dataset.page;
            document.getElementById(pageId).classList.add('active');
            
            // --- Enhancement: Update Page Title ---
            const pageTitleMap = {
                'dashboard': 'Student Dashboard',
                'my-projects': 'My Projects',
                'feedback': 'Feedback',
                'calendar': 'Calendar',
                'profile': 'Profile'
            };
            const pageTitleElement = document.getElementById('page-title');
            if (pageTitleElement) {
                pageTitleElement.textContent = pageTitleMap[pageId] || 'Student Portal';
            }
            // --------------------------------------

            if (pageId === 'dashboard') { loadDashboardStats(); } // <-- THIS LINE IS ADDED
            if (pageId === 'my-projects') { loadMyProjects(); }
            if (pageId === 'profile') { loadProfileData(); }
            if (pageId === 'calendar') { fetchAndRenderCalendar(new Date()); }
            if (pageId === 'feedback') { loadFeedback(); }
        });
    });

    // --- FIX: Event Delegation listener moved to 'document' ---
    document.addEventListener('click', function(e) {
        // For buttons inside 'My Projects' page
        if (e.target.closest('.projects-container') && e.target.classList.contains('view-details-btn')) {
            openDetailsModal(e.target.dataset.projectId);
        }
        // For buttons inside 'View Details' modal
        if (e.target.closest('#details-task-list') && e.target.classList.contains('submit-work-btn')) {
            const taskId = e.target.dataset.taskId;
            const taskTitle = e.target.dataset.taskTitle;
            document.getElementById('submissionTaskId').value = taskId;
            document.getElementById('submissionTaskTitle').textContent = taskTitle;
            submitWorkModal.style.display = 'block';
        }
    });

    document.getElementById('addProjectBtn')?.addEventListener('click', () => addProjectModal.style.display = 'block');

    // Form Submissions
    document.getElementById('addProjectForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = {
            title: document.getElementById('projectTitle').value,
            description: document.getElementById('projectDescription').value,
            department: document.getElementById('projectDepartment').value,
            faculty: document.getElementById('projectFaculty').value,
            teamMembers: document.getElementById('teamMembers').value
        };
        fetch('/api/student/projects', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert('Project created successfully!');
                addProjectModal.style.display = 'none';
                this.reset();
                loadMyProjects();
            } else { alert('Error: ' + data.message); }
        });
    });

    document.getElementById('submitWorkForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const taskId = document.getElementById('submissionTaskId').value;
        const formData = new FormData();
        formData.append('progress_description', document.getElementById('submissionProgress').value);
        const file = document.getElementById('submissionFile').files[0];
        if (file) { formData.append('submissionFile', file); }
        fetch(`/api/student/task/${taskId}/submit`, {
            method: 'POST',
            body: formData
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert(data.message);
                submitWorkModal.style.display = 'none';
                this.reset();
                const openProjectId = document.querySelector('.view-details-btn[data-project-id]')?.dataset.projectId;
                if(document.getElementById('viewDetailsModal').style.display === 'block') {
                    const titleElement = document.getElementById('details-title');
                    // Find the project card that has this title to get the project ID
                    // This is a bit complex, a better way would be storing the current project ID globally
                    // For now, let's just close and tell user to reopen. A better solution is possible.
                    document.getElementById('viewDetailsModal').style.display = 'none';
                    alert("Please reopen 'View Details' to see the updated task status.");
                }
            } else { alert('Error: ' + data.message); }
        });
    });

    // Generic Modal Close Logic
    document.querySelectorAll('.modal .close, .modal .cancel-btn').forEach(el => {
        el.addEventListener('click', () => el.closest('.modal').style.display = 'none');
    });
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) e.target.style.display = 'none';
    });

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        if (confirm('Are you sure you want to logout?')) {
            fetch('/api/logout', { method: 'POST' }).then(() => window.location.href = '/login');
        }
    });
    
    // Calendar Controls
    let calendarDate = new Date();
    document.getElementById('prevMonth')?.addEventListener('click', () => {
        calendarDate.setMonth(calendarDate.getMonth() - 1);
        fetchAndRenderCalendar(calendarDate);
    });
    document.getElementById('nextMonth')?.addEventListener('click', () => {
        calendarDate.setMonth(calendarDate.getMonth() + 1);
        fetchAndRenderCalendar(calendarDate);
    });
    loadDashboardStats();
});