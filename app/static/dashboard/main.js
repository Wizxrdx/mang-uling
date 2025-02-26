function replaceWithContent(selector, url) {
    $.get(url, function(data) {
        $(selector).replaceWith(data);
    });
}

function updateTable() {
    $.getJSON("/log", function (response) {
        let tableBody = $(".table-body table");
        tableBody.find("tr:gt(0)").remove(); // Remove old rows, keep header
        Object.entries(response.data).forEach(([key, value]) => {
            tableBody.append(`
                <tr>
                    <td>${key}</td>
                    <td>${value.bag_1kg} bags</td>
                    <td>${value.bag_10kg} bags</td>
                </tr>
            `);
        });

        $("#week-info").text(`Week: ${response.start_date} - ${response.end_date}`);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const navToggle = document.querySelector(".nav-toggle");
    const navMenu = document.querySelector("nav ul");

    navToggle.addEventListener("click", function () {
        navMenu.classList.toggle("show");
    });
});

$(document).ready(function() {
    replaceWithContent("#status", "/status");
    replaceWithContent("#1kg", "/quota/1kg");
    replaceWithContent("#10kg", "/quota/10kg");
    updateTable();

    var refreshId = setInterval(function() {
        replaceWithContent("#status", "/status");
        replaceWithContent("#1kg", "/quota/1kg");
        replaceWithContent("#10kg", "/quota/10kg");
        updateTable();
    }, 3000);
});

$(document).on("click", "#run-1kg", function () {
    $.ajax({
        url: "/status/1kg",
        type: "PUT",
        success: function (data) {
            replaceWithContent("#status", "/status");
            replaceWithContent("#1kg", "/quota/1kg");
            replaceWithContent("#10kg", "/quota/10kg");
        },
        error: function (xhr, status, error) {
            console.error("Error updating status:", error);
        }
    });
});

$(document).on("click", "#stop-1kg", function () {
    $.ajax({
        url: "/status/stop",
        type: "PUT",
        success: function (data) {
            replaceWithContent("#status", "/status");
            replaceWithContent("#1kg", "/quota/1kg");
            replaceWithContent("#10kg", "/quota/10kg");
        },
        error: function (xhr, status, error) {
            console.error("Error updating status:", error);
        }
    });
});

$(document).on("click", "#edit-1kg", function () {
    let modal = new bootstrap.Modal(document.getElementById("modal-1kg"));
    modal.show();
});

$(document).on("click", "#set-1kg", function () {
    let newValue = $("#modal-input-1kg").val().trim();

    $.ajax({
        url: "/quota/1kg/" + newValue,
        type: "POST",
        success: function (data) {
            console.log(data);
            replaceWithContent("#status", "/status");
            replaceWithContent("#1kg", "/quota/1kg");
            replaceWithContent("#10kg", "/quota/10kg");
            $("#modal-1kg").modal("hide");
        },
        error: function (xhr, status, error) {
            alert("Invalid input. Please enter a valid number.");
        }
    });
});

$(document).on("click", "#run-10kg", function () {
    $.ajax({
        url: "/status/10kg",
        type: "PUT",
        success: function (data) {
            replaceWithContent("#status", "/status");
            replaceWithContent("#1kg", "/quota/1kg");
            replaceWithContent("#10kg", "/quota/10kg");
        },
        error: function (xhr, status, error) {
            console.error("Error updating status:", error);
        }
    });
});

$(document).on("click", "#stop-10kg", function () {
    $.ajax({
        url: "/status/stop",
        type: "PUT",
        success: function (data) {
            replaceWithContent("#status", "/status");
            replaceWithContent("#1kg", "/quota/1kg");
            replaceWithContent("#10kg", "/quota/10kg");
        },
        error: function (xhr, status, error) {
            console.error("Error updating status:", error);
        }
    });
});

$(document).on("click", "#edit-10kg", function () {
    let modal = new bootstrap.Modal(document.getElementById("modal-10kg"));
    modal.show();
});


$(document).on("click", "#set-10kg", function () {
    let newValue = $("#modal-input-10kg").val().trim();

    $.ajax({
        url: "/quota/10kg/" + newValue,
        type: "POST",
        success: function (data) {
            console.log(data);
            replaceWithContent("#status", "/status");
            replaceWithContent("#1kg", "/quota/1kg");
            replaceWithContent("#10kg", "/quota/10kg");
            $("#modal-10kg").modal("hide");
        },
        error: function (xhr, status, error) {
            alert("Invalid input. Please enter a valid number.");
        }
    });
});
