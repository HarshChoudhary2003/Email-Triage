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
        // Update Progress
        const processed = obs.emails_processed || 0;
        const total = obs.total_emails || 1;
        const percent = (processed / total) * 100;
        document.getElementById('progress-text').textContent = `${processed}/${total} Emails`;
        document.getElementById('progress-fill').style.width = `${percent}%`;

        // Update Tabs/Content
        if (!obs || !obs.current_email) {
            document.getElementById('tab-email').innerHTML = `
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
        document.getElementById('tab-email').innerHTML = `
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
            </div>
        `;

        // Metadata view
        document.getElementById('metadata-content').innerHTML = `
            <div class="email-field"><span class="label">ID</span><div class="value">${email.id}</div></div>
            <div class="email-field"><span class="label">Timestamp</span><div class="value">${email.timestamp}</div></div>
            <div class="email-field"><span class="label">Remaining</span><div class="value">${obs.emails_remaining}</div></div>
            <div class="email-field"><span class="label">History</span><div class="value">${obs.last_action_feedback || 'None'}</div></div>
        `;

        // JSON View
        document.getElementById('json-inspector').textContent = JSON.stringify(obs, null, 2);

        this.renderActions(obs);
    },

    renderActions(obs) {
        this.actionControls.innerHTML = '';
        this.actionPanel.style.display = 'block';

        const taskId = obs.task_id;
        
        if (taskId.includes('task_1')) {
            this.createActionBtn('Actionable', { binary_label: 'actionable' }, 'actionable');
            this.createActionBtn('Not Actionable', { binary_label: 'not_actionable' }, 'not_actionable');
        } else if (taskId.includes('task_2')) {
            ['urgent', 'high', 'medium', 'low', 'spam'].forEach(p => {
                this.createActionBtn(p, { priority_label: p, requires_reply: true }, p);
            });
        } else if (taskId.includes('task_3')) {
            // Task 3 is complex, we'll provide a simplified 'Action' button or more buttons
            ['urgent', 'high', 'medium', 'low', 'spam'].forEach(p => {
                this.createActionBtn(p, { 
                    priority_label: p, 
                    requires_reply: p === 'urgent' || p === 'high',
                    category: 'general',
                    action_summary: `Triaged as ${p}`
                }, p);
            });
        }

        // Add Skip Button
        const skipBtn = document.createElement('button');
        skipBtn.className = 'action-btn skip-btn';
        skipBtn.textContent = 'Skip Email (Penalty)';
        skipBtn.onclick = () => this.handleAction({ skip: true });
        this.actionControls.appendChild(skipBtn);
    },

    createActionBtn(label, actionObj, styleType) {
        const btn = document.createElement('button');
        btn.className = 'action-btn';
        if (styleType) btn.dataset.type = styleType;
        if (styleType) btn.dataset.action = styleType;
        btn.textContent = label.charAt(0).toUpperCase() + label.slice(1);
        btn.onclick = () => this.handleAction(actionObj);
        this.actionControls.appendChild(btn);
    },

    async handleAction(actionObj) {
        try {
            this.addLog(`Performing action...`, 'info');
            
            const result = await API.step(actionObj);
            
            if (result.error) throw new Error(result.error);

            this.updateStats(result.observation.emails_processed, result.reward.cumulative_reward);
            this.renderObservation(result.observation);
            
            const stepReward = result.reward.step_reward;
            if (stepReward >= 0.8) {
                this.addLog(`Excellent! Reward: +${stepReward}`, 'success');
                this.showNotification('Great Choice! ✨');
                this.triggerSparkle();
            } else if (stepReward > 0.4) {
                this.addLog(`Acceptable. Reward: +${stepReward}`, 'info');
            } else {
                this.addLog(`Incorrect. Reward: ${stepReward}`, 'error');
                this.showNotification('Suboptimal Action', 3000);
            }

            if (result.done) {
                this.addLog(`<b>Task Finished!</b> Final Score: ${result.reward.cumulative_reward.toFixed(2)}`, 'success');
                this.showNotification('Task Completed! 🏆');
            }
        } catch (err) {
            this.addLog(`Error: ${err.message}`, 'error');
            this.showNotification('Action failed', 4000);
        }
    },

    triggerSparkle() {
        const obs = document.getElementById('observation-container');
        obs.style.boxShadow = '0 0 40px var(--success)';
        setTimeout(() => obs.style.boxShadow = 'var(--shadow)', 1000);
    },

    updateStats(steps, score) {
        this.statSteps.textContent = steps;
        this.statScore.textContent = typeof score === 'number' ? score.toFixed(2) : score;
    },

    async init() {
        // Tab Handling
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.onclick = () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
            };
        });

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
