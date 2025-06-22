document.getElementById('login_form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value;
    const password = document.getElementById('password').value;
    const csrf_token = document.getElementById('csrf_token').value;
    const errorDiv = document.getElementById('login_error');

    // Client-side validation
    if (!name || !password) {
        if (errorDiv) {
            errorDiv.textContent = 'Both username and password are required!';
        } else {
            alert('Both username and password are required!');
        }
        return;
    }

    if (!csrf_token) {
        if (errorDiv) {
            errorDiv.textContent = 'CSRF token is missing. Reloading page...';
        } else {
            alert('CSRF token is missing. Reloading page...');
        }
        setTimeout(() => window.location.reload(), 2000);
        return;
    }

    if (!/^[a-zA-Z0-9_.-]+$/.test(name)) {
        if (errorDiv) {
            errorDiv.textContent = 'Username contains invalid characters';
        } else {
            alert('Username contains invalid characters');
        }
        return;
    }

    try {
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, password, csrf_token })
        });

        const result = await res.json();

        if (result.status === 'success') {
            alert('Login successful!');
            if (result.redirect) {
                window.location.href = result.redirect;
            } else {
                window.location.href = '/';
            }
        } else if (res.status === 403) {
            // Handle CSRF token issues
            if (errorDiv) {
                errorDiv.textContent = result.message + ' Reloading page...';
            } else {
                alert(result.message + ' Reloading page...');
            }
            setTimeout(() => window.location.reload(), 2000);
        } else {
            if (errorDiv) {
                errorDiv.textContent = result.message || 'Login failed';
            } else {
                alert(result.message || 'Login failed');
            }
        }
    } catch (err) {
        const errorMessage = 'Network error or server is down.';
        if (errorDiv) {
            errorDiv.textContent = errorMessage;
        } else {
            alert(errorMessage);
        }
        console.error(err);
    }
});

document.getElementById('signup_form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('signup_name').value;
    const password = document.getElementById('signup_password').value;
    const role = document.getElementById('role').value;
    const csrf_token = document.getElementById('csrf_token').value;
    const errorDiv = document.getElementById('signup_error');

    // Client-side validation
    if (!name || !password || !role) {
        if (errorDiv) {
            errorDiv.textContent = 'All fields are required!';
        } else {
            alert('All fields are required!');
        }
        return;
    }

    if (!csrf_token) {
        if (errorDiv) {
            errorDiv.textContent = 'CSRF token is missing. Reloading page...';
        } else {
            alert('CSRF token is missing. Reloading page...');
        }
        setTimeout(() => window.location.reload(), 2000);
        return;
    }

    if (!/^[a-zA-Z0-9_.-]+$/.test(name)) {
        if (errorDiv) {
            errorDiv.textContent = 'Username contains invalid characters';
        } else {
            alert('Username contains invalid characters');
        }
        return;
    }

    if (password.length < 12 || !/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/[0-9]/.test(password) || !/[^a-zA-Z0-9]/.test(password)) {
        if (errorDiv) {
            errorDiv.textContent = 'Password must be at least 12 characters with upper, lower, digit, and special character';
        } else {
            alert('Password must be at least 12 characters with upper, lower, digit, and special character');
        }
        return;
    }

    try {
        const res = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, password, role, csrf_token })
        });

        const result = await res.json();

        if (result.status === 'success') {
            alert('Signup successful! Please login.');
            window.location.href = '/login_page';
        } else if (res.status === 403) {
            if (errorDiv) {
                errorDiv.textContent = result.message + ' Reloading page...';
            } else {
                alert(result.message + ' Reloading page...');
            }
            setTimeout(() => window.location.reload(), 2000);
        } else {
            if (errorDiv) {
                errorDiv.textContent = result.message || 'Signup failed';
            } else {
                alert(result.message || 'Signup failed');
            }
        }
    } catch (err) {
        const errorMessage = 'Network error or server is down.';
        if (errorDiv) {
            errorDiv.textContent = errorMessage;
        } else {
            alert(errorMessage);
        }
        console.error(err);
    }
});