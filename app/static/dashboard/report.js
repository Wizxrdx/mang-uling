document.addEventListener("DOMContentLoaded", function () {
    const modal = new bootstrap.Modal(document.getElementById("weekSelectionModal"));
    const weekContainer = document.getElementById("week-container");
    const addWeekBtn = document.getElementById("add-week");
    const openWeekBtn = document.getElementById("open-week-data");
    const downloadCheckbox = document.getElementById("download-checkbox");

    // Open Modal
    document.getElementById("open-week-modal").addEventListener("click", function () {
        modal.show();
    });

    // Add a new week input field
    addWeekBtn.addEventListener("click", function () {
        addWeekEntry("");
    });

    // Remove a week input field
    weekContainer.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-week")) {
            event.target.closest(".week-entry").remove();
        }
    });

    // Quick-select buttons for "This Month" and "Last Month"
    document.querySelectorAll(".quick-select").forEach(button => {
        button.addEventListener("click", function () {
            const type = this.getAttribute("data-type");
            populateWeeks(type);
        });
    });

    function populateWeeks(type) {
        let today = new Date();
        let start, end;

        if (type === "this-month") {
            start = new Date(today.getFullYear(), today.getMonth(), 1);
            end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        } else if (type === "last-month") {
            start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            end = new Date(today.getFullYear(), today.getMonth(), 0);
        }

        let weeks = getWeeksBetween(start, end);
        weekContainer.innerHTML = ""; // Reset

        weeks.forEach(week => addWeekEntry(week));
    }

    function addWeekEntry(weekValue) {
        let formattedWeek = formatWeekLabel(weekValue);
    
        const weekEntry = document.createElement("div");
        weekEntry.classList.add("week-entry", "mt-2");
    
        weekEntry.innerHTML = `
            <div class="row">
                <div class="col-6 d-flex align-items-center">
                    <label class="week-label">${formattedWeek}</label>
                </div>
                <div class="col-6 d-flex justify-content-end">
                    <input type="week" class="form-control form-control-sm week-input" value="${weekValue}" style="max-width: 120px;">
                </div>
            </div>
            <div class="row mt-1">
                <div class="col">
                    <button type="button" class="btn btn-danger w-100 remove-week">Remove</button>
                </div>
            </div>
        `;
    
        weekContainer.appendChild(weekEntry);
    
        // Add event listener to update label when the week input changes
        const weekInput = weekEntry.querySelector(".week-input");
        const weekLabel = weekEntry.querySelector(".week-label");
    
        weekInput.addEventListener("change", function () {
            weekLabel.textContent = formatWeekLabel(weekInput.value);
        });
    
        // Auto-focus so user can select a week immediately
        weekInput.focus();
    }

    // Function to get all weeks between two dates
    function getWeeksBetween(start, end) {
        let weeks = [];
        let tempDate = new Date(start);

        while (tempDate <= end) {
            let year = tempDate.getFullYear();
            let week = getWeekNumber(tempDate);
            weeks.push(`${year}-W${String(week).padStart(2, "0")}`);
            tempDate.setDate(tempDate.getDate() + 7);
        }

        return weeks;
    }

    function formatWeekLabel(weekValue) {
        if (!weekValue) return "Invalid Week";
    
        let [year, week] = weekValue.split("-W");
        let date = new Date(year, 0, (week - 1) * 7 + 1); // Get first day of the week
    
        let month = date.toLocaleDateString("en-US", { month: "long" }); // Get month name
        let weekNumber = getReadableWeekOfMonth(date); // Get 1st, 2nd, 3rd week
    
        return `${weekNumber}, ${year}`;
    }

    // Function to get week number of a date
    function getWeekNumber(date) {
        let temp = new Date(date);
        temp.setHours(0, 0, 0, 0);
        temp.setDate(temp.getDate() + 4 - (temp.getDay() || 7));
        let yearStart = new Date(temp.getFullYear(), 0, 1);
        return Math.ceil((((temp - yearStart) / 86400000) + 1) / 7);
    }

    // Handle Open button click (resets the modal)
    openWeekBtn.addEventListener("click", function () {
        let selectedWeeks = Array.from(document.querySelectorAll(".week-input"))
            .map(input => input.value)
            .filter(value => value !== "");

        console.log("Selected Weeks:", selectedWeeks);
        console.log("Download:", downloadCheckbox.checked ? "Yes" : "No");

        modal.hide();
        weekContainer.innerHTML = ""; // Reset selection
        addWeekEntry(""); // Add one default input
        downloadCheckbox.checked = false;
    });
});

function getReadableWeekOfMonth(date) {
    const day = date.getDate();
    
    const start = new Date(date);
    start.setDate(day - date.getDay() + 1); // Monday (adjusted for Sunday as the start of the week)
    const end = new Date(start);
    end.setDate(start.getDate() + 6); // Sunday

    const options = { month: "long", day: "numeric" };
    return `${start.toLocaleDateString(undefined, options)} – ${end.toLocaleDateString(undefined, options)}`;
}

document.addEventListener("DOMContentLoaded", function () {
    const openButton = document.getElementById("fetch-log");
    const downloadCheckbox = document.getElementById("download-checkbox");

    openButton.addEventListener("click", function () {
        let weeks = [];
        document.querySelectorAll(".week-input").forEach(input => {
            if (input.value) weeks.push(input.value);
        });

        if (weeks.length === 0) {
            alert("Please select at least one week.");
            return;
        }

        fetch("/generate_pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ weeks: weeks })
        })
        .then(response => response.blob())
        .then(blob => {
            const pdfUrl = URL.createObjectURL(blob);
            
            // Open PDF in a new tab
            window.open(pdfUrl, "_blank");

            // Download if checkbox is checked
            if (downloadCheckbox.checked) {
                const a = document.createElement("a");
                a.href = pdfUrl;
                a.download = "log_report.pdf";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }
        })
        .catch(error => console.error("Error:", error));
    });
});
