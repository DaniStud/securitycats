document.getElementById('login_form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value;
    const password = document.getElementById('password').value;
    const csrf_token = document.getElementById('csrf_token').value;

    if (!name || !password) {
        alert('Both fields are required!');
        return;
    }

    if (!csrf_token){
        alert('CSRF token is missing, please reload page');
        return;
    }
    

    try {
const res = await fetch('/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name, password, csrf_token })
});

        const result = await res.json();
        console.log(result);

if (result.status === 'success') {
            alert('Login successful!');
            window.location.href = '/admin';
        } else if (result.message === 'Invalid CSRF token') {
            alert('Invalid CSRF token. Please reload the page and try again.');
        } else {
            alert('Login failed: ' + result.message);
        }
    } catch (err) {
        alert('Network error or server is down.');
        console.error(err);
    }
});
