from datetime import datetime
import sqlite3
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "documents.db"

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


@app.before_first_request
def setup_db() -> None:
    init_db()


@app.route("/")
def index() -> str:
    status_filter = request.args.get("status", "all")
    query = "SELECT * FROM documents"
    params = []
    if status_filter != "all":
        query += " WHERE status = ?"
        params.append(status_filter)
    query += " ORDER BY updated_at DESC"
    with get_db() as conn:
        documents = conn.execute(query, params).fetchall()
    return render_template("index.html", documents=documents, status_filter=status_filter)


@app.route("/documents/new", methods=["GET", "POST"])
def create_document() -> str:
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        status = request.form.get("status", "draft")
        if not title or not content:
            return render_template(
                "form.html",
                document=None,
                error="Заполните название и содержимое документа.",
            )
        timestamp = datetime.utcnow().isoformat()
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO documents (title, content, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, content, status, timestamp, timestamp),
            )
        return redirect(url_for("index"))
    return render_template("form.html", document=None, error=None)


@app.route("/documents/<int:document_id>")
def document_detail(document_id: int) -> str:
    with get_db() as conn:
        document = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
    if document is None:
        abort(404)
    return render_template("detail.html", document=document)


@app.route("/documents/<int:document_id>/edit", methods=["GET", "POST"])
def edit_document(document_id: int) -> str:
    with get_db() as conn:
        document = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
    if document is None:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        status = request.form.get("status", "draft")
        if not title or not content:
            return render_template(
                "form.html",
                document=document,
                error="Заполните название и содержимое документа.",
            )
        timestamp = datetime.utcnow().isoformat()
        with get_db() as conn:
            conn.execute(
                """
                UPDATE documents
                SET title = ?, content = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, content, status, timestamp, document_id),
            )
        return redirect(url_for("document_detail", document_id=document_id))

    return render_template("form.html", document=document, error=None)


@app.route("/documents/<int:document_id>/delete", methods=["POST"])
def delete_document(document_id: int) -> str:
    with get_db() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
