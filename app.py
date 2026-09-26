from flask import Flask
app= Flask(__name__)

@app.route("/")
def home():
    return "MCMT AI Assistant is running!"

if __name__ == "_main_":
    app.run(debug=True)