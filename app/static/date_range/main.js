// Initialize Flatpickr for date range selection
const datepicker = flatpickr("#datepicker", {
    mode: "range",
    dateFormat: "Y-m-d",
    maxDate: "today",
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
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Destroy existing charts if they exist
        if (chart1kg) {
            chart1kg.destroy();
        }
        if (chart5kg) {
            chart5kg.destroy();
        }

        // Create 1kg chart
        const ctx1kg = document.getElementById('chart1kg').getContext('2d');
        chart1kg = new Chart(ctx1kg, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: '1kg Production',
                        data: data.datasets[0].data,
                        borderColor: 'rgb(75, 192, 192)',  // Teal for actual
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: '1kg Forecast',
                        data: data.datasets[0].forecast,
                        borderColor: 'rgb(255, 159, 64)',  // Orange for forecast
                        borderDash: [5, 5],
                        fill: false,
                        borderWidth: 2
                    }
                ]
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
        const ctx5kg = document.getElementById('chart5kg').getContext('2d');
        chart5kg = new Chart(ctx5kg, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: '5kg Production',
                        data: data.datasets[1].data,
                        borderColor: 'rgb(54, 162, 235)',  // Blue for actual
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: '5kg Forecast',
                        data: data.datasets[1].forecast,
                        borderColor: 'rgb(153, 102, 255)',  // Purple for forecast
                        borderDash: [5, 5],
                        fill: false,
                        borderWidth: 2
                    }
                ]
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