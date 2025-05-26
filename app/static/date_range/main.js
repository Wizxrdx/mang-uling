// Initialize Flatpickr for date range selection
const today = new Date();
const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
lastDayOfMonth.setHours(23, 59, 59, 999);

const datepicker = flatpickr("#datepicker", {
    mode: "range",
    dateFormat: "Y-m-d",
    showMonths: 2,
    maxDate: lastDayOfMonth,
    defaultDate: "today",
    disableMobile: true,
    enableTime: false,
    time_24hr: true,
    onChange: function(selectedDates, dateStr, instance) {
        if (selectedDates.length === 2) {
            submitRange();
        }
    }
});

// Initialize chart variables
let chart1kg = null;
let chart5kg = null;

// Function to submit the date range and fetch data
function submitRange() {
    const selectedDates = datepicker.selectedDates;
    if (selectedDates.length !== 2) {
        alert('Please select a date range');
        return;
    }

    const startDate = selectedDates[0].toISOString().split('T')[0];
    const endDate = selectedDates[1].toISOString().split('T')[0];

    // Show loading state
    const chartContainer1kg = document.getElementById('chart1kg');
    const chartContainer5kg = document.getElementById('chart5kg');
    chartContainer1kg.style.opacity = '0.5';
    chartContainer5kg.style.opacity = '0.5';

    // Fetch data from the server
    fetch('/date-range-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            start_date: startDate,
            end_date: endDate
        })
    })
    .then(response => response.json())
    .then(data => {
        // Destroy existing charts if they exist
        if (chart1kg) chart1kg.destroy();
        if (chart5kg) chart5kg.destroy();

        // Create new charts
        const ctx1kg = document.getElementById('chart1kg').getContext('2d');
        const ctx5kg = document.getElementById('chart5kg').getContext('2d');

        // Create 1kg chart
        chart1kg = new Chart(ctx1kg, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Actual Production',
                    data: data.datasets[0].data,
                    borderColor: 'rgb(255, 80, 0)',
                    backgroundColor: 'rgba(255, 80, 0, 0.2)',
                    fill: true,
                }, {
                    label: 'Forecast',
                    data: data.datasets[0].forecast,
                    borderColor: 'rgb(0, 128, 255)',
                    backgroundColor: 'rgba(0, 128, 255, 0.2)',
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of 1kg Bags'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '1kg Bag Production and Forecast'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });

        // Create 5kg chart
        chart5kg = new Chart(ctx5kg, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Actual Production',
                    data: data.datasets[1].data,
                    borderColor: 'rgb(255, 80, 0)',
                    backgroundColor: 'rgba(255, 80, 0, 0.2)',
                    fill: true,
                }, {
                    label: 'Forecast',
                    data: data.datasets[1].forecast,
                    borderColor: 'rgb(0, 128, 255)',
                    backgroundColor: 'rgba(0, 128, 255, 0.2)',
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of 5kg Bags'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: '5kg Bag Production and Forecast'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });

        // Reset loading state
        chartContainer1kg.style.opacity = '1';
        chartContainer5kg.style.opacity = '1';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error fetching data. Please try again.');
        chartContainer1kg.style.opacity = '1';
        chartContainer5kg.style.opacity = '1';
    });
} 