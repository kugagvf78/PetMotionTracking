from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def index():
    with open("motion_log.txt", "r") as f:
        logs = f.readlines()
    return render_template("index.html", logs=logs)

app.run(debug=True)
