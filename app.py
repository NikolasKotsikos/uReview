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
    """
    Finds all genres and all platforms in the db and sorts them by name
    to display alphabetically in relevant carousel.
    """
    genres = list(mongo.db.genres.find().sort("genre_name", 1))
    platforms = list(mongo.db.platforms.find().sort("platform_name", 1))
    return render_template("index.html", genres=genres, platforms=platforms)


# search functionality
@app.route("/search", methods=["GET", "POST"])
def search():
    """
    Performs text index search on the reviews
    collection using the query variable.
    """
    query = request.form.get("query")
    reviews = list(mongo.db.reviews.find({"$text": {"$search": query}}))
    return render_template("reviews.html", reviews=reviews)


# create account functionality
@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        """Checks if the username already exists in db"""
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
            """Puts the new user into 'session' cookie"""
            session["user"] = request.form.get("username").lower()
            flash("Account Created Successfully!")
            return redirect(url_for("profile", username=session["user"]))

    return render_template("create_account.html")


# login-logout functionality
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        """Checks if the username exists in db"""
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            """Makes sure that the hashed password matches the users input"""
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))

            else:
                """Invalid password match"""
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            """Username doesn't exist"""
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Removes user from session cookie"""
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


# profile page functionality
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """Gets the session user's username from the database"""
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("profile.html", username=username)


# reviews functionality
@app.route("/get_reviews")
def get_reviews():
    """
    Finds all reviews in the database and sorts the cards
    chronologically with more recent items first based on
    the datetime info stored in '_id'
    """
    reviews = list(mongo.db.reviews.find().sort("_id", -1))
    return render_template("reviews.html", reviews=reviews)


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        """
        If post method is executed, creates a dictionary for form
        and inserts user input into the database
        """
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
        flash("Review Added Successfully!")
        return redirect(url_for("my_reviews"))

    """Sort form values in alphabetical order"""
    genres = mongo.db.genres.find().sort("genre_name", 1)
    platforms = mongo.db.platforms.find().sort("platform_name", 1)
    return render_template(
        "add_review.html", genres=genres, platforms=platforms)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        """
        If post method is executed, finds review by id
        and updates database with updated form input
        """
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
        return redirect(url_for("my_reviews"))

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    genres = mongo.db.genres.find().sort("genre_name", 1)
    platforms = mongo.db.platforms.find().sort("platform_name", 1)
    return render_template("edit_review.html",
                           review=review,
                           genres=genres,
                           platforms=platforms)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    """Finds review by id and removes it from the database"""
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Deleted Successfully")
    return redirect(url_for("get_reviews"))


@app.route("/read_review/<review_id>", methods=["GET"])
def read_review(review_id):
    """Finds review by id and direct to read_review template"""
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    return render_template("read_review.html", review=review)


@app.route("/my_reviews")
def my_reviews():
    """Finds review by  and direct to read_review template"""
    reviews = list(mongo.db.reviews.find({"created_by": session["user"]}))
    return render_template("my_reviews.html", reviews=reviews)


# genres functionality
@app.route("/add_genre", methods=["GET", "POST"])
def add_genre():
    """
    If post method is executed, creates a dictionary for form
    and inserts new genre name into the database
    """
    if request.method == "POST":
        genre = {
            "genre_name": request.form.get("genre_name")
        }
        mongo.db.genres.insert_one(genre)
        flash("Genre Added Successfully!")
        return redirect(url_for("get_genres"))

    return render_template("add_genre.html")


@app.route("/get_genres")
def get_genres():
    """
    Finds all genres in the database and sorts the cards
    alphabetically by genre name
    """
    genres = list(mongo.db.genres.find().sort("genre_name", 1))
    return render_template("genres.html", genres=genres)


@app.route("/edit_genre/<genre_id>", methods=["GET", "POST"])
def edit_genre(genre_id):
    """
    If post method is executed, finds genre by id
    and updates database with new form input
    """
    if request.method == "POST":
        submit = {
            "genre_name": request.form.get("genre_name")
        }
        mongo.db.genres.update({"_id": ObjectId(genre_id)}, submit)
        flash("Genre Edited Successfully!")
        return redirect(url_for("get_genres"))


@app.route("/delete_genre/<genre_id>")
def delete_genre(genre_id):
    """Finds genre by id and removes it from the database"""
    mongo.db.genres.remove({"_id": ObjectId(genre_id)})
    flash("Genre Deleted")
    return redirect(url_for("get_genres"))


@app.route("/find_genre/<genre_name>", methods=["GET", "POST"])
def find_genre(genre_name):
    """
    Returns a list of reviews that contain the specified genre name
    """
    reviews = list(mongo.db.reviews.find({"genre_name": genre_name}))
    return render_template("reviews.html", reviews=reviews)


# platforms functionality
@app.route("/add_platform", methods=["GET", "POST"])
def add_platform():
    """
    If post method is executed, creates a dictionary for form
    and inserts new platform name and img url into the database
    """
    if request.method == "POST":
        platform = {
            "platform_name": request.form.get("platform_name"),
            "img_url": request.form.get("img_url")
        }
        mongo.db.platforms.insert_one(platform)
        flash("Platform Added Successfully!")
        return redirect(url_for("get_platforms"))

    return render_template("add_platform.html")


@app.route("/get_platforms")
def get_platforms():
    """
    Finds all platforms in the database and sorts the cards
    alphabetically by platform name
    """
    platforms = list(mongo.db.platforms.find().sort("platform_name", 1))
    return render_template("platforms.html", platforms=platforms)


@app.route("/edit_platform/<platform_id>", methods=["GET", "POST"])
def edit_platform(platform_id):
    """
    If post method is executed, finds platform by id
    and updates database with new form inputs
    """
    if request.method == "POST":
        submit = {
            "platform_name": request.form.get("platform_name"),
            "img_url": request.form.get("img_url")
        }
        mongo.db.platforms.update({"_id": ObjectId(platform_id)}, submit)
        flash("Platform Edited Successfully!")
        return redirect(url_for("get_platforms"))


@app.route("/delete_platform/<platform_id>")
def delete_platform(platform_id):
    """Finds platform by id and removes it from the database"""
    mongo.db.platforms.remove({"_id": ObjectId(platform_id)})
    flash("Platform Deleted")
    return redirect(url_for("get_platforms"))


@app.route("/find_platform/<platform_name>", methods=["GET", "POST"])
def find_platform(platform_name):
    """
    Returns a list of reviews that contain the specified platform name
    """
    reviews = list(mongo.db.reviews.find({"platform": platform_name}))
    return render_template("reviews.html", reviews=reviews)


# 404 page function
@app.errorhandler(404)
def page_not_found(error):
    # the 404 status is set explicitly
    return render_template('404.html', title='404'), 404


# 500 page function
@app.errorhandler(500)
def internal_server(error):
    # the 500 status is set explicitly
    return render_template('500.html', title='500'), 500


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
