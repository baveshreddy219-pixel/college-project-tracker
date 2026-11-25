// Faculty Dashboard JavaScript

function loadFacultyMyProjects() {
    const container = document.querySelector('#my-projects .projects-container');
    fetch('/api/faculty/my-projects')
        .then(response => response.json())
        .then(projects => {
            container.innerHTML = '';
            if (projects.length === 0) {
                container.innerHTML = '<p>No projects are assigned to you yet.</p>';
                return;
            }
            projects.forEach(project => {
                // Default action is to just view details
                let actionsHtml = `<button class="btn btn-secondary btn-small view-details-btn-faculty" data-project-id="${project.id}">View Details</button>`;
                
                let projectDetailsHtml = '';

                // Only show detailed info for 'approved' projects
                if (project.status === 'approved') {
                    let tasksHtml = '<p>No pending tasks for approval.</p>';
                    if (project.pending_tasks.length > 0) {
                        tasksHtml = project.pending_tasks.map(task => `
                            <div class="task-item" id="task-${task.id}">
                                <p><strong>${task.title}</strong></p>
                                <p>${task.progress_description}</p>
                                ${task.file_path ? `<a href="/uploads/${task.file_path}" target="_blank">View Attached File</a>` : ''}
                                <div class="task-actions">
                                    <button class="btn btn-small btn-success" onclick="handleTaskAction(${task.id}, 'approved')">Approve</button>
                                    <button class="btn btn-small btn-danger" onclick="handleTaskAction(${task.id}, 'rejected')">Reject</button>
                                </div>
                            </div>
                        `).join('');
                    }
                    
                    // Add the "Add Milestone" button only for approved projects
                    actionsHtml = `
                        <button class="btn btn-primary btn-small add-milestone-btn" data-project-id="${project.id}">Add Milestone</button>
                        ${actionsHtml}
                    `;
                    
                    projectDetailsHtml = `
                        ${project.submission_date ? `<p><strong>Deadline:</strong> ${project.submission_date}</p>` : ''}
                        <div class="project-progress">
                            <div class="progress-bar">
                                <div class="progress" style="width: ${project.progress_percentage}%"></div>
                            </div>
                            <span>${project.progress_percentage}% Complete</span>
                        </div>
                        <div class="pending-tasks">
                            <h4>Pending Tasks for Approval</h4>
                            ${tasksHtml}
                        </div>
                    `;
                } else {
                     projectDetailsHtml = `<p>This project was rejected and is inactive.</p>`;
                }


                const projectCard = `
                    <div class="project-card">
                        <h3>${project.title}</h3>
                        <p><strong>Status:</strong> ${project.status}</p>
                        ${projectDetailsHtml}
                        <div class="project-actions">
                           ${actionsHtml}
                        </div>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', projectCard);
            });
        });
}

// In faculty.js

function openFacultyDetailsModal(projectId) {
    const modal = document.getElementById('facultyViewDetailsModal');
    fetch(`/api/project/${projectId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.success) { alert(data.message); return; }
            const project = data.project;

            // Populate project details
            document.getElementById('details-title-faculty').textContent = project.title;
            document.getElementById('details-department-faculty').textContent = project.department;
            document.getElementById('details-status-faculty').textContent = project.status;
            document.getElementById('details-description-faculty').textContent = project.description;
            
            // FIX: Use the specific modal ID to target the deadline elements
            document.getElementById('details-deadline-faculty').textContent = project.submission_date || 'Not Set';
            
            // THE CRITICAL FIX: Ensure the button is targeted correctly within the modal
            const changeDeadlineBtn = document.querySelector('#facultyViewDetailsModal .change-deadline-btn');
            if (changeDeadlineBtn) {
                changeDeadlineBtn.dataset.projectId = project.id; 
            }

            // Populate team members
            const memberList = document.getElementById('details-members-list-faculty');
            memberList.innerHTML = '';
            if (data.members.length > 0) {
                data.members.forEach(member => {
                    const li = document.createElement('li');
                    li.textContent = `${member.name} (${member.roll_no})`;
                    memberList.appendChild(li);
                });
            } else {
                memberList.innerHTML = '<li>No members found.</li>';
            }

            // Populate all tasks
            const taskList = document.getElementById('details-task-list-faculty');
            taskList.innerHTML = '';
            if (data.tasks.length > 0) {
                data.tasks.forEach(task => {
                    const submittedBy = task.student_name ? `(Submitted by: ${task.student_name})` : '';
                    const taskItem = document.createElement('div');
                    taskItem.className = 'task-item';
                    taskItem.innerHTML = `
                        <p><strong>${task.title}</strong> - <span class="status-${task.status}">${task.status.replace('_', ' ')}</span> ${submittedBy}</p>
                        <p>${task.description}</p>
                    `;
                    taskList.appendChild(taskItem);
                });
            } else {
                taskList.innerHTML = '<p>No milestones have been assigned to this project yet.</p>';
            }

            modal.style.display = 'block';
        });
}

function handleTaskAction(taskId, action) {
    if (action === 'approved') {
        // Approval can happen directly
        fetch(`/api/faculty/task/${taskId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: action })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Task ${action} successfully!`);
                loadFacultyMyProjects();
            } else {
                alert('Error: ' + data.message);
            }
        });
    } else if (action === 'rejected') {
        // For rejection, open the remarks modal first
        document.getElementById('remarksTaskId').value = taskId;
        document.getElementById('taskRemarksModal').style.display = 'block';
    }
}

// Faculty Dashboard JavaScript

let facultyChart = null; // To hold the chart instance

function loadFacultyDashboardStats() {
    fetch('/api/faculty/dashboard-stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('faculty-total-projects').textContent = data.total_projects;
            document.getElementById('faculty-ongoing-projects').textContent = data.ongoing_projects;
            document.getElementById('faculty-completed-projects').textContent = data.completed_projects;

            const ctx = document.getElementById('facultyProjectChart').getContext('2d');

            // Destroy the old chart instance before creating a new one
            if (facultyChart) {
                facultyChart.destroy();
            }

            facultyChart = new Chart(ctx, {
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
                        legend: { position: 'top' },
                        title: {
                            display: true,
                            text: 'Supervised Projects Distribution'
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error loading faculty dashboard stats:', error));
}

// --- NEW FUNCTION TO LOAD PROFILE DATA ---
function loadFacultyProfileData() {
    fetch('/api/faculty/profile')
        .then(response => response.json())
        .then(data => {
            // Get the placeholder elements
            const profileDetails = document.querySelector('#profile .profile-details');
            const profileProjectsList = document.querySelector('#profile .profile-projects ul');
            
            // Clear existing content (from the initial empty HTML tags)
            profileDetails.innerHTML = '';
            profileProjectsList.innerHTML = '';

            // Populate profile details
            const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
            profileDetails.innerHTML = `
                <h3 id="profile-name-faculty">${esc(data.profile.name)}</h3>
                <p id="profile-email-faculty">Email: ${esc(data.profile.email)}</p>
                <p id="profile-dept-faculty">Department: ${esc(data.profile.department)}</p>
            `;

            // Populate supervised projects
            if (data.projects && data.projects.length > 0) {
                data.projects.forEach(project => {
                    const li = document.createElement('li');
                    li.textContent = `${project.title} (${project.status})`;
                    profileProjectsList.appendChild(li);
                });
            } else {
                profileProjectsList.innerHTML = '<li>No projects currently supervising.</li>';
            }
        })
        .catch(error => console.error('Error loading faculty profile:', error));
}
// -----------------------------------------

function loadProjectRequests() {
    const container = document.querySelector('#project-requests .requests-container');
    fetch('/api/faculty/project-requests')
        .then(response => response.json())
        .then(requests => {
            container.innerHTML = '';
            if (requests.length === 0) {
                container.innerHTML = '<p>There are no new project requests.</p>';
                return;
            }
            requests.forEach(req => {
                const requestCard = `
                    <div class="request-card" id="request-${req.id}">
                        <h3>${req.title}</h3>
                        <p><strong>Team:</strong> ${req.team_members}</p>
                        <p><strong>Description:</strong> ${req.description}</p>
                        <div class="request-actions">
                            <button class="btn btn-success approve-btn" data-project="${req.id}">Approve</button>
                            <button class="btn btn-danger reject-btn" data-project="${req.id}">Reject</button>
                        </div>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', requestCard);
            });
        });
}

document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');
    
    function handleProjectAction(projectId, action) {
        if (action === 'approve') {
            fetch(`/api/faculty/project/${projectId}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: 'approved' })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`request-${projectId}`).remove();
                    document.getElementById('deadlineProjectId').value = projectId;
                    document.getElementById('deadlineModal').style.display = 'block';
                } else { alert('Error: ' + data.message); }
            });
        } else if (action === 'reject') {
            document.getElementById('remarksProjectId').value = projectId;
            document.getElementById('remarksModal').style.display = 'block';
        }
    }

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            const pageId = this.dataset.page;
            document.getElementById(pageId).classList.add('active');
            
            // --- Enhancement: Update Page Title ---
            const pageTitleMap = {
                'dashboard': 'Faculty Dashboard',
                'project-requests': 'Project Requests',
                'my-projects': 'My Projects',
                'profile': 'Profile'
            };
            const pageTitleElement = document.getElementById('page-title');
            if (pageTitleElement) {
                pageTitleElement.textContent = pageTitleMap[pageId] || 'Faculty Portal';
            }
            // --------------------------------------

            if (pageId === 'dashboard') { loadFacultyDashboardStats(); } // <-- THIS LINE IS NEW
            if (pageId === 'project-requests') { loadProjectRequests(); }
            if (pageId === 'my-projects') { loadFacultyMyProjects(); }
            if (pageId === 'profile') { loadFacultyProfileData(); } // <-- ADDED PROFILE LOAD
        });
    });

    // FIX: Change the event delegation listener to the document to include clicks inside the modal.
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('approve-btn')) { handleProjectAction(e.target.dataset.project, 'approve'); }
        if (e.target.classList.contains('reject-btn')) { handleProjectAction(e.target.dataset.project, 'reject'); }
        if (e.target.classList.contains('add-milestone-btn')) {
            document.getElementById('milestoneProjectId').value = e.target.dataset.projectId;
            document.getElementById('addMilestoneModal').style.display = 'block';
        }
        if (e.target.classList.contains('view-details-btn-faculty')) {
            openFacultyDetailsModal(e.target.dataset.projectId);
        }
        // Listener for the Change Deadline button inside the modal
        if (e.target.closest('#facultyViewDetailsModal') && e.target.classList.contains('change-deadline-btn')) {
            const projectId = e.target.dataset.projectId;
            document.getElementById('facultyViewDetailsModal').style.display = 'none'; // Close view details modal
            document.getElementById('deadlineProjectId').value = projectId; 
            document.getElementById('deadlineModal').style.display = 'block';
        }
    });

    document.getElementById('deadlineForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const projectId = document.getElementById('deadlineProjectId').value;
        const submissionDate = document.getElementById('submissionDate').value;
        fetch(`/api/faculty/project/${projectId}/deadline`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ submission_date: submissionDate })
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert('Project deadline set or updated successfully!');
                document.getElementById('deadlineModal').style.display = 'none';
                loadFacultyMyProjects();
            } else { alert('Error: ' + data.message); }
        });
    });

    document.getElementById('remarksForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const projectId = document.getElementById('remarksProjectId').value;
        const remarks = document.getElementById('remarksText').value;
        fetch(`/api/faculty/project/${projectId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'rejected', remarks: remarks })
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert('Project rejected and remarks sent.');
                document.getElementById('remarksModal').style.display = 'none';
                document.getElementById(`request-${projectId}`).remove();
                this.reset();
            } else { alert('Error: ' + data.message); }
        });
    });

    document.getElementById('addMilestoneForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const projectId = document.getElementById('milestoneProjectId').value;
        const formData = {
            title: document.getElementById('milestoneTitle').value,
            description: document.getElementById('milestoneDescription').value,
            percentage_value: document.getElementById('milestonePercentage').value,
        };
        fetch(`/api/faculty/project/${projectId}/add-milestone`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert(data.message);
                document.getElementById('addMilestoneModal').style.display = 'none';
                this.reset();
            } else { alert('Error: ' + data.message); }
        });
    });

        document.getElementById('taskRemarksForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        const taskId = document.getElementById('remarksTaskId').value;
        const remarks = document.getElementById('taskRemarksText').value;

        fetch(`/api/faculty/task/${taskId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'rejected', remarks: remarks })
        }).then(res => res.json()).then(data => {
            if (data.success) {
                alert(data.message);
                document.getElementById('taskRemarksModal').style.display = 'none';
                this.reset();
                loadFacultyMyProjects(); // Refresh the project list
            } else {
                alert('Error: ' + data.message);
            }
        });
    });
    
    document.querySelectorAll('.modal .close, .modal .cancel-btn').forEach(el => {
        el.addEventListener('click', () => el.closest('.modal').style.display = 'none');
    });
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) e.target.style.display = 'none';
    });
    
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        if (confirm('Are you sure you want to logout?')) {
            fetch('/api/logout', { method: 'POST' }).then(() => window.location.href = '/login');
        }
    });
    loadFacultyDashboardStats();
});