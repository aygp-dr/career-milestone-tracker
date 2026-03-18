"""CareerMilestoneTracker — Track and celebrate career milestones and achievements.

A Flask web app for Replit deployment. Lets users add, view, filter, edit,
and delete career milestones with a progress summary by year.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, g, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")

DB_PATH = Path("data/milestones.db")

app.config.setdefault("DB_PATH", str(DB_PATH))

CATEGORIES = ["promotion", "certification", "project", "award", "talk"]

CATEGORY_ICONS = {
    "promotion": "\u2b06",
    "certification": "\U0001f4dc",
    "project": "\U0001f680",
    "award": "\U0001f3c6",
    "talk": "\U0001f399",
}

CATEGORY_COLORS = {
    "promotion": "#3fb950",
    "certification": "#58a6ff",
    "project": "#f0883e",
    "award": "#d2a8ff",
    "talk": "#79c0ff",
}


def get_db():
    if "db" not in g:
        db_path = Path(app.config["DB_PATH"])
        db_path.parent.mkdir(exist_ok=True)
        g.db = sqlite3.connect(str(db_path))
        g.db.row_factory = sqlite3.Row
        g.db.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Career Milestone Tracker</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, sans-serif; background: #0d1117; color: #c9d1d9; }
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
h1 { color: #58a6ff; margin-bottom: 8px; }
.subtitle { color: #8b949e; margin-bottom: 24px; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }

/* Filter tabs */
.filters { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
.filter-btn { padding: 6px 14px; border: 1px solid #30363d; background: #21262d;
  color: #c9d1d9; border-radius: 20px; cursor: pointer; text-decoration: none; font-size: 13px; }
.filter-btn:hover { background: #30363d; text-decoration: none; }
.filter-btn.active { background: #1f6feb; border-color: #1f6feb; color: white; }

/* Summary */
.summary { margin-bottom: 24px; padding: 16px; background: #161b22;
  border-radius: 8px; border: 1px solid #30363d; }
.summary h2 { color: #58a6ff; font-size: 16px; margin-bottom: 12px; }
.summary-grid { display: flex; gap: 16px; flex-wrap: wrap; }
.summary-item { text-align: center; min-width: 80px; }
.summary-count { font-size: 28px; font-weight: 700; color: #f0883e; }
.summary-label { font-size: 12px; color: #8b949e; }
.year-bars { margin-top: 12px; }
.year-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.year-label { font-size: 13px; color: #8b949e; width: 50px; text-align: right; }
.year-bar { height: 20px; background: #21262d; border-radius: 4px; flex: 1; overflow: hidden; }
.year-fill { height: 100%; background: #3fb950; border-radius: 4px; transition: width 0.3s;
  display: flex; align-items: center; padding-left: 8px; font-size: 11px; color: white; min-width: 24px; }

/* Add form */
.add-form { margin-bottom: 24px; padding: 16px; background: #161b22;
  border-radius: 8px; border: 1px solid #30363d; }
.add-form h2 { color: #58a6ff; font-size: 16px; margin-bottom: 12px; }
.form-row { display: flex; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
.form-row input, .form-row select, .form-row textarea {
  background: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
  border-radius: 6px; padding: 8px 12px; font-family: inherit; font-size: 14px; }
.form-row input[type="text"] { flex: 1; min-width: 200px; }
.form-row input[type="date"] { width: 160px; }
.form-row select { width: 160px; }
.form-row textarea { width: 100%; min-height: 60px; resize: vertical; }
.btn { padding: 8px 16px; border: 1px solid #30363d; background: #21262d;
  color: #c9d1d9; border-radius: 6px; cursor: pointer; font-size: 14px; }
.btn:hover { background: #30363d; }
.btn-primary { background: #238636; border-color: #238636; color: white; }
.btn-primary:hover { background: #2ea043; }
.btn-danger { background: #da3633; border-color: #da3633; color: white; font-size: 12px; padding: 4px 10px; }
.btn-danger:hover { background: #f85149; }
.btn-edit { background: #1f6feb; border-color: #1f6feb; color: white; font-size: 12px; padding: 4px 10px; }
.btn-edit:hover { background: #388bfd; }

/* Timeline */
.timeline { position: relative; }
.timeline::before { content: ''; position: absolute; left: 20px; top: 0; bottom: 0;
  width: 2px; background: #30363d; }
.milestone { position: relative; padding-left: 50px; margin-bottom: 16px; }
.milestone-dot { position: absolute; left: 13px; top: 18px; width: 16px; height: 16px;
  border-radius: 50%; border: 2px solid #30363d; background: #161b22; }
.milestone-card { padding: 16px; background: #161b22; border: 1px solid #30363d;
  border-radius: 8px; transition: border-color 0.2s; }
.milestone-card:hover { border-color: #58a6ff; }
.milestone-header { display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 6px; flex-wrap: wrap; gap: 8px; }
.milestone-title { font-size: 16px; font-weight: 600; }
.milestone-actions { display: flex; gap: 6px; }
.milestone-meta { display: flex; gap: 12px; font-size: 13px; color: #8b949e; margin-bottom: 4px; flex-wrap: wrap; }
.milestone-category { padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.5px; }
.milestone-desc { font-size: 14px; color: #8b949e; margin-top: 6px; }

/* Edit form */
.edit-form { padding: 16px; background: #161b22; border: 1px solid #30363d;
  border-radius: 8px; margin-bottom: 16px; }
.edit-form h2 { color: #58a6ff; font-size: 16px; margin-bottom: 12px; }

.empty { text-align: center; color: #8b949e; padding: 40px; }
</style>
</head>
<body>
<div class="container">
<h1>Career Milestone Tracker</h1>
<p class="subtitle">Celebrate and track your career milestones and achievements</p>

<!-- Category filters -->
<div class="filters">
  <a href="{{ url_for('index') }}" class="filter-btn {{ 'active' if not current_filter }}">All</a>
  {% for cat in categories %}
  <a href="{{ url_for('index', category=cat) }}"
     class="filter-btn {{ 'active' if current_filter == cat }}"
     style="{{ 'background:' + cat_colors[cat] + ';border-color:' + cat_colors[cat] + ';color:white' if current_filter == cat else '' }}">
    {{ cat_icons[cat] }} {{ cat | capitalize }}
  </a>
  {% endfor %}
</div>

<!-- Progress summary -->
<div class="summary">
  <h2>Progress Summary</h2>
  <div class="summary-grid">
    <div class="summary-item">
      <div class="summary-count">{{ total_count }}</div>
      <div class="summary-label">Total Milestones</div>
    </div>
    {% for cat in categories %}
    <div class="summary-item">
      <div class="summary-count" style="color: {{ cat_colors[cat] }}; font-size: 20px;">{{ cat_counts[cat] }}</div>
      <div class="summary-label">{{ cat_icons[cat] }} {{ cat | capitalize }}</div>
    </div>
    {% endfor %}
  </div>
  {% if year_data %}
  <div class="year-bars">
    {% for year, count in year_data %}
    <div class="year-row">
      <span class="year-label">{{ year }}</span>
      <div class="year-bar">
        <div class="year-fill" style="width: {{ (count / max_year_count * 100) | int }}%">{{ count }}</div>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>

<!-- Add milestone form -->
{% if not editing %}
<div class="add-form">
  <h2>Add Milestone</h2>
  <form method="POST" action="{{ url_for('add_milestone') }}">
    <div class="form-row">
      <input type="text" name="title" placeholder="Milestone title..." required>
      <input type="date" name="date" value="{{ today }}" required>
      <select name="category" required>
        {% for cat in categories %}
        <option value="{{ cat }}">{{ cat_icons[cat] }} {{ cat | capitalize }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="form-row">
      <textarea name="description" placeholder="Description (optional)"></textarea>
    </div>
    <button type="submit" class="btn btn-primary">Add Milestone</button>
  </form>
</div>
{% endif %}

<!-- Edit form -->
{% if editing %}
<div class="edit-form">
  <h2>Edit Milestone</h2>
  <form method="POST" action="{{ url_for('edit_milestone', milestone_id=editing.id) }}">
    <div class="form-row">
      <input type="text" name="title" value="{{ editing.title }}" required>
      <input type="date" name="date" value="{{ editing.date }}" required>
      <select name="category" required>
        {% for cat in categories %}
        <option value="{{ cat }}" {{ 'selected' if editing.category == cat }}>{{ cat_icons[cat] }} {{ cat | capitalize }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="form-row">
      <textarea name="description">{{ editing.description }}</textarea>
    </div>
    <button type="submit" class="btn btn-primary">Save Changes</button>
    <a href="{{ url_for('index') }}" class="btn" style="display:inline-block;margin-left:8px">Cancel</a>
  </form>
</div>
{% endif %}

<!-- Timeline -->
<div class="timeline">
  {% if milestones %}
    {% for m in milestones %}
    <div class="milestone">
      <div class="milestone-dot" style="background: {{ cat_colors[m.category] }}; border-color: {{ cat_colors[m.category] }};"></div>
      <div class="milestone-card">
        <div class="milestone-header">
          <span class="milestone-title">{{ cat_icons[m.category] }} {{ m.title }}</span>
          <div class="milestone-actions">
            <a href="{{ url_for('index', edit=m.id) }}" class="btn btn-edit">Edit</a>
            <form method="POST" action="{{ url_for('delete_milestone', milestone_id=m.id) }}" style="display:inline"
              onsubmit="return confirm('Delete this milestone?')">
              <button type="submit" class="btn btn-danger">Delete</button>
            </form>
          </div>
        </div>
        <div class="milestone-meta">
          <span class="milestone-category" style="background: {{ cat_colors[m.category] }}22; color: {{ cat_colors[m.category] }};">{{ m.category }}</span>
          <span>{{ m.date }}</span>
        </div>
        {% if m.description %}
        <div class="milestone-desc">{{ m.description }}</div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  {% else %}
    <div class="empty">No milestones yet. Add your first career milestone above!</div>
  {% endif %}
</div>
</div>
</body>
</html>"""


@app.route("/")
def index():
    db = get_db()
    current_filter = request.args.get("category")
    edit_id = request.args.get("edit", type=int)

    if current_filter and current_filter in CATEGORIES:
        milestones = db.execute(
            "SELECT * FROM milestones WHERE category=? ORDER BY date DESC, id DESC",
            (current_filter,),
        ).fetchall()
    else:
        current_filter = None
        milestones = db.execute(
            "SELECT * FROM milestones ORDER BY date DESC, id DESC"
        ).fetchall()

    # Category counts
    cat_counts = {}
    for cat in CATEGORIES:
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM milestones WHERE category=?", (cat,)
        ).fetchone()
        cat_counts[cat] = row["cnt"]

    total_count = sum(cat_counts.values())

    # Year data for progress summary
    year_rows = db.execute(
        "SELECT substr(date, 1, 4) as year, COUNT(*) as cnt "
        "FROM milestones GROUP BY year ORDER BY year"
    ).fetchall()
    year_data = [(r["year"], r["cnt"]) for r in year_rows]
    max_year_count = max((r[1] for r in year_data), default=1)

    editing = None
    if edit_id:
        editing = db.execute(
            "SELECT * FROM milestones WHERE id=?", (edit_id,)
        ).fetchone()

    return render_template_string(
        TEMPLATE,
        milestones=milestones,
        categories=CATEGORIES,
        cat_icons=CATEGORY_ICONS,
        cat_colors=CATEGORY_COLORS,
        cat_counts=cat_counts,
        total_count=total_count,
        year_data=year_data,
        max_year_count=max_year_count,
        current_filter=current_filter,
        editing=editing,
        today=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/add", methods=["POST"])
def add_milestone():
    db = get_db()
    title = request.form.get("title", "").strip()
    date = request.form.get("date", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not date or category not in CATEGORIES:
        return redirect(url_for("index"))

    db.execute(
        "INSERT INTO milestones (title, date, category, description) VALUES (?, ?, ?, ?)",
        (title, date, category, description),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/edit/<int:milestone_id>", methods=["POST"])
def edit_milestone(milestone_id):
    db = get_db()
    title = request.form.get("title", "").strip()
    date = request.form.get("date", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not date or category not in CATEGORIES:
        return redirect(url_for("index"))

    db.execute(
        "UPDATE milestones SET title=?, date=?, category=?, description=? WHERE id=?",
        (title, date, category, description, milestone_id),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:milestone_id>", methods=["POST"])
def delete_milestone(milestone_id):
    db = get_db()
    db.execute("DELETE FROM milestones WHERE id=?", (milestone_id,))
    db.commit()
    return redirect(url_for("index"))


@app.route("/api/milestones")
def api_milestones():
    db = get_db()
    category = request.args.get("category")
    if category and category in CATEGORIES:
        rows = db.execute(
            "SELECT * FROM milestones WHERE category=? ORDER BY date DESC, id DESC",
            (category,),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM milestones ORDER BY date DESC, id DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/milestones/<int:milestone_id>")
def api_milestone(milestone_id):
    db = get_db()
    row = db.execute("SELECT * FROM milestones WHERE id=?", (milestone_id,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.route("/api/summary")
def api_summary():
    db = get_db()
    cat_counts = {}
    for cat in CATEGORIES:
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM milestones WHERE category=?", (cat,)
        ).fetchone()
        cat_counts[cat] = row["cnt"]

    year_rows = db.execute(
        "SELECT substr(date, 1, 4) as year, COUNT(*) as cnt "
        "FROM milestones GROUP BY year ORDER BY year"
    ).fetchall()
    by_year = {r["year"]: r["cnt"] for r in year_rows}

    return jsonify({
        "total": sum(cat_counts.values()),
        "by_category": cat_counts,
        "by_year": by_year,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
