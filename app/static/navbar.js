document.addEventListener("DOMContentLoaded", function () {
    const navToggle = document.querySelector(".nav-toggle");
    const navMenu = document.querySelector("nav ul");

    navToggle.addEventListener("click", function () {
        navMenu.classList.toggle("show");
    });
});

function replaceWithContent(selector, url) {
    $.get(url, function(data) {
        $(selector).replaceWith(data);
    });
}

let notifyInterval = null;

function toggleNotification() {
  const icon = document.getElementById('notifyIcon');

  if (Notification.permission === 'default') {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        icon.textContent = 'notifications_active';
        new Notification("Notifications enabled!");
        startPolling();
      } else {
        alert("Notifications are blocked or denied.");
      }
    });
  } else if (Notification.permission === 'granted') {
    icon.textContent = 'notifications_active';
    new Notification("Notifications already enabled!");
    startPolling();
  } else {
    alert("Notifications are blocked.");
  }
}

function startPolling() {
  if (notifyInterval) return; // Already polling

  notifyInterval = setInterval(() => {
    fetch('/api/notify')
      .then(response => response.json())
      .then(data => {
        if (data.message) {
          new Notification("Packing Done", { body: data.message });
        }
      })
      .catch(error => {
        console.error("Notification polling failed:", error);
      });
  }, 3000); // Poll every 3 seconds
}

document.getElementById('loadProfile').addEventListener('click', function() {
    // Fetch the profile content using an API call
    fetch('/profile')
        .then(response => response.text())
        .then(html => {
            // Insert the HTML content into the modal body
            $('#profileModal').replaceWith(html);
            
            // Now show the modal after the content is fetched and inserted
            var profileModal = new bootstrap.Modal(document.getElementById('profileModal'));
            profileModal.show();
        })
        .catch(error => {
            console.error('Error fetching profile content:', error);
        });
});

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('saveChanges')?.addEventListener('click', function() {
        var newName = document.getElementById('newName').value;
        var newPassword = document.getElementById('newPassword').value;

        console.log('New Name:', newName);
        console.log('New Password:', newPassword);

        document.getElementById('newName').value = '';
        document.getElementById('newPassword').value = '';

        var modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
        modal.hide();
    });
});