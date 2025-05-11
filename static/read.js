const DBurl = 'http://localhost:5000';
const url = 'http://localhost:5500';


// Function to fetch the article by ID and insert it into the page
async function fetchArticleById(articleId) {
    try {
        const response = await fetch(`${DBurl}/get_article/${articleId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            insertArticleIntoPage(result.data);
        } else {
            console.error('Error fetching article:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Function to insert the article into the HTML
function insertArticleIntoPage(article) {
    const section = document.querySelector('section');
    section.innerHTML = `
        <div class="articleWrapper">
            <h1 class="articleTitle">${article.title}</h1>
            <p class="articleContent">${article.article}</p>
        </div>
    `;
}


// Function to fetch and log comments for the current article
async function fetchCommentsForArticle(articleId) {
    try {
        const response = await fetch(`${DBurl}/get_comments/${articleId}`);
        console.log("lorem");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.status === 'success') {
            console.log(`Comments for article ${articleId}:`, result.data);
        } else {
            console.error('Error fetching comments:', result.message);
        }
    } catch (error) {
        console.error('Error fetching comments:', error);
    }
}

