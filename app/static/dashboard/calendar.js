// Initialize Flatpickr for a single month calendar selection
flatpickr("#datepicker", {
    mode: "range",         // Enables range selection (start and end dates)
    dateFormat: "Y-m-d",   // Format for the selected date
    inline: true,          // Displays the calendar inline (no dropdown)
    showMonths: 1,         // Show only 1 month
});

// Function to handle date range selection and plot data
function submitRange() {
    const range = document.getElementById("datepicker").value;
    if (!range) {
        alert("Please select a date range.");
        return;
    }
    alert("Selected range: " + range);
    
    // Parse the start and end dates from the selected range
    const [startDate, endDate] = range.split(' to ').map(date => moment(date));

    // Generate dummy data for the graph based on the date range
    const data = generateData(startDate, endDate);

    // Call the function to plot the graph with the fetched data
    plotGraph(data);
}

// Function to generate dummy data for the graph
function generateData(startDate, endDate) {
    let data = [];
    let labels = [];
    let currentDate = startDate;

    // Generate data for each date in the range
    while (currentDate.isBefore(endDate) || currentDate.isSame(endDate, 'day')) {
        labels.push(currentDate.format('YYYY-MM-DD'));
        data.push(Math.floor(Math.random() * 100) + 1);  // Simulate random data
        currentDate.add(1, 'days');
    }

    return { labels: labels, data: data };
}

// Function to plot the graph using Chart.js
function plotGraph(data) {
    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Data for Selected Range',
                data: data.data,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                fill: true,
            }]
        },
        options: {
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    min: 0
                }
            }
        }
    });
}