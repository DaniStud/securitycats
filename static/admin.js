document.getElementById('article_form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const atitle = document.getElementById('atitle').value;
    const article = document.getElementById('article').value;
    const csrf_token = document.getElementById('csrf_token').value;
    const errorDiv = document.getElementById('article_error');
    
    if (!atitle || !article) {
        if (errorDiv) {
            errorDiv.textContent = 'Both title and article content are required!';
        } else {
            alert('Both title and article content are required!');
        }
        return;
    }
    
    if (!csrf_token) {
        if (errorDiv) {
            errorDiv.textContent = 'CSRF token is missing, please reload page';
        } else {
            alert('CSRF token is missing, please reload page');
        }
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
            document.getElementById('atitle').value = '';
            document.getElementById('article').value = '';
            if (errorDiv) errorDiv.textContent = '';
            window.location.reload();
        } else if (result.message.includes('CSRF')) {
            if (errorDiv) {
                errorDiv.textContent = 'Invalid CSRF token. Please reload the page and try again.';
            } else {
                alert('Invalid CSRF token. Please reload the page and try again.');
            }
            setTimeout(() => window.location.reload(), 2000);
        } else {
            if (errorDiv) {
                errorDiv.textContent = result.message || 'Article submission failed';
            } else {
                alert('Article submission failed: ' + result.message);
            }
        }
    } catch (err) {
        if (errorDiv) {
            errorDiv.textContent = 'Network error or server is down.';
        } else {
            alert('Network error or server is down.');
        }
        console.error(err);
    }
});