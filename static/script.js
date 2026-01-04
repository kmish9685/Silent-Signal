document.addEventListener('DOMContentLoaded', () => {
    // --- Signal Submission Logic (index.html) ---
    if (document.querySelector('.signal-grid')) {
        const buttons = document.querySelectorAll('.signal-btn');
        const contextSelect = document.getElementById('context');
        const messageInput = document.getElementById('message');
        const statusDiv = document.getElementById('status');

        buttons.forEach(btn => {
            btn.addEventListener('click', async () => {
                const type = btn.dataset.type;
                const context = contextSelect.value;
                const message = messageInput.value;

                // UI Feedback
                btn.style.transform = 'scale(0.95)';
                setTimeout(() => btn.style.transform = '', 100);

                try {
                    const res = await fetch('/api/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ type, context, message })
                    });

                    if (res.ok) {
                        statusDiv.textContent = 'Signal Sent!';
                        messageInput.value = ''; // Clear input
                        setTimeout(() => statusDiv.textContent = '', 2000);
                    }
                } catch (e) {
                    console.error(e);
                    statusDiv.textContent = 'Error sending signal.';
                }
            });
        });
    }

    // --- Dashboard Logic (dashboard.html) ---
    if (document.querySelector('.dashboard-container')) {
        let typeChart, contextChart;

        async function fetchStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();

            updateCharts(data);
            updateInsights(data.insights);
            updateTable(data.recent_signals);

            document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }

        function updateCharts(data) {
            const typeCtx = document.getElementById('typeChart').getContext('2d');
            const contextCtx = document.getElementById('contextChart').getContext('2d');

            // --- Type Chart ---
            const typeLabels = Object.keys(data.type_counts);
            const typeValues = Object.values(data.type_counts);

            if (typeChart) typeChart.destroy();
            typeChart = new Chart(typeCtx, {
                type: 'bar', // Using Bar for clarity
                data: {
                    labels: typeLabels,
                    datasets: [{
                        label: 'Signals',
                        data: typeValues,
                        backgroundColor: ['#ff6b6b', '#fca5a5', '#f87171', '#4ade80', '#60a5fa'],
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, grid: { color: '#334155' } }, x: { grid: { display: false } } }
                }
            });

            // --- Context Chart (Doughnut as Heatmap replacement for simplicity) ---
            const contextLabels = Object.keys(data.context_counts);
            const contextValues = Object.values(data.context_counts);

            if (contextChart) contextChart.destroy();
            contextChart = new Chart(contextCtx, {
                type: 'doughnut',
                data: {
                    labels: contextLabels,
                    datasets: [{
                        data: contextValues,
                        backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'right', labels: { color: '#94a3b8' } } }
                }
            });
        }

        function updateInsights(insights) {
            const container = document.getElementById('ai-insights');
            container.innerHTML = insights.map(text =>
                `<div class="insight-card">${text}</div>`
            ).join('');
        }

        function updateTable(signals) {
            const tbody = document.querySelector('#signals-table tbody');
            tbody.innerHTML = signals.map(s => `
                <tr>
                    <td>${new Date(s.timestamp).toLocaleTimeString()}</td>
                    <td>${s.type}</td>
                    <td>${s.context}</td>
                    <td style="color: #94a3b8; font-style: italic;">${s.message || '-'}</td>
                </tr>
            `).join('');
        }

        // Initial Load & Poll
        fetchStats();
        setInterval(fetchStats, 5000); // Poll every 5s
    }
});
