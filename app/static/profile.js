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

            // Add event listener after modal is loaded
            document.getElementById('saveChanges').addEventListener('click', async function() {
                const newName = document.getElementById('newName').value;
                const newPassword = document.getElementById('newPassword').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                if (!newName && !newPassword) {
                    alert('Please enter either a new name or password');
                    return;
                }

                if (newPassword) {
                    if (newPassword.length < 6) {
                        alert('Password must be at least 6 characters long');
                        return;
                    }

                    if (newPassword !== confirmPassword) {
                        alert('Passwords do not match');
                        return;
                    }
                }
                
                try {
                    const response = await fetch('/update-profile', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            name: newName,
                            password: newPassword
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        alert('Profile updated successfully!');
                        // Close the modal
                        const modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
                        if (modal) {
                            modal.hide();
                        }
                        // Clear the form
                        document.getElementById('newName').value = '';
                        document.getElementById('newPassword').value = '';
                        document.getElementById('confirmPassword').value = '';
                        // Reload the page to show updated name
                        location.reload();
                    } else {
                        alert(data.message || 'Failed to update profile');
                    }
                } catch (error) {
                    alert('An error occurred while updating profile');
                    console.error('Error:', error);
                }
            });
        })
        .catch(error => {
            console.error('Error fetching profile content:', error);
        });
});
