const API = {
    listTasks: async () => (await fetch('/tasks')).json(),
    reset: async (taskId) => {
        const res = await fetch('/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId, session_id: 'default' })
        });
        return res.json();
    },
    step: async (action) => {
        const res = await fetch('/step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: 'default', action })
        });
        return res.json();
    },
    getState: async () => (await fetch('/state?session_id=default')).json()
};

const UI = {
    tasksList: document.getElementById('tasks-list'),
    obsContent: document.getElementById('obs-content'),
    actionPanel: document.getElementById('action-panel'),
    actionControls: document.getElementById('action-controls'),
    taskIdDisplay: document.getElementById('task-name-display'),
    logsList: document.getElementById('logs-list'),
    statSteps: document.getElementById('stat-steps'),
    statScore: document.getElementById('stat-score'),
    sessionId: document.getElementById('session-id'),
    connStatus: document.getElementById('connection-status'),
    resetBtn: document.getElementById('reset-btn'),
    clearLogsBtn: document.getElementById('clear-logs'),
    notification: document.getElementById('notification'),

    currentTaskId: null,

    showNotification(msg, duration = 3000) {
        this.notification.textContent = msg;
        this.notification.classList.add('show');
        setTimeout(() => this.notification.classList.remove('show'), duration);
    },

    addLog(msg, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        entry.innerHTML = `<span style="color:var(--text-muted)">[${time}]</span> ${msg}`;
        this.logsList.prepend(entry);
        
        // Remove empty state if present
        const empty = this.logsList.querySelector('.empty-log');
        if (empty) empty.remove();
    },

    renderObservation(obs) {
        if (!obs || !obs.current_email) {
            this.obsContent.innerHTML = `
                <div class="welcome-message">
                    <h2>Task Completed!</h2>
                    <p>You have triaged all emails in this set.</p>
                    <div class="hero-icons">✅ 🏆 📬</div>
                </div>
            `;
            this.actionPanel.style.display = 'none';
            return;
        }

        const email = obs.current_email;
        this.obsContent.innerHTML = `
            <div class="email-view">
                <div class="email-field">
                    <span class="label">From</span>
                    <div class="value">${email.sender}</div>
                </div>
                <div class="email-field">
                    <span class="label">Subject</span>
                    <div class="value" style="font-weight:700">${email.subject}</div>
                </div>
                <div class="email-field">
                    <span class="label">Content</span>
                    <div class="value email-body">${email.body}</div>
                </div>
                <div class="email-field">
                    <span class="label">Metadata</span>
                    <div class="value" style="font-size:0.8rem; color:var(--text-muted)">
                        ID: ${email.id} | Timestamp: ${email.timestamp || 'N/A'}
                    </div>
                </div>
            </div>
        `;

        this.renderActions(obs.available_actions);
    },

    renderActions(actions) {
        this.actionControls.innerHTML = '';
        this.actionPanel.style.display = 'block';

        if (!actions || actions.length === 0) {
            this.actionControls.innerHTML = '<p style="color:var(--text-muted)">No actions available.</p>';
            return;
        }

        actions.forEach(actStr => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.textContent = actStr;
            btn.onclick = () => this.handleAction(actStr);
            this.actionControls.appendChild(btn);
        });
    },

    async handleAction(actionStr) {
        try {
            this.addLog(`Performing action: <b>${actionStr}</b>`, 'info');
            
            // Format action for API
            let actionObj = { type: actionStr };
            
            // Heuristic for OpenEnv Action parsing if needed, but the current app.py 
            // expects a Dict[str, Any] which Action(**req.action) handles.
            // In our env, action types are like "Archive", "Label: Priority", etc.
            
            const result = await API.step(actionObj);
            
            if (result.error) throw new Error(result.error);

            this.updateStats(result.observation.step_count, result.reward.total);
            this.renderObservation(result.observation);
            
            if (result.reward.last > 0) {
                this.addLog(`Action successful! Reward: +${result.reward.last.toFixed(2)}`, 'success');
            } else if (result.reward.last < 0) {
                this.addLog(`Incorrect action. Penalty: ${result.reward.last.toFixed(2)}`, 'error');
            } else {
                this.addLog(`Action recorded.`, 'info');
            }

            if (result.done) {
                this.addLog(`<b>Task Finished!</b> Final Score: ${result.reward.total.toFixed(2)}`, 'success');
                this.showNotification('Task Completed!');
            }
        } catch (err) {
            this.addLog(`Error: ${err.message}`, 'error');
            this.showNotification('Action failed', 4000);
        }
    },

    updateStats(steps, score) {
        this.statSteps.textContent = steps;
        this.statScore.textContent = typeof score === 'number' ? score.toFixed(2) : score;
    },

    async init() {
        try {
            const tasks = await API.listTasks();
            this.tasksList.innerHTML = '';
            
            Object.entries(tasks).forEach(([id, cfg]) => {
                const item = document.createElement('div');
                item.className = 'task-item';
                item.dataset.id = id;
                item.innerHTML = `
                    <span class="task-name">${cfg.name}</span>
                    <span class="task-meta">${cfg.num_emails} emails • ${cfg.difficulty}</span>
                `;
                item.onclick = () => this.selectTask(id);
                this.tasksList.appendChild(item);
            });

            this.connStatus.textContent = 'Connected';
            this.connStatus.classList.remove('pulse');
            this.connStatus.style.color = 'var(--success)';
            
            this.addLog('System initialized. Select a task to begin.', 'info');
        } catch (err) {
            console.error(err);
            this.connStatus.textContent = 'Offline';
            this.connStatus.style.color = 'var(--error)';
            this.showNotification('Failed to connect to server');
        }

        this.resetBtn.onclick = () => {
            if (this.currentTaskId) this.selectTask(this.currentTaskId);
            else this.showNotification('Select a task first');
        };

        this.clearLogsBtn.onclick = () => {
            this.logsList.innerHTML = '<div class="empty-log">Log is empty.</div>';
        };
    },

    async selectTask(id) {
        try {
            // UI updates
            document.querySelectorAll('.task-item').forEach(el => el.classList.remove('active'));
            const active = document.querySelector(`.task-item[data-id="${id}"]`);
            if (active) active.classList.add('active');
            
            this.currentTaskId = id;
            this.taskIdDisplay.textContent = id.replace(/_/g, ' ');
            
            this.addLog(`Initializing task: ${id}...`, 'info');
            
            const result = await API.reset(id);
            this.sessionId.textContent = result.session_id;
            this.renderObservation(result.observation);
            this.updateStats(0, 0.0);
            
            this.addLog(`Task ready.`, 'success');
            this.showNotification('Task environment reset');
        } catch (err) {
            this.addLog(`Failed to reset task: ${err.message}`, 'error');
        }
    }
};

window.onload = () => UI.init();
