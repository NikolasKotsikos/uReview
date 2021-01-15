import os

from flask import Flask
if os.path.exists("env.py"):
    import env


@app.route("/")
def hello():
    return "uReview initial setup"


if __name__ == "__main__":
    app.run(host=os.environ.get("IP")
            port=os.environ.get("PORT")
            debug=True)


