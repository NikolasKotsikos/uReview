import os


@app.route("/")
def hello():
    return "uReview initial setup"


if __name__ == "__main__":
    app.run(host=os.environ.get("IP")
            port=os.environ.get("PORT")
            debug=True)


