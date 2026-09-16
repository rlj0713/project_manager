from flask import Flask, jsonify, render_template

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/test")
def api_test():
    return jsonify(message="API is working")


if __name__ == "__main__":
    app.run(debug=True)