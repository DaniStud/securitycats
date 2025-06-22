async function fetchArticleById(articleId) {
    try {
        const response = await fetch(`/get_article/${articleId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();

        if (result.status === 'success') {
            insertArticleIntoPage(result.data.article);
            insertCommentsIntoPage(result.data.comments);
        } else {
            console.error('Error fetching article:', result.message);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function insertArticleIntoPage(article) {
    const section = document.querySelector('section');
    const wrapper = document.querySelector('.articleWrapper');
    if (wrapper) {
        wrapper.querySelector('.articleTitle').textContent = article.title;
        wrapper.querySelector('.articleContent').textContent = article.article;
    }
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
        
        const usernameLink = document.createElement('a');
        usernameLink.className = 'comment-username';
        usernameLink.href = `/user_profile/${comment.user_id}`;
        usernameLink.textContent = `Posted by: ${comment.name || 'Unknown'}`;
        commentDiv.appendChild(usernameLink);

        if (comment.profile_pic) {
            const profilePic = document.createElement('img');
            profilePic.className = 'comment-profile-pic';
            profilePic.src = `/static/uploads/${comment.profile_pic}`;
            profilePic.alt = `${comment.name || 'Unknown'}'s profile picture`;
            commentDiv.appendChild(profilePic);
        }

        const content = document.createElement('p');
        content.className = 'comment-content';
        content.textContent = comment.content || 'No content';
        commentDiv.appendChild(content);

        if (isAuthorizedToDelete()) {
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.className = 'delete-button';
            deleteButton.addEventListener('click', () => removeComment(comment.comment_id));
            commentDiv.appendChild(deleteButton);
        }

        wrapper.appendChild(commentDiv);
    });
    section.appendChild(wrapper);
}

function isAuthorizedToDelete() {
    const role = document.getElementById('user_role')?.value;
    return role === 'admin' || role === 'moderator';
}

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
            fetchArticleComments();
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

    try {
        const res = await fetch(`/submit_comment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ article_id: articleId, comment, csrf_token: csrfToken })
        });

        const result = await res.json();
        console.log(result);

        if (result.status === 'success') {
            alert('Comment submitted successfully!');
            document.getElementById('comment').value = ''; // Clear the textarea
            fetchArticleComments();
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        console.error('Error submitting comment:', error);
        alert('Failed to submit comment.');
    }
});

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    const pathSegments = window.location.pathname.split('/');
    const articleId = pathSegments[pathSegments.length - 1];
    if (articleId) {
        fetchArticleById(articleId);
    }
    fetchArticleComments();
});