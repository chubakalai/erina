import os
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    abort,
    jsonify,
    render_template_string,
    request,
    send_from_directory,
)

app = Flask(__name__)
DB_NAME = "comments.db"


def init_db():
    """Create database tables immediately on load."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
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
        conn.commit()


init_db()


# -----------------------------------------------------------------------------
# 1. Main Page: All posts vertically stacked in reverse chronological order
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)


@app.route("/api/posts", methods=["GET"])
def get_all_posts():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch posts ordered newest first (reverse chronology)
        cursor.execute(
            "SELECT id, slug, content, created_at FROM posts ORDER BY id DESC"
        )
        posts_rows = cursor.fetchall()

        posts_data = []
        for post in posts_rows:
            post_dict = dict(post)
            cursor.execute(
                "SELECT id, content, created_at FROM comments WHERE post_id = ? ORDER BY id ASC",
                (post["id"],),
            )
            comments = [dict(row) for row in cursor.fetchall()]
            post_dict["comments"] = comments
            posts_data.append(post_dict)

    return jsonify({"posts": posts_data})


# -----------------------------------------------------------------------------
# 2. Base Pics: Serve files inside /basepics directly via path
# -----------------------------------------------------------------------------
@app.route("/basepics/<path:filename>")
def serve_basepics(filename):
    basepics_dir = os.path.join(app.root_path, "basepics")
    return send_from_directory(basepics_dir, filename)


# -----------------------------------------------------------------------------
# 3. Dynamic Post Route & Comment API
# -----------------------------------------------------------------------------
@app.route("/posts/<slug>")
def render_post_page(slug):
    return render_template_string(SINGLE_POST_TEMPLATE, slug=slug)


@app.route("/api/post/<slug>", methods=["GET"])
def get_single_post(slug):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, content, created_at FROM posts WHERE slug = ?", (slug,)
        )
        post = cursor.fetchone()

        if not post:
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            dummy_text = f"Post content for '{slug}'. Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            cursor.execute(
                "INSERT INTO posts (slug, content, created_at) VALUES (?, ?, ?)",
                (slug, dummy_text, date_str),
            )
            conn.commit()
            cursor.execute(
                "SELECT id, content, created_at FROM posts WHERE slug = ?",
                (slug,),
            )
            post = cursor.fetchone()

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


# -----------------------------------------------------------------------------
# 4. Clean Extensionless Root URLs
# -----------------------------------------------------------------------------
@app.route("/<name>")
def serve_root_html(name):
    target_file = f"{name}.html"
    file_path = os.path.join(app.root_path, target_file)

    if os.path.isfile(file_path):
        return send_from_directory(app.root_path, target_file)

    abort(404)


INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Posts Feed</title>
</head>
<body style="background-color: #ffffff; margin: 0; padding-top: 40px; padding-bottom: 60px;">

<div id="posts-container" style="display: flex; flex-direction: column; align-items: center;"></div>

<script>
    async function loadFeed() {
        try {
            const response = await fetch('/api/posts');
            const data = await response.json();
            const container = document.getElementById('posts-container');

            if (data.posts.length === 0) {
                container.innerHTML = '<p style="font-family: sans-serif; color: #888;">No posts found.</p>';
                return;
            }

            container.innerHTML = data.posts.map(post => renderPostBlock(post)).join('');
        } catch (err) {
            console.error(err);
        }
    }

    function renderPostBlock(post) {
        const commentsHtml = post.comments.map(c => createSvgRectangle(c.content, c.created_at, 460, 40)).join('');

        return `
            <div style="margin-bottom: 40px; display: flex; flex-direction: column; align-items: center;">
                <!-- Main Post Rectangle -->
                ${createSvgRectangle(post.content, post.created_at, 500, 0)}

                <!-- Toggle Comment Plain Text -->
                <div style="width: 500px; margin-top: 5px; margin-bottom: 10px;">
                    <span onclick="toggleCommentBox(${post.id})" style="color: #000000; cursor: pointer; font-family: sans-serif; font-size: 13px; font-weight: bold; text-decoration: underline;">Comment</span>
                </div>

                <!-- Comment Input Box -->
                <div id="comment-box-wrapper-${post.id}" style="display: none; margin-left: 40px; margin-bottom: 15px;">
                    <textarea id="comment-input-${post.id}" placeholder="Type comment..." style="width: 460px; height: 100px; background-color: #8b8c89; color: #ffffff; border: none; border-radius: 0px; box-sizing: border-box; resize: none; font-family: sans-serif; font-size: 14px; padding: 12px; display: block; outline: none;"></textarea>
                    <button onclick="submitComment(${post.id})" style="margin-top: 5px; background-color: #000000; color: #ffffff; border: none; padding: 6px 12px; cursor: pointer; font-weight: bold; font-family: sans-serif;">Submit</button>
                </div>

                <!-- Comments Stack -->
                <div id="comments-target-${post.id}">
                    ${commentsHtml}
                </div>
            </div>
        `;
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
                    <rect x="0" y="0" width="${rectWidth}" height="100" fill="#8b8c89" stroke="none" />
                    <text x="15" y="30" font-family="sans-serif" font-size="14" fill="#ffffff">${textTspans}</text>
                    <text x="${rectWidth - 15}" y="85" text-anchor="end" font-family="sans-serif" font-size="12" fill="#e0e0e0">${escapeHtml(date)}</text>
                </svg>
            </div>
        `;
    }

    function toggleCommentBox(postId) {
        const box = document.getElementById(`comment-box-wrapper-${postId}`);
        box.style.display = box.style.display === 'none' ? 'block' : 'none';
    }

    async function submitComment(postId) {
        const inputElem = document.getElementById(`comment-input-${postId}`);
        const content = inputElem.value;
        if (!content.trim()) return;

        const response = await fetch('/api/comment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                post_id: postId,
                content: content
            })
        });

        if (response.ok) {
            inputElem.value = '';
            document.getElementById(`comment-box-wrapper-${postId}`).style.display = 'none';
            loadFeed();
        }
    }

    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    loadFeed();
</script>

</body>
</html>
"""

SINGLE_POST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Post - {{ slug }}</title>
</head>
<body style="background-color: #ffffff; margin: 0; padding-top: 40px;">

<div style="display: flex; flex-direction: column; align-items: center;">

    <div id="post-target"></div>

    <div style="width: 500px; margin-top: 5px; margin-bottom: 10px;">
        <span onclick="toggleCommentBox()" style="color: #000000; cursor: pointer; font-family: sans-serif; font-size: 13px; font-weight: bold; text-decoration: underline;">Comment</span>
    </div>

    <div id="comment-box-wrapper" style="display: none; margin-left: 40px; margin-bottom: 15px;">
        <textarea id="comment-input" placeholder="Type comment..." style="width: 460px; height: 100px; background-color: #8b8c89; color: #ffffff; border: none; border-radius: 0px; box-sizing: border-box; resize: none; font-family: sans-serif; font-size: 14px; padding: 12px; display: block; outline: none;"></textarea>
        <button onclick="submitComment()" style="margin-top: 5px; background-color: #000000; color: #ffffff; border: none; padding: 6px 12px; cursor: pointer; font-weight: bold; font-family: sans-serif;">Submit</button>
    </div>

    <div id="comments-target"></div>

</div>

<script>
    const currentSlug = "{{ slug }}";
    let currentPostId = null;

    async function loadData() {
        try {
            const response = await fetch('/api/post/' + currentSlug);
            const data = await response.json();
            currentPostId = data.post.id;

            document.getElementById('post-target').innerHTML = createSvgRectangle(data.post.content, data.post.created_at, 500, 0);

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
                    <rect x="0" y="0" width="${rectWidth}" height="100" fill="#8b8c89" stroke="none" />
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
