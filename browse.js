const DBurl = 'http://localhost:5000';
const url = 'http://localhost:5500';

document.body.onload = fetchArticles;

async function fetchArticles() {
    try {
        const response = await fetch(`${DBurl}/get_articles`);
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
                <a id="readbtn" href="${url}/article.html/${article.article_id}">Security Cats</a>
                </div>
                `

                article_section.appendChild(articleDiv);
                displayNone();
            });


        } else {
            console.error('Error fetching articles:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}



// async function displayNone() {
//     const readButton = document.getElementById("readbtn");
//     if (readButton) {
//         readButton.style.border = "2px solid black";
//     }
// }

async function displayNone() {
    const readButton = document.getElementById("readbtn");
    if (readButton) {
        readButton.style.border = "2px solid black";
    }
}

async function fetchArticleById(articleId) {
    try {
        // Fetch the article with the given ID
        const response = await fetch(`${DBurl}/get_article/${articleId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            console.log('Article:', result.data); // Log the article to the console
        } else {
            console.error('Error fetching article:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
}
}

// Call the function to fetch and log the article with ID 1
fetchArticleById(2);
