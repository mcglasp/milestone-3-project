import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_articles")
def get_articles():
    articles = list(mongo.db.articles.find())
    return render_template("articles.html", articles=articles)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    articles = list(mongo.db.articles.find({"$text": {"$search": query}}))
    return render_template("articles.html", articles=articles)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)
        
        # Put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration successful")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_article", methods=["GET", "POST"])
def add_article():
    if request.method == "POST":
        article = {
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "layout": request.form.get("layout"),
            "page_count": request.form.get("page_count"),
            "description": request.form.get("description"),
            "editor": request.form.get("editor"),
            "month": request.form.get("month"),
            "year": request.form.get("year")
        }
        
        mongo.db.articles.insert_one(article)
        flash("Article successfully added")
        return redirect(url_for("get_articles"))

    years = mongo.db.years.find().sort("years", 1)
    months = mongo.db.months.find().sort("months", 1)
    sections = mongo.db.sections.find().sort("sections", 1)
    editors = mongo.db.editors.find().sort("editors", 1)
    authors = mongo.db.authors.find().sort("authors", 1)
    return render_template("add_article.html", years=years, months=months, 
        sections=sections, editors=editors, authors=authors)

@app.route("/edit_article<article_id>", methods=["GET", "POST"])
def edit_article(article_id):
    if request.method == "POST":
        submit = {
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "layout": request.form.get("layout"),
            "page_count": request.form.get("page_count"),
            "description": request.form.get("description"),
            "editor": request.form.get("editor"),
            "month": request.form.get("month"),
            "year": request.form.get("year")
        }

        mongo.db.articles.update({"_id": ObjectId(article_id)}, submit)
        flash("Article successfully updated")

    article = mongo.db.articles.find_one({"_id": ObjectId(article_id)})

    articles = mongo.db.articles.find().sort("article", 1)
    years = mongo.db.years.find().sort("years", 1)
    months = mongo.db.months.find().sort("months", 1)
    sections = mongo.db.sections.find().sort("sections", 1)
    editors = mongo.db.editors.find().sort("editors", 1)
    authors = mongo.db.authors.find().sort("authors", 1)
    return render_template("edit_article.html", years=years, months=months, 
        sections=sections, editors=editors, authors=authors, article=article, articles=articles)


@app.route("/get_editors")
def get_editors():
    editors = list(mongo.db.editors.find().sort("editor", 1))
    return render_template("get_editors.html", editors=editors)


@app.route("/add_editor", methods=["GET", "POST"])
def add_editor():
    if request.method == "POST":
        editor = {
            "editor": request.form.get("editor")
        }
        mongo.db.editors.insert_one(editor)
        flash("New editor added")
        return redirect(url_for("get_editors"))

    return render_template("add_editor.html")


@app.route("/edit_editor/<editor_id>", methods=["GET","POST"])
def edit_editor(editor_id):
    if request.method == "POST":
        submit = {
            "editor": request.form.get("editor")
        }

        mongo.db.editors.update({"_id": ObjectId(editor_id)}, submit)
        flash("Category successfully updated")
        return redirect(url_for("get_editors"))

    editor = mongo.db.editors.find_one({"_id": ObjectId(editor_id)})
    return render_template("edit_editor.html", editor=editor)


@app.route("/delete_editor/<editor_id>")
def delete_editor(editor_id):
    mongo.db.editors.remove({"_id": ObjectId(editor_id)})
    flash("Editor deleted")
    return redirect(url_for("get_editors"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
