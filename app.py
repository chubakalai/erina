import sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DB_NAME = "comments.db"


def init_db():
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
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        """
        )

        cursor.execute("SELECT COUNT(*) FROM posts")
        if cursor.fetchone()[0] == 0:
            date_str = datetime.now().strftime("%Y-%m-%d")
            dummy_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor."
            cursor.execute(
                "INSERT INTO posts (content, created_at) VALUES (?, ?)",
                (dummy_text, date_str),
            )
        conn.commit()


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
            "SELECT id, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC",
            (post["id"],),
        )
        comments = [dict(row) for row in cursor.fetchall()]

    return jsonify(
        {
            "post": dict(post),
            "comments": comments,
        }
    )


@app.route("/api/comment", methods=["POST"])
def add_comment():
    data = request.json or {}
    post_id = data.get("post_id")
    content = data.get("content", "").strip()

    if not content or not post_id:
        return jsonify({"error": "Content and post_id required"}), 400

    date_str = datetime.now().strftime("%Y-%m-%d")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comments (post_id, content, created_at) VALUES (?, ?, ?)",
            (post_id, content, date_str),
        )
        conn.commit()

    return jsonify({"status": "success"}), 201


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Geometric Rectangles</title>
</head>
<body>

<div id="post-target"></div>

<div>
    <textarea id="comment-input" rows="3" cols="50"></textarea><br>
    <button onclick="submitComment()">Submit</button>
</div>

<br>

<div id="comments-target"></div>

<script>
    let currentPostId = null;

    async function loadData() {
        try {
            const response = await fetch('/api/post');
            const data = await response.json();
            currentPostId = data.post.id;

            // Render post inside a geometric SVG rectangle with date bottom-right
            document.getElementById('post-target').innerHTML = createSvgRectangle(data.post.content, data.post.created_at, 0);

            // Render comments as indented geometric SVG rectangles with dates bottom-right
            const commentsContainer = document.getElementById('comments-target');
            commentsContainer.innerHTML = data.comments.map(c => createSvgRectangle(c.content, c.created_at, 40)).join('<br>');
        } catch (err) {
            console.error(err);
        }
    }

    function createSvgRectangle(text, date, xOffset) {
        return `
            <svg width="500" height="120" viewBox="0 0 500 120">
                <g transform="translate(${xOffset}, 0)">
                    <rect x="0" y="0" width="${460 - xOffset}" height="100" fill="none" stroke="black" stroke-width="2" />
                    <text x="15" y="35" font-family="sans-serif" font-size="14">${escapeHtml(text)}</text>
                    <text x="${445 - xOffset}" y="85" text-anchor="end" font-family="sans-serif" font-size="12">${escapeHtml(date)}</text>
                </g>
            </svg>
        `;
    }

    async function submitComment() {
        if (!currentPostId) return;
        const inputElem = document.getElementById('comment-input');
        const content = inputElem.value;
        if (!content.trim()) return;

        const response = await fetch('/api/comment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                post_id: currentPostId,
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
