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

function insertCommentsIntoPage(posted_comments) {
    const section = document.getElementById('posted_comments');
    section.innerHTML = ''; // Clear existing comments
    const wrapper = document.createElement('div');
    wrapper.id = 'comments_wrapper';
    posted_comments.forEach(comment => {
        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment';
        const p = document.createElement('p');
        p.textContent = comment.content;
        commentDiv.appendChild(p);

        // Add delete button only for admin or moderator
        if (isAuthorizedToDelete()) {
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.className = 'delete-button';
            deleteButton.onclick = () => removeComment(comment.comment_id);
            commentDiv.appendChild(deleteButton);
        }

        wrapper.appendChild(commentDiv);
    });
    section.appendChild(wrapper);
}

// Function to check if the user is authorized to delete comments
function isAuthorizedToDelete() {
    // Assuming role is stored in sessionStorage or fetched from an API
    const role = sessionStorage.getItem('role'); // Adjust based on how you store the role
    return role === 'admin' || role === 'moderator';
}

// Function to remove a comment
async function removeComment(commentId) {
    const csrfToken = document.getElementById('csrf_token').value;

    try {
        const res = await fetch('/remove_comment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment_id: commentId, csrf_token: csrfToken })
        });

        const result = await res.json();

        if (result.status === 'success') {
            alert('Comment removed successfully!');
            fetchArticleComments(); // Refresh comments
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        console.error('Error removing comment:', error);
        alert('Failed to remove comment.');
    }
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

// Fetch comments when the page loads
fetchArticleComments();