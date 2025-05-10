document.body.onload = fetchArticles;

async function fetchArticles() {
    try {
        // Fetch articles from the backend
        const response = await fetch('http://localhost:5000/get_articles');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            console.log('Articles:', result.data); // Log the articles to the console
        } else {
            console.error('Error fetching articles:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}