import time
import secrets
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_socketio import SocketIO, join_room, emit
from models import db, Room, User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///netcall.db"
db.init_app(app)
socketio = SocketIO(app)

pending_calls = {}  # Step 53: remembers ringing calls {room code: start time}

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

@app.route("/api/create-room", methods=["GET", "POST"])
def api_create_room():
    code = secrets.token_hex(3)
    room = Room(code=code)
    db.session.add(room)
    db.session.commit()
    return jsonify({"code": code})

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        user = User(name=name, phone=phone)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("signup.html")

@app.route("/room/<code>")
def open_room(code):
    room = Room.query.filter_by(code=code).first_or_404()
    return render_template("room.html", code=room.code)

@socketio.on("enter")
def handle_enter(data):
    join_room(data["code"])
    started = pending_calls.get(data["code"])
    if started and time.time() - started < 60:
        emit("incoming")

@socketio.on("call")
def handle_call(data):
    pending_calls[data["code"]] = time.time()
    emit("incoming", to=data["code"], include_self=False)

@socketio.on("accept")
def handle_accept(data):
    pending_calls.pop(data["code"], None)
    emit("accepted", to=data["code"], include_self=False)

@socketio.on("decline")
def handle_decline(data):
    pending_calls.pop(data["code"], None)
    emit("declined", to=data["code"], include_self=False)

@socketio.on("signal")
def handle_signal(data):
    emit("signal", data["message"], to=data["code"], include_self=False)

if __name__ == "__main__":
    socketio.run(app, debug=True)