from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def index():
    # Nếu file chưa tồn tại → tạo file trống UTF-8
    if not os.path.exists("motion_log.txt"):
        open("motion_log.txt", "w", encoding="utf-8").close()

    with open("motion_log.txt", "r", encoding="utf-8") as f:
        logs = f.readlines()

    return render_template("index.html", logs=logs)

app.run(debug=True)
