document.addEventListener('DOMContentLoaded', () => {

    // Initial State
    let stats = {
        Work: 0,
        Finance: 0,
        Personal: 0,
        Other: 0
    };

    let actionCounts = {
        "Archive": 0,
        "Add to calendar / notify team": 0,
        "Forward to accounts department": 0,
        "Mark as personal / no action": 0
    };

    const actionIcons = {
        "Add to calendar / notify team": "fa-calendar-plus",
        "Forward to accounts department": "fa-share",
        "Mark as personal / no action": "fa-eye-slash",
        "Archive": "fa-box-archive"
    };

    const emailListContainer = document.getElementById('email-list');
    let displayCount = 0;
    const MAX_DISPLAY = 30; // Limit emails displayed to keep UI fast

    // Chart Instance
    const ctx = document.getElementById('actionsChart').getContext('2d');
    const chartColors = ['#6b7280', '#3b82f6', '#10b981', '#f59e0b'];

    let actionsChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(actionCounts),
            datasets: [{
                data: Object.values(actionCounts),
                backgroundColor: chartColors,
                borderWidth: 2,
                borderColor: '#1e222b',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#9aa0a6' } }
            }
        }
    });

    let emailsToShow = [];

    // We fetch and parse the CSV from the local directory
    // Using PapaParse chunk to avoid blocking the main thread for massive files.
    Papa.parse("final_email_assistant.csv", {
        download: true,
        header: true,
        skipEmptyLines: true,
        chunk: function (results) {
            const dataArr = results.data;
            if (!dataArr || dataArr.length === 0) return;

            for (let i = 0; i < dataArr.length; i++) {
                const data = dataArr[i];
                const category = data.Category;
                const action = data.Agent_Action;

                // Update stats logic
                if (stats[category] !== undefined) stats[category]++;
                if (action) {
                    if (actionCounts[action] === undefined) {
                        actionCounts[action] = 0;
                        actionsChart.data.labels.push(action);
                        actionsChart.data.datasets[0].backgroundColor.push('#8b5cf6');
                    }
                    actionCounts[action]++;
                }
            }
            
            // Take the last few emails from this chunk to display as "currently processed"
            const lastEmails = dataArr.slice(-5);
            
            // Update the email list UI with these recent ones
            lastEmails.forEach(data => {
                const subject = data.Subject || "(No Subject)";
                const sender = data.From || "Unknown Sender";
                const category = data.Category;
                const action = data.Agent_Action;
                const catLower = category ? category.toLowerCase() : "unknown";
                const icon = actionIcons[action] || "fa-robot";

                const html = `
                    <div class="email-item">
                        <div class="email-header">
                            <div>
                                <div class="email-sender">${sender}</div>
                                <div class="email-subject">${subject}</div>
                            </div>
                            <div class="email-badges">
                                <span class="badge cat-${catLower}">${category || 'Unknown'}</span>
                            </div>
                        </div>
                        <div class="agent-action">
                            <i class="fa-solid ${icon}"></i>
                            <span><strong>Action:</strong> ${action || 'None'}</span>
                        </div>
                    </div>
                `;
                // Insert at the top of the list
                emailListContainer.insertAdjacentHTML('afterbegin', html);
            });
            
            // Keep the list from growing indefinitely
            while (emailListContainer.children.length > MAX_DISPLAY) {
                emailListContainer.removeChild(emailListContainer.lastChild);
            }

            // Update Dashboard UI values incrementally
            document.getElementById('stat-work').textContent = stats.Work.toLocaleString();
            document.getElementById('stat-finance').textContent = stats.Finance.toLocaleString();
            document.getElementById('stat-personal').textContent = stats.Personal.toLocaleString();
            document.getElementById('stat-other').textContent = stats.Other.toLocaleString();

            // Update the chart incrementally
            actionsChart.data.datasets[0].data = Object.values(actionCounts);
            actionsChart.update();
        },
        complete: function () {
            document.getElementById('parsing-status').textContent = "Agent Online (Dataset Synchronized)";
            const indicator = document.querySelector('.status-indicator');
            if (indicator) {
                indicator.style.animation = "none";
                indicator.style.boxShadow = "0 0 8px #10b981";
                indicator.style.backgroundColor = "#10b981";
            }
        },
        error: function (error) {
            console.error("Error parsing CSV:", error);
            document.getElementById('parsing-status').textContent = "Error parsing CSV.";
        }
    });

    // -----------------------------------------------------
    // Manual Classification Logic (Python replica)
    // -----------------------------------------------------
    function categorize(subject) {
        if (!subject) return "Unknown";
        let sub = subject.toLowerCase();
        if (sub.includes("meeting") || sub.includes("schedule")) return "Work";
        else if (sub.includes("invoice") || sub.includes("payment")) return "Finance";
        else if (sub.includes("party") || sub.includes("invitation")) return "Personal";
        else return "Other";
    }

    function getAgentAction(category) {
        if (category === "Work") return "Add to calendar / notify team";
        else if (category === "Finance") return "Forward to accounts department";
        else if (category === "Personal") return "Mark as personal / no action";
        else return "Archive";
    }

    document.getElementById('btn-classify').addEventListener('click', async () => {
        const subject = document.getElementById('manual-subject').value.trim();
        if (!subject) return;

        const resultBox = document.getElementById('classification-result');
        const resCat = document.getElementById('res-category');
        const resAct = document.getElementById('res-action');
        
        // Indicate loading
        resCat.innerHTML = `Agent is thinking... <i class="fa-solid fa-spinner fa-spin"></i>`;
        resAct.innerHTML = "";
        resultBox.style.display = "flex";

        try {
            const response = await fetch('http://localhost:8000/classify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: subject, thread_id: "demo-thread-1" })
            });

            const data = await response.json();

            if (data.status === "success") {
                const category = data.category;
                const action = data.action;
                const catLower = category.toLowerCase();

                resCat.innerHTML = `Predicted Category: <span class="badge cat-${catLower}" style="margin-left: 10px;">${category}</span>`;
                
                let actionHtml = `
                    <div style="margin-top: 10px;">
                        <strong>Agent Action:</strong> ${action} <i class="fa-solid ${actionIcons[action] || 'fa-robot'}" style="margin-left: 8px; color: var(--accent-primary);"></i>
                    </div>
    // Initial State
    let stats = {
        Work: 0,
        Finance: 0,
        Personal: 0,
        Other: 0
    };

    let actionCounts = {
        "Archive": 0,
        "Add to calendar / notify team": 0,
        "Forward to accounts department": 0,
        "Mark as personal / no action": 0
    };

    const actionIcons = {
        "Add to calendar / notify team": "fa-calendar-plus",
        "Forward to accounts department": "fa-share",
        "Mark as personal / no action": "fa-eye-slash",
        "Archive": "fa-box-archive"
    };

    const emailListContainer = document.getElementById('email-list');
    let displayCount = 0;
    const MAX_DISPLAY = 30; // Limit emails displayed to keep UI fast

    // Chart Instance
    const ctx = document.getElementById('actionsChart').getContext('2d');
    const chartColors = ['#6b7280', '#3b82f6', '#10b981', '#f59e0b'];

    let actionsChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(actionCounts),
            datasets: [{
                data: Object.values(actionCounts),
                backgroundColor: chartColors,
                borderWidth: 2,
                borderColor: '#1e222b',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#9aa0a6' } }
            }
        }
    });

    let emailsToShow = [];

    // We fetch and parse the CSV from the local directory
    // Using PapaParse chunk to avoid blocking the main thread for massive files.
    Papa.parse("final_email_assistant.csv", {
        download: true,
        header: true,
        skipEmptyLines: true,
        chunk: function (results) {
            const dataArr = results.data;
            if (!dataArr || dataArr.length === 0) return;

            for (let i = 0; i < dataArr.length; i++) {
                const data = dataArr[i];
                const category = data.Category;
                const action = data.Agent_Action;

                // Update stats logic
                if (stats[category] !== undefined) stats[category]++;
                if (action) {
                    if (actionCounts[action] === undefined) {
                        actionCounts[action] = 0;
                        actionsChart.data.labels.push(action);
                        actionsChart.data.datasets[0].backgroundColor.push('#8b5cf6');
                    }
                    actionCounts[action]++;
                }
            }
            
            // Take the last few emails from this chunk to display as "currently processed"
            const lastEmails = dataArr.slice(-5);
            
            // Update the email list UI with these recent ones
            lastEmails.forEach(data => {
                const subject = data.Subject || "(No Subject)";
                const sender = data.From || "Unknown Sender";
                const category = data.Category;
                const action = data.Agent_Action;
                const catLower = category ? category.toLowerCase() : "unknown";
                const icon = actionIcons[action] || "fa-robot";

                const html = `
                    <div class="email-item">
                        <div class="email-header">
                            <div>
                                <div class="email-sender">${sender}</div>
                                <div class="email-subject">${subject}</div>
                            </div>
                            <div class="email-badges">
                                <span class="badge cat-${catLower}">${category || 'Unknown'}</span>
                            </div>
                        </div>
                        <div class="agent-action">
                            <i class="fa-solid ${icon}"></i>
                            <span><strong>Action:</strong> ${action || 'None'}</span>
                        </div>
                    </div>
                `;
                // Insert at the top of the list
                emailListContainer.insertAdjacentHTML('afterbegin', html);
            });
            
            // Keep the list from growing indefinitely
            while (emailListContainer.children.length > MAX_DISPLAY) {
                emailListContainer.removeChild(emailListContainer.lastChild);
            }

            // Update Dashboard UI values incrementally
            document.getElementById('stat-work').textContent = stats.Work.toLocaleString();
            document.getElementById('stat-finance').textContent = stats.Finance.toLocaleString();
            document.getElementById('stat-personal').textContent = stats.Personal.toLocaleString();
            document.getElementById('stat-other').textContent = stats.Other.toLocaleString();

            // Update the chart incrementally
            actionsChart.data.datasets[0].data = Object.values(actionCounts);
            actionsChart.update();
        },
        complete: function () {
            document.getElementById('parsing-status').textContent = "Agent Online (Dataset Synchronized)";
            const indicator = document.querySelector('.status-indicator');
            if (indicator) {
                indicator.style.animation = "none";
                indicator.style.boxShadow = "0 0 8px #10b981";
                indicator.style.backgroundColor = "#10b981";
            }
        },
        error: function (error) {
            console.error("Error parsing CSV:", error);
            document.getElementById('parsing-status').textContent = "Error parsing CSV.";
        }
    });

    // -----------------------------------------------------
    // Manual Classification Logic (Python replica)
    // -----------------------------------------------------
    function categorize(subject) {
        if (!subject) return "Unknown";
        let sub = subject.toLowerCase();
        if (sub.includes("meeting") || sub.includes("schedule")) return "Work";
        else if (sub.includes("invoice") || sub.includes("payment")) return "Finance";
        else if (sub.includes("party") || sub.includes("invitation")) return "Personal";
        else return "Other";
    }

    function getAgentAction(category) {
        if (category === "Work") return "Add to calendar / notify team";
        else if (category === "Finance") return "Forward to accounts department";
        else if (category === "Personal") return "Mark as personal / no action";
        else return "Archive";
    }

    document.getElementById('btn-classify').addEventListener('click', async () => {
        const subject = document.getElementById('manual-subject').value.trim();
        if (!subject) return;

        const resultBox = document.getElementById('classification-result');
        const resCat = document.getElementById('res-category');
        const resAct = document.getElementById('res-action');
        
        // Indicate loading
        resCat.innerHTML = `Agent is thinking... <i class="fa-solid fa-spinner fa-spin"></i>`;
        resAct.innerHTML = "";
        resultBox.style.display = "flex";

        try {
            const response = await fetch('http://localhost:8000/classify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: subject, thread_id: "demo-thread-1" })
            });

            const data = await response.json();

            if (data.status === "success") {
                const category = data.category;
                const action = data.action;
                const catLower = category.toLowerCase();

                resCat.innerHTML = `Predicted Category: <span class="badge cat-${catLower}" style="margin-left: 10px;">${category}</span>`;
                
                let actionHtml = `
                    <div style="margin-top: 10px;">
                        <strong>Agent Action:</strong> ${action} <i class="fa-solid ${actionIcons[action] || 'fa-robot'}" style="margin-left: 8px; color: var(--accent-primary);"></i>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.85em; color: #9aa0a6; font-style: italic;">
                        <strong>Reasoning:</strong> "${data.reasoning}"
                    </div>
                `;

                if (data.requires_human_approval) {
                    actionHtml += `
                        <div id="hitl-container" style="margin-top: 15px; padding: 10px; border: 1px dashed #f59e0b; border-radius: 8px; background-color: rgba(245, 158, 11, 0.1);">
                            <strong style="color: #f59e0b;"><i class="fa-solid fa-triangle-exclamation"></i> Action Paused (Human-in-the-Loop)</strong>
                            <p style="font-size: 0.85em; margin-bottom: 10px; margin-top: 5px;">Agent requests permission to execute this critical action.</p>
                            <button id="btn-approve" class="btn" style="background-color: #10b981; color: white; padding: 5px 15px; margin-right: 10px;">Approve</button>
                            <button id="btn-deny" class="btn" style="background-color: #ef4444; color: white; padding: 5px 15px; margin-right: 10px;">Deny</button>
                            
                            <hr style="border: 0; border-top: 1px solid rgba(245, 158, 11, 0.3); margin: 10px 0;">
                            <div style="display: flex; gap: 10px;">
                                <input type="text" id="edit-instruction" placeholder="e.g., 'Actually, call him Robert'" style="flex: 1; padding: 8px; border-radius: 4px; border: 1px solid #4b5563; background: #1f2937; color: #fff;">
                                <button id="btn-edit" class="btn" style="background-color: #3b82f6; color: white; padding: 5px 15px;">Edit & Learn</button>
                            </div>
                        </div>
                    `;
                }

                resAct.innerHTML = actionHtml;

                if (data.requires_human_approval) {
                    document.getElementById('btn-approve').addEventListener('click', () => sendDecision('approve'));
                    document.getElementById('btn-deny').addEventListener('click', () => sendDecision('deny'));
                    document.getElementById('btn-edit').addEventListener('click', () => {
                        const instruction = document.getElementById('edit-instruction').value.trim();
                        sendDecision('edit', instruction);
                    });
                }

            } else {
                resCat.innerHTML = `<span style="color: #ef4444;">Error: ${data.detail || "Agent offline"}</span>`;
            }
        } catch (error) {
            console.error("Classification error:", error);
            resCat.innerHTML = `<span style="color: #ef4444;">Could not connect to backend. Is the server running?</span>`;
        }
    });

    async function sendDecision(decisionStr, editInstruction = "") {
        const hitlContainer = document.getElementById('hitl-container');
        hitlContainer.innerHTML = `Processing ${decisionStr}... <i class="fa-solid fa-spinner fa-spin"></i>`;
        
        try {
            const response = await fetch('http://localhost:8000/human_decision', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision: decisionStr, thread_id: "demo-thread-1", edit_instruction: editInstruction })
            });
            const data = await response.json();
            
            if (decisionStr === 'approve') {
                hitlContainer.innerHTML = `<strong style="color: #10b981;"><i class="fa-solid fa-check"></i> Action Executed Successfully.</strong><br/><span style="font-size: 0.8em; color: #9aa0a6;">${data.final_reasoning}</span>`;
                hitlContainer.style.borderColor = "#10b981";
                hitlContainer.style.backgroundColor = "rgba(16, 185, 129, 0.1)";
            } else if (decisionStr === 'edit') {
                hitlContainer.innerHTML = `<strong style="color: #3b82f6;"><i class="fa-solid fa-brain"></i> Memory Updated. Executing...</strong><br/><span style="font-size: 0.8em; color: #9aa0a6;">${data.final_reasoning}</span>`;
                hitlContainer.style.borderColor = "#3b82f6";
                hitlContainer.style.backgroundColor = "rgba(59, 130, 246, 0.1)";
            } else {
                hitlContainer.innerHTML = `<strong style="color: #ef4444;"><i class="fa-solid fa-xmark"></i> Action Denied & Aborted.</strong>`;
                hitlContainer.style.borderColor = "#ef4444";
                hitlContainer.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
            }
        } catch (e) {
            hitlContainer.innerHTML = "Error processing decision.";
        }
    }
});
