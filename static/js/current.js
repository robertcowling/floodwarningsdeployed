let currentChart = null;

function updateCurrentChart() {
    fetch('/api/current')
        .then(response => response.json())
        .then(data => {
            // Update table counts
            document.getElementById('severeCount').textContent = data.severes;
            document.getElementById('warningCount').textContent = data.warnings;
            document.getElementById('alertCount').textContent = data.alerts;

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

            const ctx = document.getElementById('currentChart').getContext('2d');
            currentChart = new Chart(ctx, config);
        })
        .catch(error => console.error('Error fetching current data:', error));
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    updateCurrentChart();
    // Update every minute
    setInterval(updateCurrentChart, 60000);
});
