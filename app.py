"""The Tinshed Players roster prototype."""

import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

import click
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


ROLES = (
    "Stage manager",
    "Lighting operator",
    "Sound operator",
    "Front of house",
    "Box office",
    "Bar 1",
    "Bar 2",
    "Usher 1",
    "Usher 2",
)

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS volunteers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS productions (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS performances (
    id INTEGER PRIMARY KEY,
    production_id INTEGER NOT NULL REFERENCES productions(id) ON DELETE RESTRICT,
    starts_at TEXT NOT NULL,
    venue TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY,
    performance_id INTEGER NOT NULL REFERENCES performances(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    volunteer_id INTEGER NOT NULL REFERENCES volunteers(id) ON DELETE RESTRICT,
    confirmed INTEGER NOT NULL DEFAULT 0 CHECK (confirmed IN (0, 1)),
    UNIQUE (performance_id, role),
    UNIQUE (performance_id, volunteer_id)
);
"""


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        DATABASE=os.environ.get("APP_DATABASE", str(Path(app.instance_path) / "tinshed.sqlite3")),
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-only"),
        APP_ENV=os.environ.get("APP_ENV", "development"),
    )
    if test_config:
        app.config.update(test_config)
    if app.config["APP_ENV"] == "production" and app.config["SECRET_KEY"] == "local-development-only":
        raise RuntimeError("Set SECRET_KEY before running in production")
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    with app.app_context():
        db().executescript(SCHEMA)
        db().commit()

    @app.before_request
    def protect_writes():
        if request.method == "POST":
            submitted = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not expected or not secrets.compare_digest(submitted, expected):
                abort(400, "Form expired. Refresh the page and try again.")

    @app.context_processor
    def template_globals():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"], "roles": ROLES}

    def row_or_404(query, params):
        row = db().execute(query, params).fetchone()
        if row is None:
            abort(404)
        return row

    def required(value, label):
        value = value.strip()
        if not value:
            raise ValueError(f"{label} is required.")
        return value

    def valid_start(value):
        try:
            return datetime.fromisoformat(value).strftime("%Y-%m-%dT%H:%M")
        except ValueError as exc:
            raise ValueError("Enter a valid performance date and time.") from exc

    def volunteer_form():
        return (
            required(request.form.get("name", ""), "Name"),
            request.form.get("email", "").strip(),
            request.form.get("phone", "").strip(),
        )

    def performance_form():
        production_id = request.form.get("production_id", type=int)
        if not production_id or not db().execute("SELECT 1 FROM productions WHERE id = ?", (production_id,)).fetchone():
            raise ValueError("Choose an existing production.")
        return production_id, valid_start(request.form.get("starts_at", "")), request.form.get("venue", "").strip()

    def assignment_form(performance_id, current_id=None):
        role = request.form.get("role", "")
        volunteer_id = request.form.get("volunteer_id", type=int)
        if role not in ROLES:
            raise ValueError("Choose a valid role.")
        volunteer = db().execute("SELECT id, active FROM volunteers WHERE id = ?", (volunteer_id,)).fetchone()
        if volunteer is None or not volunteer["active"]:
            raise ValueError("Choose an active volunteer.")
        conflict = db().execute(
            "SELECT id FROM assignments WHERE performance_id = ? AND (role = ? OR volunteer_id = ?) AND id != ?",
            (performance_id, role, volunteer_id, current_id or -1),
        ).fetchone()
        if conflict:
            raise ValueError("This role or volunteer is already assigned to this performance.")
        return role, volunteer_id

    @app.get("/health")
    def health():
        db().execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @app.get("/")
    def index():
        counts = {
            "volunteers": db().execute("SELECT count(*) FROM volunteers WHERE active = 1").fetchone()[0],
            "productions": db().execute("SELECT count(*) FROM productions").fetchone()[0],
            "performances": db().execute("SELECT count(*) FROM performances").fetchone()[0],
        }
        performances = db().execute(
            "SELECT p.*, pr.title, count(a.id) AS assigned FROM performances p "
            "JOIN productions pr ON pr.id = p.production_id "
            "LEFT JOIN assignments a ON a.performance_id = p.id "
            "GROUP BY p.id ORDER BY p.starts_at LIMIT 20"
        ).fetchall()
        return render_template("index.html", counts=counts, performances=performances)

    @app.route("/volunteers", methods=["GET", "POST"])
    def volunteers():
        if request.method == "POST":
            try:
                values = volunteer_form()
                db().execute("INSERT INTO volunteers (name, email, phone) VALUES (?, ?, ?)", values)
                db().commit()
                flash("Volunteer added.", "success")
                return redirect(url_for("volunteers"))
            except ValueError as exc:
                flash(str(exc), "error")
        items = db().execute("SELECT * FROM volunteers ORDER BY active DESC, name").fetchall()
        return render_template("volunteers.html", volunteers=items)

    @app.route("/volunteers/<int:volunteer_id>/edit", methods=["GET", "POST"])
    def edit_volunteer(volunteer_id):
        volunteer = row_or_404("SELECT * FROM volunteers WHERE id = ?", (volunteer_id,))
        if request.method == "POST":
            try:
                values = volunteer_form()
                db().execute("UPDATE volunteers SET name = ?, email = ?, phone = ? WHERE id = ?", (*values, volunteer_id))
                db().commit()
                flash("Volunteer updated.", "success")
                return redirect(url_for("volunteers"))
            except ValueError as exc:
                flash(str(exc), "error")
        return render_template("volunteer_edit.html", volunteer=volunteer)

    @app.post("/volunteers/<int:volunteer_id>/toggle")
    def toggle_volunteer(volunteer_id):
        volunteer = row_or_404("SELECT * FROM volunteers WHERE id = ?", (volunteer_id,))
        if volunteer["active"]:
            assigned = db().execute("SELECT 1 FROM assignments WHERE volunteer_id = ? LIMIT 1", (volunteer_id,)).fetchone()
            if assigned:
                flash("Remove this volunteer's assignments before deactivating them.", "error")
                return redirect(url_for("volunteers"))
        db().execute("UPDATE volunteers SET active = ? WHERE id = ?", (0 if volunteer["active"] else 1, volunteer_id))
        db().commit()
        flash("Volunteer status updated.", "success")
        return redirect(url_for("volunteers"))

    @app.route("/productions", methods=["GET", "POST"])
    def productions():
        if request.method == "POST":
            try:
                title = required(request.form.get("title", ""), "Title")
                notes = request.form.get("notes", "").strip()
                db().execute("INSERT INTO productions (title, notes) VALUES (?, ?)", (title, notes))
                db().commit()
                flash("Production added.", "success")
                return redirect(url_for("productions"))
            except ValueError as exc:
                flash(str(exc), "error")
        items = db().execute(
            "SELECT pr.*, count(p.id) AS performance_count FROM productions pr "
            "LEFT JOIN performances p ON p.production_id = pr.id GROUP BY pr.id ORDER BY pr.title"
        ).fetchall()
        return render_template("productions.html", productions=items)

    @app.route("/productions/<int:production_id>/edit", methods=["GET", "POST"])
    def edit_production(production_id):
        production = row_or_404("SELECT * FROM productions WHERE id = ?", (production_id,))
        if request.method == "POST":
            try:
                title = required(request.form.get("title", ""), "Title")
                db().execute("UPDATE productions SET title = ?, notes = ? WHERE id = ?", (title, request.form.get("notes", "").strip(), production_id))
                db().commit()
                flash("Production updated.", "success")
                return redirect(url_for("productions"))
            except ValueError as exc:
                flash(str(exc), "error")
        return render_template("production_edit.html", production=production)

    @app.route("/performances", methods=["GET", "POST"])
    def performances():
        if request.method == "POST":
            try:
                values = performance_form()
                db().execute("INSERT INTO performances (production_id, starts_at, venue) VALUES (?, ?, ?)", values)
                db().commit()
                flash("Performance added.", "success")
                return redirect(url_for("performances"))
            except ValueError as exc:
                flash(str(exc), "error")
        productions_list = db().execute("SELECT id, title FROM productions ORDER BY title").fetchall()
        items = db().execute(
            "SELECT p.*, pr.title, count(a.id) AS assigned FROM performances p "
            "JOIN productions pr ON pr.id = p.production_id "
            "LEFT JOIN assignments a ON a.performance_id = p.id "
            "GROUP BY p.id ORDER BY p.starts_at"
        ).fetchall()
        return render_template("performances.html", performances=items, productions=productions_list)

    @app.route("/performances/<int:performance_id>/edit", methods=["GET", "POST"])
    def edit_performance(performance_id):
        performance = row_or_404("SELECT * FROM performances WHERE id = ?", (performance_id,))
        if request.method == "POST":
            try:
                values = performance_form()
                db().execute("UPDATE performances SET production_id = ?, starts_at = ?, venue = ? WHERE id = ?", (*values, performance_id))
                db().commit()
                flash("Performance updated.", "success")
                return redirect(url_for("performance", performance_id=performance_id))
            except ValueError as exc:
                flash(str(exc), "error")
        productions_list = db().execute("SELECT id, title FROM productions ORDER BY title").fetchall()
        return render_template("performance_edit.html", performance=performance, productions=productions_list)

    @app.route("/performances/<int:performance_id>", methods=["GET", "POST"])
    def performance(performance_id):
        item = row_or_404(
            "SELECT p.*, pr.title FROM performances p JOIN productions pr ON pr.id = p.production_id WHERE p.id = ?",
            (performance_id,),
        )
        if request.method == "POST":
            try:
                role, volunteer_id = assignment_form(performance_id)
                db().execute(
                    "INSERT INTO assignments (performance_id, role, volunteer_id) VALUES (?, ?, ?)",
                    (performance_id, role, volunteer_id),
                )
                db().commit()
                flash("Assignment added.", "success")
                return redirect(url_for("performance", performance_id=performance_id))
            except (ValueError, sqlite3.IntegrityError) as exc:
                db().rollback()
                flash(str(exc) if isinstance(exc, ValueError) else "This role or volunteer is already assigned.", "error")
        roster = db().execute(
            "SELECT a.*, v.name FROM assignments a JOIN volunteers v ON v.id = a.volunteer_id "
            "WHERE a.performance_id = ? ORDER BY a.role", (performance_id,)
        ).fetchall()
        available = db().execute("SELECT id, name FROM volunteers WHERE active = 1 ORDER BY name").fetchall()
        return render_template("performance.html", performance=item, roster=roster, volunteers=available)

    @app.route("/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
    def edit_assignment(assignment_id):
        assignment = row_or_404("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
        if request.method == "POST":
            try:
                role, volunteer_id = assignment_form(assignment["performance_id"], assignment_id)
                db().execute("UPDATE assignments SET role = ?, volunteer_id = ? WHERE id = ?", (role, volunteer_id, assignment_id))
                db().commit()
                flash("Assignment updated.", "success")
                return redirect(url_for("performance", performance_id=assignment["performance_id"]))
            except (ValueError, sqlite3.IntegrityError) as exc:
                db().rollback()
                flash(str(exc) if isinstance(exc, ValueError) else "This role or volunteer is already assigned.", "error")
        available = db().execute("SELECT id, name FROM volunteers WHERE active = 1 ORDER BY name").fetchall()
        return render_template("assignment_edit.html", assignment=assignment, volunteers=available)

    @app.post("/assignments/<int:assignment_id>/delete")
    def delete_assignment(assignment_id):
        assignment = row_or_404("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
        db().execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        db().commit()
        flash("Assignment removed.", "success")
        return redirect(url_for("performance", performance_id=assignment["performance_id"]))

    @app.post("/assignments/<int:assignment_id>/toggle-confirm")
    def toggle_assignment_confirmation(assignment_id):
        assignment = row_or_404("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
        confirmed = 0 if assignment["confirmed"] else 1
        db().execute("UPDATE assignments SET confirmed = ? WHERE id = ?", (confirmed, assignment_id))
        db().commit()
        flash("Assignment confirmed." if confirmed else "Assignment confirmation cleared.", "success")
        return redirect(url_for("performance", performance_id=assignment["performance_id"]))

    @app.get("/my-roster")
    def my_roster():
        volunteer_id = request.args.get("volunteer_id", type=int)
        available = db().execute("SELECT id, name FROM volunteers WHERE active = 1 ORDER BY name").fetchall()
        selected = db().execute("SELECT * FROM volunteers WHERE id = ?", (volunteer_id,)).fetchone() if volunteer_id else None
        items = db().execute(
            "SELECT p.id, p.starts_at, p.venue, pr.title, a.role FROM assignments a "
            "JOIN performances p ON p.id = a.performance_id JOIN productions pr ON pr.id = p.production_id "
            "WHERE a.volunteer_id = ? ORDER BY p.starts_at", (volunteer_id or -1,)
        ).fetchall()
        return render_template("my_roster.html", volunteers=available, selected=selected, assignments=items)

    @app.cli.command("seed-demo")
    def seed_demo():
        """Insert fictional data into an empty database."""
        if db().execute("SELECT 1 FROM productions LIMIT 1").fetchone():
            raise click.ClickException("Database already contains productions; demo data was not added.")
        db().executemany("INSERT INTO volunteers (name) VALUES (?)", [("Alex Morgan",), ("Taylor Lee",), ("Sam Patel",)])
        db().execute("INSERT INTO productions (title, notes) VALUES (?, ?)", ("The Cracked Pot", "Fictional sample production"))
        db().execute("INSERT INTO performances (production_id, starts_at, venue) VALUES (?, ?, ?)", (1, "2026-10-09T19:30", "School of Arts Hall"))
        db().commit()
        click.echo("Fictional demo data added.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", "8000")), debug=os.environ.get("APP_ENV") == "development")
