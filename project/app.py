from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "no elo. <h1>xDxDxD<h1>"

if __name__ == '__main__':
    app.run(debug=True)
