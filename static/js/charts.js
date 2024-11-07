// Update charts every minute
setInterval(updateCharts, 60000);

async function updateCharts() {
    await Promise.all([
        updateCurrentChart(),
        updateTrendChart()
    ]);
}

async function updateCurrentChart() {
    const response = await fetch('/api/current');
    const data = await response.json();
    
    const ctx = document.getElementById('currentChart').getContext('2d');
    
    if (window.currentChart) {
        window.currentChart.destroy();
    }
    
    window.currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Alerts', 'Warnings', 'Severe'],
            datasets: [{
                label: 'Current Flood Status',
                data: [data.alerts, data.warnings, data.severes],
                backgroundColor: [
                    'rgba(255, 193, 7, 0.5)',  // Yellow for alerts
                    'rgba(255, 87, 34, 0.5)',  // Orange for warnings
                    'rgba(244, 67, 54, 0.5)'   // Red for severe
                ],
                borderColor: [
                    'rgb(255, 193, 7)',
                    'rgb(255, 87, 34)',
                    'rgb(244, 67, 54)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

async function updateTrendChart() {
    const response = await fetch('/api/historical');
    const data = await response.json();
    
    const timestamps = data.map(d => new Date(d.timestamp).toLocaleTimeString());
    const alerts = data.map(d => d.alerts);
    const warnings = data.map(d => d.warnings);
    const severes = data.map(d => d.severes);
    
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (window.trendChart) {
        window.trendChart.destroy();
    }
    
    window.trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: 'Alerts',
                    data: alerts,
                    borderColor: 'rgb(255, 193, 7)',
                    fill: false
                },
                {
                    label: 'Warnings',
                    data: warnings,
                    borderColor: 'rgb(255, 87, 34)',
                    fill: false
                },
                {
                    label: 'Severe',
                    data: severes,
                    borderColor: 'rgb(244, 67, 54)',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Initial chart update
updateCharts();
