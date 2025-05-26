document.getElementById('article_form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const atitle = document.getElementById('atitle').value;
    const article = document.getElementById('article').value;
    const csrf_token = document.getElementById('csrf_token').value;
    
    if (!atitle || !article) {
        alert('Both title and article content are required!');
        return;
    }
    
    if (!csrf_token) {
        alert('CSRF token is missing, please reload page');
        return;
    }
   
    try {
        const res = await fetch('/submit_article', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ atitle, article, csrf_token })
        });
        
        const result = await res.json();
        console.log(result);
        
        if (result.status === 'success') {
            alert('Article submitted successfully!');
            // Clear the form
            document.getElementById('atitle').value = '';
            document.getElementById('article').value = '';
            // Optionally reload page to get new CSRF token
            window.location.reload();
        } else if (result.message === 'Invalid CSRF token') {
            alert('Invalid CSRF token. Please reload the page and try again.');
            window.location.reload();
        } else {
            alert('Article submission failed: ' + result.message);
        }
    } catch (err) {
        alert('Network error or server is down.');
        console.error(err);
    }
});