// Initialize trend chart
let trendChart = null;

// Function to show loading state
function showLoading() {
    const canvas = document.getElementById('trendChart');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'chartLoading';
    loadingDiv.className = 'position-absolute top-50 start-50 translate-middle text-center';
    loadingDiv.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <div class="mt-2">Loading data...</div>
    `;
    canvas.parentElement.style.position = 'relative';
    canvas.parentElement.appendChild(loadingDiv);
    canvas.style.opacity = '0.5';
}

function hideLoading() {
    const loadingDiv = document.getElementById('chartLoading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
    document.getElementById('trendChart').style.opacity = '1';
}

// Function to update chart based on selected time period
async function updateTrendChart() {
    const timeRange = document.getElementById('timeRange').value;
    const endDate = new Date();
    let startDate = new Date();

    // Calculate start date based on selected range
    switch(timeRange) {
        case '48h':
            startDate.setHours(startDate.getHours() - 48);
            break;
        case '7d':
            startDate.setDate(startDate.getDate() - 7);
            break;
        case '30d':
            startDate.setDate(startDate.getDate() - 30);
            break;
        default: // 24h
            startDate.setHours(startDate.getHours() - 24);
    }

    // Format dates for API
    const formattedStartDate = startDate.toISOString().split('T')[0];
    const formattedEndDate = endDate.toISOString().split('T')[0];

    try {
        showLoading();
        const response = await fetch(`/api/historical?start_date=${formattedStartDate}&end_date=${formattedEndDate}`);
        const data = await response.json();
        
        const timestamps = data.map(d => {
            const date = new Date(d.timestamp);
            return date.toLocaleDateString('en-GB', {
                weekday: 'short',
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }).replace(',', '');
        });

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
                        data: data.map(d => d.alerts || 0),
                        borderColor: 'rgb(255, 193, 7)',
                        fill: false
                    },
                    {
                        label: 'Warnings',
                        data: data.map(d => d.warnings || 0),
                        borderColor: 'rgb(255, 87, 34)',
                        fill: false
                    },
                    {
                        label: 'Severe',
                        data: data.map(d => d.severes || 0),
                        borderColor: 'rgb(244, 67, 54)',
                        fill: false
                    }
                ]
            },
            options: {
                animation: false, // Disable animations for better performance
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    decimation: {
                        enabled: true,
                        algorithm: 'min-max'
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

        const ctx = document.getElementById('trendChart').getContext('2d');
        trendChart = new Chart(ctx, config);
    } catch (error) {
        console.error('Error fetching trend data:', error);
    } finally {
        hideLoading();
    }
}

// Update chart when time range changes
document.getElementById('timeRange').addEventListener('change', updateTrendChart);

// Initial chart load
document.addEventListener('DOMContentLoaded', () => {
    updateTrendChart();
    // Update every minute
    setInterval(updateTrendChart, 60000);
});
