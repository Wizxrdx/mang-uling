function toggleNotification() {
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          document.getElementById('notifyIcon').textContent = 'notifications_active';
          new Notification("Notifications enabled!");
        }
      });
    } else if (Notification.permission === 'granted') {
      document.getElementById('notifyIcon').textContent = 'notifications_active';
      new Notification("Notifications already enabled!");
    } else {
      alert("Notifications are blocked.");
    }
  }