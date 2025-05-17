document.getElementById('login_form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value;
    const password = document.getElementById('password').value;

    if (!name || !password) {
        alert('Both fields are required!');
        return;
    }

    try {
const res = await fetch('/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name, password })
});

        const result = await res.json();
        console.log(result);

        if (result.status === 'success') {
            alert('Login successful!');
            // Optional: redirect to admin or dashboard
            window.location.href = '/admin';
        } else {
            alert('Login failed: ' + result.message);
        }
    } catch (err) {
        alert('Network error or server is down.');
        console.error(err);
    }
});
