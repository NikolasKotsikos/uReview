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
@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/get_reviews")
def get_reviews():
    reviews = list(mongo.db.reviews.find())
    return render_template("reviews.html", reviews=reviews)


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("This username is taken")
            return redirect(url_for("create_account"))

        else:
            create_account = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            mongo.db.users.insert_one(create_account)
            # put the new user into 'session' cookie
            session["user"] = request.form.get("username").lower()
            flash("Account created successfuly!")
            return redirect(url_for("profile", username=session["user"]))

    return render_template("create_account.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from the database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("profile.html", username=username)


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        review = {
            "review_name": request.form.get("review_name"),
            "genre_name": request.form.get("genre_name"),
            "platform": request.form.get("platform"),
            "dev_name": request.form.get("dev_name"),
            "release_year": request.form.get("release_year"),
            "img_url": request.form.get("img_url"),
            "review_text": request.form.get("review_text"),
            "created_by": session["user"]
        }
        mongo.db.reviews.insert_one(review)
        flash("Review Added Successfuly!")
        return redirect(url_for("get_reviews"))

    genres = mongo.db.genres.find().sort("genre_name", 1)
    platforms = mongo.db.platforms.find().sort("platform_name", 1)
    return render_template(
        "add_review.html", genres=genres, platforms=platforms)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        submit = {
            "review_name": request.form.get("review_name"),
            "genre_name": request.form.get("genre_name"),
            "platform": request.form.get("platform"),
            "dev_name": request.form.get("dev_name"),
            "release_year": request.form.get("release_year"),
            "img_url": request.form.get("img_url"),
            "review_text": request.form.get("review_text"),
            "created_by": session["user"]
        }
        mongo.db.reviews.update({"_id": ObjectId(review_id)}, submit)
        flash("Review Edited, Changes Saved!")

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    genres = mongo.db.genres.find().sort("genre_name", 1)
    platforms = mongo.db.platforms.find().sort("platform_name", 1)
    return render_template("edit_review.html",
                           review=review,
                           genres=genres,
                           platforms=platforms)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Deleted Successfuly")
    return redirect(url_for("get_reviews"))


@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    if request.method == "POST":
        genre = {
            "genre_name": request.form.get("genre_name")
        }
        mongo.db.genres.insert_one(genre)
        flash("Genre Added Successfuly!")
        return redirect(url_for("get_genres"))

    return render_template("add_genre.html")


@app.route("/get_genres")
def get_genres():
    genres = list(mongo.db.genres.find().sort("genre_name", 1))
    return render_template("genres.html", genres=genres)


@app.route("/edit_genre/<genre_id>", methods=["GET", "POST"])
def edit_genre(genre_id):
    if request.method == "POST":
        submit = {
            "genre_name": request.form.get("genre_name")
        }
        mongo.db.genres.update({"_id": ObjectId(genre_id)}, submit)
        flash("Genre Edited Successfuly!")
        return redirect(url_for("get_genres"))


@app.route("/delete_genre/<genre_id>")
def delete_genre(genre_id):
    mongo.db.genres.remove({"_id": ObjectId(genre_id)})
    flash("Genre Deleted")
    return redirect(url_for("get_genres"))


@app.route("/find_genre/<genre_name>", methods=["GET", "POST"])
def find_genre(genre_name):
    reviews = list(mongo.db.reviews.find({"genre_name": genre_name}))
    return render_template("reviews.html", reviews=reviews)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
