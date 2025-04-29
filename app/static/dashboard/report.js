document.addEventListener("DOMContentLoaded", function () {
    const modal = new bootstrap.Modal(document.getElementById("weekSelectionModal"));
    const weekContainer = document.getElementById("week-container");
    const addWeekBtn = document.getElementById("add-week");
    const downloadCheckbox = document.getElementById("download-checkbox");
    const openButton = document.getElementById("fetch-log");

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

    function getDateRangeOfWeek(weekNo){
        var d1 = new Date();
        numOfdaysPastSinceLastMonday = eval(d1.getDay()- 1);
        d1.setDate(d1.getDate() - numOfdaysPastSinceLastMonday);
        var weekNoToday = d1.getWeek();
        var weeksInTheFuture = eval( weekNo - weekNoToday );
        d1.setDate(d1.getDate() + eval( 7 * weeksInTheFuture ));
        var rangeIsFrom = eval(d1.getMonth()+1) +"/" + d1.getDate() + "/" + d1.getFullYear();
        d1.setDate(d1.getDate() + 6);
        var rangeIsTo = eval(d1.getMonth()+1) +"/" + d1.getDate() + "/" + d1.getFullYear() ;
        return rangeIsFrom + " to "+rangeIsTo;
    };

    function formatWeekLabel(weekValue) {
        if (!weekValue) return "Invalid Week";
    
        let [year, week] = weekValue.split("-W");

        const startOfWeek = getStartOfISOWeek(year, week);
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        
        const options = { month: "long", day: "numeric" };
        return `${startOfWeek.toLocaleDateString(undefined, options)} – ${endOfWeek.toLocaleDateString(undefined, options)}, ${year}`;
    }

    function getStartOfISOWeek(year, weekNumber) {
        const simpleDate = new Date(year, 0, 1 + (weekNumber - 1) * 7); // Start with first day of the year, adjusted by week number
        const dayOfWeek = simpleDate.getDay(); // Get the day of the week (0 is Sunday, 1 is Monday, etc.)
        
        // Adjust to the previous Monday (ISO weeks start on Monday)
        const date = simpleDate.getDate() - dayOfWeek + (dayOfWeek == 0 ? -6 : 1); // if Sunday, subtract 6, else subtract the day of the week - 1
        
        return new Date(simpleDate.setDate(date)); // Set the adjusted date and return it
    }

    // Function to get week number of a date
    function getWeekNumber(date) {
        let temp = new Date(date);
        temp.setHours(0, 0, 0, 0);
        temp.setDate(temp.getDate() + 4 - (temp.getDay() || 7));
        let yearStart = new Date(temp.getFullYear(), 0, 1);
        return Math.ceil((((temp - yearStart) / 86400000) + 1) / 7);
    }
});
