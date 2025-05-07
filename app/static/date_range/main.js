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

// Initialize chart variable
let myChart = null;

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
    const chartContainer = document.getElementById('myChart');
    chartContainer.style.opacity = '0.5';

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
        // Destroy existing chart if it exists
        if (myChart) {
            myChart.destroy();
        }

        // Create new chart
        const ctx = document.getElementById('myChart').getContext('2d');
        myChart = new Chart(ctx, {
            type: 'line',
            data: data,
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
                            text: 'Number of Bags'
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
                        text: 'Production Data by Date Range'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });

        // Reset loading state
        chartContainer.style.opacity = '1';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error fetching data. Please try again.');
        chartContainer.style.opacity = '1';
    });
} 