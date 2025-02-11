document.addEventListener("DOMContentLoaded", function () {
    const navToggle = document.querySelector(".nav-toggle");
    const navClose = document.querySelector(".nav-close");
    const navMenu = document.querySelector("nav ul");

    navToggle.addEventListener("click", function () {
        navMenu.classList.toggle("show");
    });
    navClose.addEventListener("click", function () {
        navMenu.classList.toggle("show");
    });
});

function replaceWithContent(selector, url) {
    $.get(url, function(data) {
        $(selector).replaceWith(data);
    });
}

$(document).ready(function() {
    replaceWithContent("#status", "/status");
    replaceWithContent("#count", "/count");
    replaceWithContent("#quota", "/quota");

    // var refreshId = setInterval(function() {
    //     replaceWithContent("#status", "/status");
    //     replaceWithContent("#count", "/count");
    //     replaceWithContent("#quota", "/quota");
    // }, 3000);
});