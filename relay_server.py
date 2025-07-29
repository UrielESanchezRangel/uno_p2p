# relay_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)
salas = {}

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    codigo = data["codigo"]
    ip = data["ip"]
    salas[codigo] = ip
    return jsonify({"status": "registrado"})

@app.route("/sala/<codigo>", methods=["GET"])
def obtener_ip(codigo):
    if codigo in salas:
        return jsonify({"ip": salas[codigo]})
    return jsonify({"error": "No encontrada"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
