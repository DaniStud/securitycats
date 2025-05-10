const url = 'http://localhost:5000';

document.body.onload = fetchArticles;

async function fetchArticles() {
    try {
        const response = await fetch(`${url}/get_articles`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            const article_section = document.getElementById("articles");

            result.data.forEach(article =>{
                const articleDiv = document.createElement("div");
                articleDiv.className = "singleArticle"

                articleDiv.innerHTML = `
                <div class="articleWrapper"> 
                <div class="articleTitle">Title: ${article.title}</div>
                <div class="articleContent">Content: ${article.article}</div>
                <a href="${url}/${article.article_id}">Security Cats</a>
                </div>
                `

                article_section.appendChild(articleDiv);

            });


        } else {
            console.error('Error fetching articles:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}