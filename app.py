import sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DB_NAME = "comments.db"


def init_db():
    """Ensure database and tables are created before processing requests."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                parent_id INTEGER,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (parent_id) REFERENCES comments (id)
            )
        """
        )

        cursor.execute("SELECT COUNT(*) FROM posts")
        if cursor.fetchone()[0] == 0:
            date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
            dummy_text = (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip."
            )
            cursor.execute(
                "INSERT INTO posts (content, created_at) VALUES (?, ?)",
                (dummy_text, date_str),
            )
        conn.commit()


# Run DB initialization immediately when app module loads (Crucial for Gunicorn/Fly.io)
init_db()


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/post", methods=["GET"])
def get_post():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, content, created_at FROM posts ORDER BY id ASC LIMIT 1"
        )
        post = cursor.fetchone()

        if not post:
            return jsonify({"error": "Post not found"}), 404

        cursor.execute(
            "SELECT id, parent_id, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC",
            (post["id"],),
        )
        comments = [dict(row) for row in cursor.fetchall()]

    return jsonify(
        {
            "post": dict(post),
            "comments": build_comment_tree(comments),
        }
    )


@app.route("/api/comment", methods=["POST"])
def add_comment():
    data = request.json or {}
    post_id = data.get("post_id")
    parent_id = data.get("parent_id")
    content = data.get("content", "").strip()

    if not content or not post_id:
        return jsonify({"error": "Content and post_id are required"}), 400

    date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comments (post_id, parent_id, content, created_at) VALUES (?, ?, ?, ?)",
            (post_id, parent_id, content, date_str),
        )
        conn.commit()

    return jsonify({"status": "success"}), 201


def build_comment_tree(comments):
    comment_dict = {c["id"]: {**c, "children": []} for c in comments}
    tree = []

    for c in comment_dict.values():
        parent_id = c["parent_id"]
        if parent_id and parent_id in comment_dict:
            comment_dict[parent_id]["children"].append(c)
        else:
            tree.append(c)

    return tree


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post & Comments</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background-color: #f4f6f8;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }

        .container {
            width: 100%;
            max-width: 650px;
        }

        .card {
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
            border-radius: 8px;
            padding: 18px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-bottom: 10px;
        }

        .post-card {
            border-left: 4px solid #0066cc;
        }

        .date {
            font-size: 0.8rem;
            color: #6a737d;
            margin-bottom: 8px;
            display: block;
        }

        .content {
            font-size: 0.95rem;
            color: #24292e;
            line-height: 1.5;
            margin: 0 0 10px 0;
        }

        .nested-comments {
            margin-left: 24px;
            border-left: 2px solid #e1e4e8;
            padding-left: 10px;
        }

        textarea {
            width: 100%;
            min-height: 60px;
            padding: 10px;
            border: 1px solid #d1d5da;
            border-radius: 6px;
            resize: vertical;
            font-family: inherit;
            margin-bottom: 8px;
        }

        textarea:focus {
            outline: none;
            border-color: #0066cc;
        }

        button {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 7px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
        }

        button:hover { background-color: #0052a3; }

        .btn-reply {
            background: none;
            color: #0066cc;
            padding: 0;
            font-size: 0.82rem;
        }

        .btn-reply:hover {
            background: none;
            text-decoration: underline;
        }

        .reply-form {
            margin-top: 10px;
            display: none;
        }

        .reply-form.active { display: block; }
    </style>
</head>
<body>

<div class="container">
    <div id="post-target">Loading...</div>

    <div class="card">
        <textarea id="main-comment-input" placeholder="Write a comment..."></textarea>
        <button onclick="submitComment(null, 'main-comment-input')">Comment</button>
    </div>

    <div class="comments-container" id="comments-target"></div>
</div>

<script>
    let currentPostId = null;

    async function loadData() {
        try {
            const response = await fetch('/api/post');
            if (!response.ok) throw new Error("Failed to fetch post");
            
            const data = await response.json();
            currentPostId = data.post.id;
            
            document.getElementById('post-target').innerHTML = `
                <div class="card post-card">
                    <span class="date">${data.post.created_at}</span>
                    <p class="content">${escapeHtml(data.post.content)}</p>
                </div>
            `;

            document.getElementById('comments-target').innerHTML = renderCommentsTree(data.comments);
        } catch (err) {
            console.error(err);
            document.getElementById('post-target').innerHTML = `<div class="card">Error loading post.</div>`;
        }
    }

    function renderCommentsTree(comments) {
        if (!comments || comments.length === 0) return '';
        
        return comments.map(comment => `
            <div class="comment-node">
                <div class="card">
                    <span class="date">${comment.created_at}</span>
                    <p class="content">${escapeHtml(comment.content)}</p>
                    <button class="btn-reply" onclick="toggleReplyForm(${comment.id})">Reply</button>

                    <div class="reply-form" id="reply-form-${comment.id}">
                        <textarea id="reply-input-${comment.id}" placeholder="Write a reply..."></textarea>
                        <button onclick="submitComment(${comment.id}, 'reply-input-${comment.id}')">Submit Reply</button>
                    </div>
                </div>
                
                <div class="nested-comments">
                    ${renderCommentsTree(comment.children)}
                </div>
            </div>
        `).join('');
    }

    function toggleReplyForm(commentId) {
        const form = document.getElementById(`reply-form-${commentId}`);
        form.classList.toggle('active');
    }

    async function submitComment(parentId, inputId) {
        if (!currentPostId) return;

        const inputElem = document.getElementById(inputId);
        const content = inputElem.value;

        if (!content.trim()) return;

        const response = await fetch('/api/comment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                post_id: currentPostId,
                parent_id: parentId,
                content: content
            })
        });

        if (response.ok) {
            inputElem.value = '';
            loadData();
        }
    }

    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    loadData();
</script>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
