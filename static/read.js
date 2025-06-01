// Removed: const url = 'http://localhost:5500';


// Function to fetch the article by ID and insert it into the page
async function fetchArticleById(articleId) {
    try {
        const response = await fetch(`/get_article/${articleId}`);
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
    const wrapper = document.createElement('div');
    wrapper.className = 'articleWrapper';
    const title = document.createElement('h1');
    title.className = 'articleTitle';
    title.textContent = article.title;
    const content = document.createElement('p');
    content.className = 'articleContent';
    content.textContent = article.article;
    wrapper.appendChild(title);
    wrapper.appendChild(content);
    section.appendChild(wrapper);
}

async function fetchArticleComments() {
    try {
        const pathSegments = window.location.pathname.split('/');
        const articleId = pathSegments[pathSegments.length - 1];

        if (!articleId) {
            console.error('Article ID not found in URL');
            return;
        }

        const response = await fetch(`/get_article/${articleId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.status === 'success') {
            console.log('Comments:', data.data.comments);
            insertCommentsIntoPage(data.data.comments);
        } else {
            console.error('Error:', data.message);
        }
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

fetchArticleComments();

function insertCommentsIntoPage(posted_comments) {
    const section = document.getElementById('posted_comments');
    const wrapper = document.createElement('div');
    wrapper.id = 'comments_wrapper';
    posted_comments.forEach(comment => {
        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment';
        const p = document.createElement('p');
        p.textContent = comment.content;
        commentDiv.appendChild(p);
        wrapper.appendChild(commentDiv);
    });
    section.appendChild(wrapper);
}

document.getElementById('comment_form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const pathSegments = window.location.pathname.split('/');
    const articleId = pathSegments[pathSegments.length - 1];
    const comment = document.getElementById('comment').value;
    const csrfToken = document.getElementById('csrf_token').value;

    if (!comment) {
        alert('Comment cannot be empty!');
        return;
    }

    const res = await fetch(`/submit_comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId, comment, csrf_token: csrfToken })
    });

    const result = await res.json();
    console.log(result);

    if (result.status === 'success') {
        alert('Comment submitted successfully!');
        fetchArticleComments();
    } else {
        alert(`Error: ${result.message}`);
    }
});
