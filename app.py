import sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DB_NAME = "comments.db"


def init_db():
    """Create database tables and seed initial post immediately on load."""
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
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            dummy_text = (
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
            )
            cursor.execute(
                "INSERT INTO posts (content, created_at) VALUES (?, ?)",
                (dummy_text, date_str),
            )
        conn.commit()


# Execute DB initialization immediately upon module import for Gunicorn
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

    return jsonify({"post": dict(post), "comments": comments})


@app.route("/api/comment", methods=["POST"])
def add_comment():
    data = request.json or {}
    post_id = data.get("post_id")
    content = data.get("content", "").strip()

    if not content or not post_id:
        return jsonify({"error": "Content and post_id required"}), 400

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

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
    <title>Geometric Comments</title>
</head>
<body style="background-color: #ffffff; margin: 0; padding-top: 40px;">

<div style="display: flex; flex-direction: column; align-items: center;">

    <!-- Main Geometric Post -->
    <div id="post-target"></div>

    <!-- Toggle Comment Input -->
    <div style="width: 500px; margin-top: 5px; margin-bottom: 10px;">
        <button onclick="toggleCommentBox()" style="background-color: #8b8c89; color: #ffffff; border: 1px solid #000000; padding: 6px 12px; cursor: pointer; font-family: sans-serif; font-size: 13px;">Comment</button>
    </div>

    <!-- Input Box matching exact comment dimensions and location -->
    <div id="comment-box-wrapper" style="display: none; margin-left: 40px; margin-bottom: 15px;">
        <textarea id="comment-input" placeholder="Type comment..." style="width: 460px; height: 100px; background-color: #8b8c89; color: #ffffff; border: 2px solid #000000; border-radius: 0px; box-sizing: border-box; resize: none; font-family: sans-serif; font-size: 14px; padding: 12px; display: block; outline: none;"></textarea>
        <button onclick="submitComment()" style="margin-top: 5px; background-color: #000000; color: #ffffff; border: none; padding: 6px 12px; cursor: pointer; font-weight: bold; font-family: sans-serif;">Submit</button>
    </div>

    <!-- Comments Stack -->
    <div id="comments-target"></div>

</div>

<script>
    let currentPostId = null;

    async function loadData() {
        try {
            const response = await fetch('/api/post');
            const data = await response.json();
            currentPostId = data.post.id;

            // Render post (width 500px, margin-left 0px)
            document.getElementById('post-target').innerHTML = createSvgRectangle(data.post.content, data.post.created_at, 500, 0);

            // Render comments (width 460px, margin-left 40px)
            const commentsContainer = document.getElementById('comments-target');
            commentsContainer.innerHTML = data.comments.map(c => createSvgRectangle(c.content, c.created_at, 460, 40)).join('');
        } catch (err) {
            console.error(err);
        }
    }

    function createSvgRectangle(text, date, rectWidth, leftMargin) {
        const words = text.split(' ');
        let lines = [];
        let currentLine = '';
        
        words.forEach(word => {
            if ((currentLine + word).length > 42) {
                lines.push(currentLine);
                currentLine = word + ' ';
            } else {
                currentLine += word + ' ';
            }
        });
        lines.push(currentLine);

        const textTspans = lines.map((line, index) => 
            `<tspan x="15" dy="${index === 0 ? 0 : 20}">${escapeHtml(line)}</tspan>`
        ).join('');

        return `
            <div style="margin-left: ${leftMargin}px; margin-bottom: 10px;">
                <svg width="${rectWidth}" height="100" viewBox="0 0 ${rectWidth} 100">
                    <rect x="0" y="0" width="${rectWidth}" height="100" fill="#8b8c89" stroke="#000000" stroke-width="2" />
                    <text x="15" y="30" font-family="sans-serif" font-size="14" fill="#ffffff">${textTspans}</text>
                    <text x="${rectWidth - 15}" y="85" text-anchor="end" font-family="sans-serif" font-size="12" fill="#e0e0e0">${escapeHtml(date)}</text>
                </svg>
            </div>
        `;
    }

    function toggleCommentBox() {
        const box = document.getElementById('comment-box-wrapper');
        box.style.display = box.style.display === 'none' ? 'block' : 'none';
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
            document.getElementById('comment-box-wrapper').style.display = 'none';
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
