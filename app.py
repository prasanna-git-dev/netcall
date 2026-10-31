import secrets
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
from models import db, Room

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///netcall.db"
db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create")
def create_room():
    code = secrets.token_hex(3)
    room = Room(code=code)
    db.session.add(room)
    db.session.commit()
    return redirect(url_for("open_room", code=code))

@app.route("/rooms")
def list_rooms():
    rooms = Room.query.all()
    return ", ".join(room.code for room in rooms)

@app.route("/room/<code>")
def open_room(code):
    room = Room.query.filter_by(code=code).first_or_404()
    return render_template("room.html", code=room.code)

@socketio.on("enter")
def handle_enter(data):
    join_room(data["code"])

@socketio.on("call")
def handle_call(data):
    emit("incoming", to=data["code"], include_self=False)

@socketio.on("accept")
def handle_accept(data):
    emit("accepted", to=data["code"], include_self=False)

@socketio.on("decline")
def handle_decline(data):
    emit("declined", to=data["code"], include_self=False)

@socketio.on("signal")
def handle_signal(data):
    emit("signal", data["message"], to=data["code"], include_self=False)

if __name__ == "__main__":
    socketio.run(app, debug=True)