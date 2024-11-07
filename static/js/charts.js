// Update charts every minute
setInterval(updateCharts, 60000);

let currentChart = null;
let trendChart = null;

async function updateCharts() {
    try {
        console.log('Starting chart updates...');
        await Promise.all([
            updateCurrentChart(),
            updateTrendChart()
        ]);
        console.log('Charts updated successfully');
    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

async function createChart(ctx, config) {
    try {
        if (typeof Chart === 'undefined') {
            throw new Error('Chart.js is not loaded');
        }
        return new Chart(ctx, config);
    } catch (error) {
        console.error('Error creating chart:', error);
        return null;
    }
}

async function updateCurrentChart() {
    try {
        console.log('Fetching current data...');
        const response = await fetch('/api/current');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Current data received:', data);

        if (!data) {
            console.warn('No current data available');
            return;
        }

        const ctx = document.getElementById('currentChart');
        if (!ctx) {
            console.error('Current chart canvas not found');
            return;
        }

        const config = {
            type: 'bar',
            data: {
                labels: ['Alerts', 'Warnings', 'Severe'],
                datasets: [{
                    label: 'Current Flood Status',
                    data: [
                        data.alerts || 0,
                        data.warnings || 0,
                        data.severes || 0
                    ],
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
        };

        if (currentChart instanceof Chart) {
            currentChart.destroy();
        }
        
        currentChart = await createChart(ctx.getContext('2d'), config);
    } catch (error) {
        console.error('Error updating current chart:', error);
    }
}

async function updateTrendChart() {
    try {
        console.log('Fetching historical data...');
        const response = await fetch('/api/historical');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Historical data received:', data);

        if (!data || !Array.isArray(data) || data.length === 0) {
            console.warn('No historical data available');
            return;
        }

        const ctx = document.getElementById('trendChart');
        if (!ctx) {
            console.error('Trend chart canvas not found');
            return;
        }

        const timestamps = data.map(d => {
            const date = new Date(d.timestamp);
            return date.toLocaleDateString('en-GB', { 
                weekday: 'short',
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).replace(',', '');
        });

        const alerts = data.map(d => d.alerts || 0);
        const warnings = data.map(d => d.warnings || 0);
        const severes = data.map(d => d.severes || 0);
        
        const config = {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: 'Total Warnings',
                        data: data.map(d => (d.alerts || 0) + (d.warnings || 0) + (d.severes || 0)),
                        borderColor: 'rgb(255, 255, 255)',
                        fill: false,
                        borderWidth: 2
                    },
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
        };

        if (trendChart instanceof Chart) {
            trendChart.destroy();
        }
        
        trendChart = await createChart(ctx.getContext('2d'), config);
    } catch (error) {
        console.error('Error updating trend chart:', error);
    }
}

// Wait for Chart.js to load before initializing
function initializeCharts() {
    if (typeof Chart === 'undefined') {
        console.log('Waiting for Chart.js to load...');
        setTimeout(initializeCharts, 100);
        return;
    }
    console.log('Chart.js loaded, initializing charts...');
    updateCharts();
}

// Initialize charts when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCharts);
} else {
    initializeCharts();
}
