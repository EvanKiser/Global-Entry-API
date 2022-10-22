from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    resp = jsonify(health="healthy")
    resp.status_code = 200
    return resp

@app.route('/user', methods = ['POST'])
def add_user():
    return

@app.route("/guide/<id>", methods=["DELETE"])
def delete_user(id):
    return

@app.route("/locations", methods=["PUT"])
def update_locations():
    return

if __name__ == '__main__':
    app.debug = True
    app.run()