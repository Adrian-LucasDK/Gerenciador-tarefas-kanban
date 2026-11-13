import os
from datetime import datetime, date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-usar")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "kanban.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"timeout": 20}}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Entre na sua conta para continuar."
login_manager.login_message_category = "warning"

STATUSES = ["A Fazer", "Em Andamento", "Concluído"]
PRIORITIES = ["Baixa", "Média", "Alta", "Urgente"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default="user", nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="A Fazer", nullable=False)
    priority = db.Column(db.String(10), default="Média", nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[creator_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {"STATUSES": STATUSES, "PRIORITIES": PRIORITIES}


@app.route("/")
@login_required
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    users = User.query.filter_by(active=True).order_by(User.full_name).all()
    return render_template("board.html", tasks=tasks, users=users)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username, active=True).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Usuário ou senha inválidos.", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


def parse_task_form(task=None):
    title = request.form.get("title", "").strip()
    if not title:
        raise ValueError("O título da tarefa é obrigatório.")
    status = request.form.get("status", "A Fazer")
    priority = request.form.get("priority", "Média")
    if status not in STATUSES or priority not in PRIORITIES:
        raise ValueError("Status ou prioridade inválidos.")
    due_raw = request.form.get("due_date", "").strip()
    due = date.fromisoformat(due_raw) if due_raw else None
    assignee_raw = request.form.get("assignee_id", "").strip()
    assignee_id = int(assignee_raw) if assignee_raw else None
    if assignee_id and not User.query.filter_by(id=assignee_id, active=True).first():
        raise ValueError("Responsável inválido.")
    if task is None:
        task = Task(creator_id=current_user.id)
    task.title = title
    task.description = request.form.get("description", "").strip()
    task.status = status
    task.priority = priority
    task.due_date = due
    task.assignee_id = assignee_id
    return task


@app.route("/tasks/create", methods=["POST"])
@login_required
def create_task():
    try:
        task = parse_task_form()
        db.session.add(task)
        db.session.commit()
        flash("Tarefa criada com sucesso.", "success")
    except (ValueError, TypeError):
        db.session.rollback()
        flash("Não foi possível criar a tarefa. Confira os campos.", "error")
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/edit", methods=["POST"])
@login_required
def edit_task(task_id):
    task = db.get_or_404(Task, task_id)
    try:
        parse_task_form(task)
        db.session.commit()
        flash("Tarefa atualizada.", "success")
    except (ValueError, TypeError):
        db.session.rollback()
        flash("Dados inválidos. A tarefa não foi alterada.", "error")
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = db.get_or_404(Task, task_id)
    if current_user.role != "admin" and task.creator_id != current_user.id:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash("Tarefa excluída.", "success")
    return redirect(url_for("index"))


@app.route("/api/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_status(task_id):
    task = db.get_or_404(Task, task_id)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in STATUSES:
        return jsonify(ok=False, error="Status inválido."), 400
    task.status = new_status
    db.session.commit()
    return jsonify(ok=True, status=task.status)


@app.route("/api/board")
@login_required
def board_data():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify([{
        "id": t.id, "title": t.title, "description": t.description,
        "status": t.status, "priority": t.priority,
        "due_date": t.due_date.isoformat() if t.due_date else "",
        "assignee": t.assignee.full_name if t.assignee else "Não atribuído",
        "creator": t.creator.full_name
    } for t in tasks])


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        if not username or not full_name or len(password) < 8 or role not in ["user", "admin"]:
            flash("Preencha os campos. A senha deve ter pelo menos 8 caracteres.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Esse nome de usuário já existe.", "error")
        else:
            user = User(username=username, full_name=full_name, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Usuário cadastrado.", "success")
        return redirect(url_for("manage_users"))
    users = User.query.order_by(User.full_name).all()
    return render_template("users.html", users=users)


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Você não pode desativar sua própria conta.", "error")
    else:
        user.active = not user.active
        db.session.commit()
        flash("Situação do usuário atualizada.", "success")
    return redirect(url_for("manage_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = db.get_or_404(User, user_id)

    # Impede que o administrador exclua a própria conta.
    if user.id == current_user.id:
        flash("Você não pode excluir sua própria conta.", "error")
        return redirect(url_for("manage_users"))

    try:
        # Remove as tarefas criadas pelo usuário excluído.
        Task.query.filter_by(creator_id=user.id).delete(
            synchronize_session=False
        )

        # Mantém as tarefas de outras pessoas, mas remove a atribuição.
        Task.query.filter_by(assignee_id=user.id).update(
            {"assignee_id": None},
            synchronize_session=False
        )

        # Exclui definitivamente o usuário.
        db.session.delete(user)
        db.session.commit()

        flash("Usuário excluído definitivamente.", "success")

    except Exception:
        db.session.rollback()
        flash("Não foi possível excluir o usuário.", "error")

    return redirect(url_for("manage_users"))


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="Você não tem permissão para acessar este recurso."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="O recurso solicitado não foi encontrado."), 404


def initialize_database():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", full_name="Administrador", role="admin")
            admin.set_password(os.environ.get("ADMIN_PASSWORD", "Admin123!"))
            db.session.add(admin)
            db.session.commit()


initialize_database()

if __name__ == "__main__":
    # 0.0.0.0 permite conexões de outros computadores da rede local.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
