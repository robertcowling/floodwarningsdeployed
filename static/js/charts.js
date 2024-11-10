// Chart.js configuration and setup
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
Chart.defaults.font.size = 13;
Chart.defaults.color = '#333333';

let currentChart = null;
let trendChart = null;
let selectedTimeRange = 3; // Default to 3 days

// Initialize time range selector
document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('timeRangeSelector');
    if (selector) {
        selector.addEventListener('change', (e) => {
            selectedTimeRange = parseInt(e.target.value);
            updateCharts();
        });
    }
});

// Update charts every minute
setInterval(updateCharts, 60000);

async function updateCharts() {
    try {
        console.log('Starting chart updates...');
        showLoading();
        await Promise.all([
            updateCurrentChart(),
            updateTrendChart()
        ]);
        hideLoading();
        console.log('Charts updated successfully');
    } catch (error) {
        console.error('Error updating charts:', error);
        hideLoading();
    }
}

function showLoading() {
    document.querySelectorAll('.chart-container').forEach(container => {
        container.classList.add('loading');
    });
}

function hideLoading() {
    document.querySelectorAll('.chart-container').forEach(container => {
        container.classList.remove('loading');
    });
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

        // Update last updated timestamp
        const lastUpdated = document.getElementById('lastUpdated');
        if (lastUpdated) {
            const date = new Date(data.timestamp);
            lastUpdated.textContent = `Last updated: ${date.toLocaleString()}`;
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
                        'rgba(255, 193, 7, 0.8)',  // Yellow for alerts
                        'rgba(255, 87, 34, 0.8)',  // Orange for warnings
                        'rgba(244, 67, 54, 0.8)'   // Red for severe
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
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.raw}`;
                            }
                        }
                    }
                },
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
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - selectedTimeRange);
        
        const response = await fetch(`/api/historical?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`);
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
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        });

        const config = {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: 'Alerts',
                        data: data.map(d => d.alerts || 0),
                        borderColor: 'rgb(255, 193, 7)',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        fill: true
                    },
                    {
                        label: 'Warnings',
                        data: data.map(d => d.warnings || 0),
                        borderColor: 'rgb(255, 87, 34)',
                        backgroundColor: 'rgba(255, 87, 34, 0.1)',
                        fill: true
                    },
                    {
                        label: 'Severe',
                        data: data.map(d => d.severes || 0),
                        borderColor: 'rgb(244, 67, 54)',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    tooltip: {
                        position: 'nearest'
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 8
                        }
                    },
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

// Initialize charts when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateCharts);
} else {
    updateCharts();
}
