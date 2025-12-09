from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def index():
    if not os.path.exists("motion_log.txt"):
        open("motion_log.txt", "w", encoding="utf-8").close()

    with open("motion_log.txt", "r", encoding="utf-8") as f:
        logs = f.readlines()

    return render_template("index.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)
