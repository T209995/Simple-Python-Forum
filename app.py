# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# Imports pour l'authentification
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
# Imports pour les formulaires sécurisés
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

# --- Configuration de l'application Flask ---
app = Flask(__name__)

# Configuration de la base de données SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///forum.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

SECRET_KEY = os.urandom(32).hex()
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)

# --- Configuration de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Définition des modèles ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author = db.relationship('User', backref=db.backref('topics', lazy=True))
    posts = db.relationship('Post', backref='topic', lazy='dynamic', cascade="all, delete-orphan")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))


# --- Formulaires ---

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=4, max=30)])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password', message='Les mots de passe ne correspondent pas.')])
    submit = SubmitField("S'inscrire")
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ce nom d\'utilisateur est déjà pris.')

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    submit = SubmitField('Se connecter')

class PostForm(FlaskForm):
    content = TextAreaField('Votre message', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Envoyer le message')

class NewTopicForm(FlaskForm):
    title = StringField('Titre du sujet', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Premier message', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Publier le sujet')


# --- Modèles HTML ---

BASE_HEAD = """
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title if title else 'Forum Python' }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
        .form-input-field { @apply shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border border-gray-300 rounded-md p-3; }
        .form-label { @apply block text-sm font-medium text-gray-700 mb-1; }
    </style>
</head>
"""

NAV_BAR = """
<div class="max-w-4xl mx-auto mb-4 p-4 text-sm flex justify-between items-center">
    <div>
        {% if current_user.is_authenticated %}
            <span class="text-gray-700 mr-4">Connecté : <span class="font-bold text-indigo-600">{{ current_user.username }}</span></span>
            <a href="{{ url_for('logout') }}" class="text-red-500 hover:text-red-700 font-medium">Déconnexion</a>
        {% else %}
            <a href="{{ url_for('login') }}" class="text-indigo-600 hover:text-indigo-800 font-medium mr-4">Se connecter</a>
            <a href="{{ url_for('register') }}" class="text-green-600 hover:text-green-800 font-medium">S'inscrire</a>
        {% endif %}
    </div>
    <div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="px-4 py-2 rounded-lg {% if category == 'success' %}bg-green-100 text-green-700{% elif category in ['error', 'danger'] %}bg-red-100 text-red-700{% else %}bg-yellow-100 text-yellow-700{% endif %} shadow-sm">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>
</div>
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
""" + BASE_HEAD + """
<body class="bg-gray-50 min-h-screen p-4 sm:p-8">
""" + NAV_BAR + """
    <div class="max-w-4xl mx-auto">
        <header class="text-center py-6 bg-white shadow-lg rounded-xl mb-8">
            <h1 class="text-3xl font-extrabold text-indigo-700">Forum Python Simple</h1>
            <p class="text-gray-500 mt-1">Discussions simples avec Flask & SQLite.</p>
        </header>

        {% if current_user.is_authenticated %}
        <a href="{{ url_for('new_topic') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 transition duration-150 mb-6">
           + Créer un nouveau sujet
        </a>
        {% else %}
        <div class="p-4 bg-yellow-100 border border-yellow-300 text-yellow-800 rounded-lg mb-6">
            <p class="font-medium">Veuillez vous <a href="{{ url_for('login') }}" class="text-yellow-700 underline">connecter</a> pour participer.</p>
        </div>
        {% endif %}

        <div class="bg-white shadow-xl rounded-xl overflow-hidden">
            <h2 class="text-xl font-semibold p-4 border-b bg-gray-100 text-gray-800">Sujets Actifs</h2>
            {% if topics %}
                <ul class="divide-y divide-gray-200">
                    {% for topic in topics %}
                        <li class="p-4 hover:bg-indigo-50 transition duration-150">
                            <a href="{{ url_for('topic_detail', topic_id=topic.id) }}" class="block">
                                <div class="text-lg font-bold text-indigo-600 hover:text-indigo-800">{{ topic.title }}</div>
                                <div class="text-sm text-gray-500 mt-1 flex justify-between items-center">
                                    <span>Par <span class="font-semibold text-gray-700">{{ topic.author.username if topic.author else 'Anonyme' }}</span> le {{ topic.created_at.strftime('%d/%m/%Y à %H:%M') }}</span>
                                    <span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-medium rounded-full">
                                        {{ topic.posts.count() }} Messages
                                    </span>
                                </div>
                            </a>
                        </li>
                    {% endfor %}
                </ul>
            {% else %}
                <p class="p-6 text-gray-500 text-center">Aucun sujet pour le moment.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

TOPIC_DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
""" + BASE_HEAD + """
<body class="bg-gray-50 min-h-screen p-4 sm:p-8">
""" + NAV_BAR + """
    <div class="max-w-4xl mx-auto">
        <a href="{{ url_for('index') }}" class="text-indigo-600 hover:text-indigo-800 flex items-center mb-6">← Retour à l'accueil</a>

        <h1 class="text-3xl font-extrabold text-gray-900 mb-6">{{ topic.title }}</h1>

        <div class="space-y-4">
            {% for post in posts %}
                <div class="bg-white p-5 rounded-xl shadow-md border-t-4 {% if loop.index == 1 %}border-indigo-600{% else %}border-gray-200{% endif %}">
                    <div class="flex justify-between items-start mb-3">
                        <span class="text-sm font-semibold text-indigo-600">{{ post.author.username if post.author else 'Anonyme' }}</span>
                        <div class="flex items-center space-x-3">
                            <span class="text-xs text-gray-400">{{ post.created_at.strftime('%d/%m/%Y à %H:%M') }}</span>
                            {% if current_user.is_authenticated and current_user.id == post.user_id %}
                                <form action="{{ url_for('delete_post', post_id=post.id) }}" method="POST" onsubmit="return confirm('Supprimer ce message ?');" class="inline">
                                    <button type="submit" class="text-xs text-red-500 hover:text-red-700 font-medium ml-2">Supprimer</button>
                                </form>
                            {% endif %}
                        </div>
                    </div>
                    <div class="text-gray-700 whitespace-pre-wrap">{{ post.content }}</div>
                </div>
            {% endfor %}
        </div>

        <h2 class="text-2xl font-bold text-gray-800 mt-10 mb-4">Répondre</h2>
        {% if current_user.is_authenticated %}
            <div class="bg-white p-6 rounded-xl shadow-lg">
                <form method="POST">
                    {{ form.hidden_tag() }}
                    <div class="mb-4">
                        {{ form.content(rows=4, class_="form-input-field", placeholder="Votre réponse...") }}
                        {% for error in form.content.errors %} <span class="text-red-500 text-xs">{{ error }}</span> {% endfor %}
                    </div>
                    {{ form.submit(class_="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 cursor-pointer") }}
                </form>
            </div>
        {% else %}
            <div class="p-6 bg-red-50 text-red-800 rounded-xl text-center">Connectez-vous pour répondre.</div>
        {% endif %}
    </div>
</body>
</html>
"""

GENERIC_FORM_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
""" + BASE_HEAD + """
<body class="bg-gray-50 min-h-screen p-4 sm:p-8 flex items-center justify-center">
    <div class="w-full max-w-lg bg-white p-8 rounded-xl shadow-xl">
        <a href="{{ url_for('index') }}" class="text-indigo-600 mb-6 block">← Retour</a>
        <h1 class="text-2xl font-bold text-gray-900 mb-6 border-b pb-2">{{ title }}</h1>
        <form method="POST">
            {{ form.hidden_tag() }}
            {% for field in form if field.widget.input_type != 'hidden' and field.type != 'SubmitField' %}
                <div class="mb-5">
                    {{ field.label(class_="form-label") }}
                    {{ field(class_="form-input-field") }}
                    {% for error in field.errors %} <span class="text-red-500 text-xs">{{ error }}</span> {% endfor %}
                </div>
            {% endfor %}
            {{ form.submit(class_="w-full py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 cursor-pointer") }}
        </form>
    </div>
</body>
</html>
"""

# --- Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Compte créé !', 'success')
        return redirect(url_for('login'))
    return render_template_string(GENERIC_FORM_TEMPLATE, title='Inscription', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Connexion réussie.', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        flash('Identifiants invalides.', 'danger')
    return render_template_string(GENERIC_FORM_TEMPLATE, title='Connexion', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('Déconnexion réussie.', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    topics = Topic.query.order_by(Topic.created_at.desc()).all()
    return render_template_string(HOME_TEMPLATE, topics=topics)

@app.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic_detail(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    form = PostForm()
    if current_user.is_authenticated and form.validate_on_submit():
        new_post = Post(content=form.content.data, topic_id=topic.id, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Réponse publiée !', 'success')
        return redirect(url_for('topic_detail', topic_id=topic.id))
    posts = Post.query.filter_by(topic_id=topic_id).order_by(Post.created_at.asc()).all()
    return render_template_string(TOPIC_DETAIL_TEMPLATE, topic=topic, posts=posts, form=form)

@app.route('/new_topic', methods=['GET', 'POST'])
@login_required
def new_topic():
    form = NewTopicForm()
    if form.validate_on_submit():
        new_topic = Topic(title=form.title.data, user_id=current_user.id)
        db.session.add(new_topic)
        db.session.flush() # Récupère l'ID
        first_post = Post(content=form.content.data, topic_id=new_topic.id, user_id=current_user.id)
        db.session.add(first_post)
        db.session.commit()
        flash('Sujet créé !', 'success')
        return redirect(url_for('topic_detail', topic_id=new_topic.id))
    return render_template_string(GENERIC_FORM_TEMPLATE, title='Nouveau Sujet', form=form)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    
    topic_id = post.topic_id
    topic = Topic.query.get(topic_id)
    post_count = topic.posts.count()
    
    db.session.delete(post)
    db.session.commit()
    
    if post_count == 1 or topic.posts.count() == 0:
        db.session.delete(topic)
        db.session.commit()
        flash('Sujet supprimé (vide).', 'warning')
        return redirect(url_for('index'))
    
    flash('Message supprimé.', 'success')
    return redirect(url_for('topic_detail', topic_id=topic_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # En production, n'utilisez jamais "True" 
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)
