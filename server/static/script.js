/**
 * Email Triage AI - Dashboard Controller
 */

const API = {
    listTasks: async () => (await fetch('/tasks')).json(),
    reset: async (taskId) => {
        const res = await fetch('/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId, session_id: 'default' })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },
    step: async (action) => {
        const res = await fetch('/step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: 'default', action })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    }
};

const UI = {
    // State
    currentTask: null,
    isProcessing: false,
    autoMode: false,
    
    // DOM Elements
    els: {
        connLabel: document.getElementById('conn-label'),
        connPill: document.getElementById('conn-pill'),
        session: document.getElementById('session-id'),
        taskHead: document.getElementById('header-task'),
        
        scoreNum: document.getElementById('score-number'),
        scorePct: document.getElementById('score-pct'),
        scoreRing: document.getElementById('score-ring-fill'),
        
        statProcessed: document.getElementById('stat-processed'),
        statRemaining: document.getElementById('stat-remaining'),
        statSteps: document.getElementById('stat-steps'),
        
        tasksList: document.getElementById('tasks-list'),
        taskCount: document.getElementById('task-count'),
        
        btnReset: document.getElementById('btn-reset'),
        btnAuto: document.getElementById('btn-auto'),
        btnClearLog: document.getElementById('btn-clear-log'),
        
        progLabel: document.getElementById('progress-label'),
        progText: document.getElementById('progress-text'),
        progFill: document.getElementById('progress-fill'),
        rewardBars: document.getElementById('reward-bars'),
        
        emailCard: document.getElementById('email-card'),
        emailSubj: document.getElementById('email-subject'),
        emailTags: document.getElementById('email-tags'),
        
        viewEmail: document.getElementById('view-email'),
        welcomeState: document.getElementById('welcome-state'),
        doneState: document.getElementById('done-state'),
        emailContent: document.getElementById('email-content'),
        
        emailFrom: document.getElementById('email-from'),
        emailTime: document.getElementById('email-time'),
        emailBody: document.getElementById('email-body'),
        feedbackBanner: document.getElementById('feedback-banner'),
        
        metaGrid: document.getElementById('meta-grid'),
        jsonView: document.getElementById('json-view'),
        
        actionPanel: document.getElementById('action-panel'),
        actionTitle: document.getElementById('action-title'),
        actionHint: document.getElementById('action-hint'),
        actionGrid: document.getElementById('action-grid'),
        
        logList: document.getElementById('log-list'),
        toast: document.getElementById('toast')
    },

    async init() {
        this.bindEvents();
        try {
            const tasks = await API.listTasks();
            this.renderTasks(tasks);
            this.setConnection(true);
            this.log('System initialized. Ready for evaluation.', 'info');
        } catch (e) {
            this.setConnection(false);
            this.log('Server unreachable. Ensure FastAPI is running.', 'error');
            this.showToast('Connection failed');
        }
    },

    bindEvents() {
        this.els.btnReset.addEventListener('click', () => this.resetCurrent());
        this.els.btnAuto.addEventListener('click', () => this.toggleAuto());
        this.els.btnClearLog.addEventListener('click', () => {
            this.els.logList.innerHTML = '<div class="log-empty">No activity yet.</div>';
        });

        // Tabs
        document.querySelectorAll('.tab').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
                document.getElementById(e.target.dataset.tab).classList.add('active');
            });
        });
    },

    setConnection(isOk) {
        this.els.connPill.className = `status-pill ${isOk ? 'connected' : 'error'}`;
        this.els.connLabel.textContent = isOk ? 'Connected' : 'Offline';
    },

    showToast(msg, duration=3000) {
        this.els.toast.textContent = msg;
        this.els.toast.classList.add('show');
        setTimeout(() => this.els.toast.classList.remove('show'), duration);
    },

    log(msg, type='info') {
        const d = new Date();
        const time = `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
        
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span class="log-time">${time}</span>${msg}`;
        
        this.els.logList.prepend(entry);
        
        const empty = this.els.logList.querySelector('.log-empty');
        if (empty) empty.remove();
    },

    renderTasks(tasks) {
        this.els.tasksList.innerHTML = '';
        const entries = Object.entries(tasks);
        this.els.taskCount.textContent = entries.length;

        entries.forEach(([id, cfg]) => {
            const el = document.createElement('div');
            el.className = 'task-item';
            el.dataset.id = id;
            el.innerHTML = `
                <span class="task-name">${cfg.name}</span>
                <span class="task-meta">${cfg.num_emails} emails • ${cfg.difficulty}</span>
            `;
            el.addEventListener('click', () => this.selectTask(id, cfg.name));
            this.els.tasksList.appendChild(el);
        });
    },

    async selectTask(id, name) {
        if (this.isProcessing) return;
        
        document.querySelectorAll('.task-item').forEach(el => el.classList.remove('active'));
        document.querySelector(`.task-item[data-id="${id}"]`).classList.add('active');
        
        this.currentTask = { id, name };
        this.els.taskHead.textContent = name;
        this.els.btnReset.disabled = false;
        
        await this.resetCurrent();
    },

    async resetCurrent() {
        if (!this.currentTask) return;
        
        this.isProcessing = true;
        this.setViewMode('welcome');
        this.els.rewardBars.innerHTML = ''; // clear history
        this.log(`Initializing sequence: ${this.currentTask.id}`, 'info');

        try {
            const data = await API.reset(this.currentTask.id);
            this.els.session.textContent = data.session_id.substring(0,8);
            this.updateData(data.observation);
            this.log('Environment reset. Episode started.', 'success');
        } catch (e) {
            this.log(`Reset failed: ${e.message}`, 'error');
            this.showToast('Reset failed');
        } finally {
            this.isProcessing = false;
        }
    },

    updateData(obs) {
        // Stats
        this.els.statProcessed.textContent = obs.emails_processed;
        this.els.statRemaining.textContent = obs.emails_remaining;
        
        // Progress
        const total = obs.total_emails || 1;
        const processed = obs.emails_processed || 0;
        const pct = (processed / total) * 100;
        
        this.els.progLabel.textContent = obs.task_description;
        this.els.progText.textContent = `${processed} / ${total}`;
        this.els.progFill.style.width = `${pct}%`;
        
        // Score Ring (Max 314.16)
        const score = obs.cumulative_score || 0;
        this.els.scoreNum.textContent = score.toFixed(2);
        this.els.scorePct.textContent = `${(score * 100).toFixed(0)}%`;
        const offset = 314.16 - (314.16 * score);
        this.els.scoreRing.style.strokeDashoffset = offset;

        // JSON & Meta
        this.els.jsonView.textContent = JSON.stringify(obs, null, 2);
        
        // Setup Email View
        if (obs.done || !obs.current_email) {
            this.setViewMode('done');
            document.getElementById('done-score-text').innerHTML = `Episode finished with a final score of <b>${score.toFixed(2)}</b>.`;
            this.els.actionPanel.style.display = 'none';
            this.els.btnAuto.disabled = true;
            this.autoMode = false;
            return;
        }

        const email = obs.current_email;
        this.els.emailSubj.textContent = email.subject;
        this.els.emailFrom.textContent = email.sender;
        this.els.emailTime.textContent = email.timestamp;
        this.els.emailBody.textContent = email.body;
        
        this.els.metaGrid.innerHTML = `
            <div class="meta-item"><label>Email ID</label><div>${email.id}</div></div>
            <div class="meta-item"><label>Observation Step</label><div>${obs.emails_processed}</div></div>
            <div class="meta-item"><label>Queue Size</label><div>${obs.emails_remaining + 1}</div></div>
            <div class="meta-item"><label>Last Feedback</label><div>${obs.last_action_feedback || '—'}</div></div>
        `;
        
        this.els.btnAuto.disabled = false;
        this.setViewMode('content');
        this.renderActions(obs);
    },

    renderActions(obs) {
        this.els.actionPanel.style.display = 'block';
        this.els.actionGrid.innerHTML = '';
        
        const tId = obs.task_id;
        
        if (tId.includes('task_1')) {
            this.els.actionTitle.textContent = "Binary Classification";
            this.els.actionHint.textContent = "Is this actionable?";
            this.makeBtn('Actionable', { binary_label: 'actionable' }, 'actionable');
            this.makeBtn('Not Actionable', { binary_label: 'not_actionable' }, 'urgent');
        } 
        else if (tId.includes('task_2')) {
            this.els.actionTitle.textContent = "Priority Assignment";
            this.els.actionHint.textContent = "Set priority and reply status.";
            ['urgent', 'high', 'medium', 'low', 'spam'].forEach(p => {
                this.makeBtn(p, { priority_label: p, requires_reply: p==='urgent'||p==='high' }, p);
            });
        }
        else {
            this.els.actionTitle.textContent = "Full Triage";
            this.els.actionHint.textContent = "Assign priority & category.";
            ['urgent', 'high', 'medium', 'low', 'spam'].forEach(p => {
                this.makeBtn(p, { 
                    priority_label: p, 
                    requires_reply: p==='urgent',
                    category: 'admin',
                    action_summary: `Routed as ${p}`
                }, p);
            });
        }

        // Global Skip
        this.makeBtn('Skip (Penalty)', { skip: true }, 'skip');
    },

    makeBtn(label, payload, cls) {
        const b = document.createElement('button');
        b.className = `btn-action ${cls}`;
        b.textContent = label.charAt(0).toUpperCase() + label.slice(1);
        b.onclick = () => this.handleAction(payload);
        this.els.actionGrid.appendChild(b);
    },

    async handleAction(payload) {
        if (this.isProcessing) return;
        this.isProcessing = true;
        
        this.els.actionGrid.style.opacity = '0.5';
        
        try {
            const data = await API.step(payload);
            const obs = data.observation;
            const rew = data.reward;
            
            this.els.statSteps.textContent = parseInt(this.els.statSteps.textContent) + 1;
            
            // Log & Feedback
            if (rew.step_reward > 0.7) {
                this.log(`Action evaluated: Optimal (+${rew.step_reward})`, 'success');
                this.showFeedback(rew.feedback, 'success');
                this.els.emailCard.classList.remove('pulse-glow');
                void this.els.emailCard.offsetWidth; // trigger reflow
                this.els.emailCard.classList.add('pulse-glow');
            } else if (rew.step_reward > 0) {
                this.log(`Action evaluated: Suboptimal (+${rew.step_reward})`, 'warning');
                this.showFeedback(rew.feedback, 'warning');
            } else {
                this.log(`Action evaluated: Incorrect (+0.0)`, 'error');
                this.showFeedback(rew.feedback, 'penalty');
            }

            // Reward chart
            const bar = document.createElement('div');
            bar.className = `reward-bar ${rew.penalty_applied || rew.step_reward === 0 ? 'penalty' : ''}`;
            bar.style.height = `${Math.max(10, rew.step_reward * 100)}%`;
            bar.title = `Step: ${rew.step_reward}`;
            this.els.rewardBars.appendChild(bar);

            this.updateData(obs);
            
            if (this.autoMode && !obs.done) {
                setTimeout(() => this.simulateAutoAgent(), 1000);
            }
            
        } catch (e) {
            this.log(`Step failed: ${e.message}`, 'error');
            this.showToast('Action failed');
        } finally {
            this.isProcessing = false;
            this.els.actionGrid.style.opacity = '1';
        }
    },

    showFeedback(text, type) {
        const b = this.els.feedbackBanner;
        b.textContent = text;
        b.className = `feedback-banner ${type==='penalty'?'penalty':''}`;
        b.classList.remove('hidden');
    },

    setViewMode(mode) {
        this.els.welcomeState.classList.add('hidden');
        this.els.emailContent.classList.add('hidden');
        this.els.doneState.classList.add('hidden');
        this.els.feedbackBanner.classList.add('hidden');
        
        if (mode === 'welcome') {
            this.els.welcomeState.classList.remove('hidden');
            this.els.emailSubj.textContent = "Waiting for start...";
        } else if (mode === 'content') {
            this.els.emailContent.classList.remove('hidden');
        } else if (mode === 'done') {
            this.els.doneState.classList.remove('hidden');
            this.els.emailSubj.textContent = "Evaluation Finished";
        }
    },

    toggleAuto() {
        this.autoMode = !this.autoMode;
        this.els.btnAuto.classList.toggle('btn-primary', this.autoMode);
        this.els.btnAuto.classList.toggle('btn-ghost', !this.autoMode);
        this.els.btnAuto.innerHTML = this.autoMode 
            ? '<span>⏹ Stop Auto</span>' 
            : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Auto-Triage Demo`;
            
        if (this.autoMode) {
            this.log("Auto-triage agent activated.", "info");
            this.simulateAutoAgent();
        } else {
            this.log("Auto-triage agent stopped.", "warning");
        }
    },

    simulateAutoAgent() {
        if (!this.autoMode || this.isProcessing) return;
        
        // Randomly pick an available action button
        const buttons = document.querySelectorAll('.btn-action:not(.skip)');
        if (buttons.length > 0) {
            const randomBtn = buttons[Math.floor(Math.random() * buttons.length)];
            randomBtn.click();
        }
    }
};

window.addEventListener('DOMContentLoaded', () => UI.init());
