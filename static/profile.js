document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.getElementById('profile_form');
    if (!profileForm) {
        console.error('Profile form not found');
        return;
    }

    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData();
        const csrfTokenElement = document.getElementById('csrf_token');
        if (!csrfTokenElement) {
            console.error('CSRF token element not found');
            document.getElementById('profile_error').textContent = 'CSRF token missing. Please reload the page.';
            return;
        }
        formData.append('csrf_token', csrfTokenElement.value);
        console.log('CSRF Token:', csrfTokenElement.value); // Debug log

        const profilePic = document.getElementById('profile_pic').files[0];
        if (profilePic) {
            formData.append('profile_pic', profilePic);
        }
        formData.append('bio', document.getElementById('bio').value);
        const country = document.getElementById('country').value;
        formData.append('country', country);
        console.log('Country:', country); // Debug log
        // Ensure country_visible is always sent (0 or 1)
        const countryVisible = document.getElementById('country_visible').checked ? 'on' : 'off';
        formData.append('country_visible', countryVisible);
        console.log('Country Visible:', countryVisible); // Debug log

        try {
            const res = await fetch('/update_profile', {
                method: 'POST',
                body: formData
            });

            const result = await res.json();
            console.log('Server Response:', result); // Debug log

            const errorDiv = document.getElementById('profile_error');
            if (!errorDiv) {
                console.error('Profile error div not found');
                alert(result.message || 'Update failed');
                return;
            }
            if (result.status === 'success') {
                alert('Profile updated successfully!');
                errorDiv.textContent = '';
                // Reload to reflect changes in preview
                location.reload();
            } else {
                errorDiv.textContent = result.message || 'Update failed';
            }
        } catch (err) {
            console.error('Error:', err);
            document.getElementById('profile_error').textContent = 'Network error or server is down.';
        }
    });
});