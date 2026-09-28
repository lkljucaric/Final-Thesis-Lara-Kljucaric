from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
from rag import pitaj_chatbota
import traceback

app = Flask(
    __name__,
    template_folder="html",
    static_folder=".",
    static_url_path="/static"
)

app.json.ensure_ascii = False


@app.route("/")
def pocetna_stranica():
    return render_template("chatbot.html")


@app.route("/favicon.ico")
def ikonica():
    return "", 204


@app.route("/ping")
def provjera_servera():
    return jsonify({
        "status": "OK",
        "message": "Flask radi."
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        podaci = request.get_json() or {}
        pitanje = podaci.get("message", "").strip()

        if pitanje == "":
            return jsonify({
                "answer": "Molim te upiši pitanje.",
                "sources": []
            })

        rezultat = pitaj_chatbota(pitanje)

        return jsonify(rezultat)

    except Exception:
        print(traceback.format_exc())

        return jsonify({
            "answer": "Dogodila se greška u Python kodu. Provjeri terminal u kojem je pokrenut Flask server.",
            "sources": []
        }), 500


@app.errorhandler(Exception)
def obradi_greske(greska):
    if isinstance(greska, HTTPException):
        return greska

    print(traceback.format_exc())

    return jsonify({
        "answer": "Dogodila se greška na serveru. Provjeri terminal u kojem je pokrenut Flask server.",
        "sources": []
    }), 500


if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)