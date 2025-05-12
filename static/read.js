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


async function fetchArticleComments() {
    try {
        // Extract the article ID from the URL
        const pathSegments = window.location.pathname.split('/');
        const articleId = pathSegments[pathSegments.length - 1];

        if (!articleId) {
            console.error('Article ID not found in URL');
            return;
        }

        // Make a GET request to the Flask endpoint
        const response = await fetch(`${DBurl}/get_article/${articleId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Parse the JSON response
        const data = await response.json();

        // Check if the request was successful
        if (data.status === 'success') {
            // Log the comments to the console
            console.log('Comments:', data.data.comments);
            insertCommentsIntoPage(data.data.comments);
        } else {
            console.error('Error:', data.message);
        }
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

// Execute the function to fetch comments based on the actual article ID
fetchArticleComments();

// Function to insert the article into the HTML
function insertCommentsIntoPage(posted_comments) {
    const section = document.getElementById("posted_comments");
    section.innerHTML = `
        <div id="comments_wrapper">
            ${posted_comments.map(comment => `
                <div class="comment">
                    <p>${comment.content}</p> 
                </div>
            `).join('')}
        </div>
    `;
}


    /// comment form submit
    document.getElementById('comment_form').addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default form submission

        // Grab the form data (article title)
        const article = document.getElementById('comment').value
        if (!comment) {
        alert('Comment empty!');
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