    document.getElementById('articleForm').addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default form submission

        // Grab the form data (article title)
        const atitle = document.getElementById('atitle').value;
        const article = document.getElementById('article').value
        if (!atitle || !article) {
        alert('Both the article title and content are required!');
        return;
    }
        // Send a POST request to the Flask backend
        const res = await fetch('http://localhost:5000/submit_article', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ atitle, article })
        });

        // Handle the server response (optional)
        const result = await res.json();
        console.log(result);

        if (result.status === 'success') {
            alert('Article submitted successfully!');
        } else {
            alert('There was an error submitting the article.');
        }
    });