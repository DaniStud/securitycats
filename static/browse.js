async function fetchArticles() {
    try {
        const response = await fetch('/get_articles');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            const article_section = document.getElementById("articles");
            article_section.innerHTML = ''; // Clear existing articles

            result.data.forEach(article => {
                const articleDiv = document.createElement("div");
                articleDiv.className = "singleArticle";

                articleDiv.innerHTML = `
                <div class="articleWrapper"> 
                    <div class="articleTitle">Title: ${article.title}</div>
                    <div class="articleContent">Content: ${article.article}</div>
                    <a class="readbtn" href="/article/${article.article_id}">Security Cats</a>
                </div>
                `;

                article_section.appendChild(articleDiv);
            });
        } else {
            console.error('Error fetching articles:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function fetchArticleById(articleId) {
    try {
        const response = await fetch(`/get_article/${articleId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            console.log('Article:', result.data);
        } else {
            console.error('Error fetching article:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchArticles();
    // Optional: fetch a specific article for testing
    // fetchArticleById(2);
});