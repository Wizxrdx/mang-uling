// Set the dimensions and margins of the graph
const margin = { top: 5, right: 20, bottom: 70, left: 50 },
      width = 350 - margin.left - margin.right,
      height = 200 - margin.top - margin.bottom;

// Define the data
const data = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    values: [500, 500, 500, 500],
};

// Append the SVG object to the body of the page
const svg = d3.select("#my_dataviz")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

// X axis
const x = d3.scaleBand()
    .range([0, width])
    .domain(data.labels)
    .padding(0.2);

svg.append("g")
    .attr("transform", `translate(0, ${height})`)
    .call(d3.axisBottom(x))
    .selectAll("text")
    .attr("transform", "translate(-10,0)rotate(-45)")
    .style("text-anchor", "end");

// Y axis
const y = d3.scaleLinear()
    .domain([0, d3.max(data.values) + 100]) // Adjust domain based on data
    .range([height, 0]);

svg.append("g")
    .call(d3.axisLeft(y));

// Bars
svg.selectAll("mybar")
    .data(data.labels.map((label, i) => ({ label, value: data.values[i] }))) // Combine labels and values
    .join("rect")
    .attr("x", d => x(d.label))
    .attr("y", d => y(d.value))
    .attr("width", x.bandwidth())
    .attr("height", d => height - y(d.value))
    .attr("fill", "#FF5C00");
