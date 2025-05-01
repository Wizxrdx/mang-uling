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
