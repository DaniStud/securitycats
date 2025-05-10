document.body.onload = fetchArticles;

// async function fetchArticles() {
//     try {
//         // Fetch articles from the backend
//         const response = await fetch('http://localhost:5000/get_articles');
//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }
//         const result = await response.json();

//         if (result.status === 'success') {
//             console.log('Articles:', result.data); // Log the articles to the console
//         } else {
//             console.error('Error fetching articles:', result.message);
//         }
//     } catch (error) {
//         console.error('Error:', error);
//     }
// }


async function fetchArticles() {
    try {
        // Fetch articles from the backend
        const response = await fetch('http://localhost:5000/get_articles');
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