#######################################
#       ZEVI BERLIN - 12/21/2024      #
#                                     #
#           Music Server API          #
#######################################

#########################
# IMPORT EXT. LIBRARIES
from flask import Flask, request, jsonify, send_file
from flask_restful import Api, Resource, marshal_with, reqparse, fields, abort
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
# IMPORT INCL. LIBRARIES
import secrets, hashlib, os, mimetypes

# IMPORT LOCAL LIBRARIES
#########################

#########################
#     INITIALIZATION
app = Flask(__name__)
api = Api(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///databases.db"
db = SQLAlchemy(app)

UPLOAD_FOLDER = "songs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

cache = Cache(app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 600}) # im on the fence about whether this belongs in the "DECORATORS" subdivide
#########################

#########################
#       DATABASES
class SongDB(db.Model):
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True, autoincrement=True)
    gov_name = db.Column(db.String, nullable=False)
    nick_name = db.Column(db.String, nullable=False)
    writer_name = db.Column(db.String, nullable=False)
    path = db.Column(db.String, nullable=False)

    def __repr__(self):
        return "<Song {}>".format(self.id)

class Keys(db.Model):
    key = db.Column(db.String, unique=True, primary_key=True)
    admin_key = db.Column(db.String, unique=True)
#########################

#########################
#    ARGS & PARSERS
song_patch_args = reqparse.RequestParser()
song_patch_args.add_argument("admin_key", type=str, required=True)
song_patch_args.add_argument("gov_name", type=str, required=True)

song_del_args = reqparse.RequestParser()
song_del_args.add_argument("admin_key", type=str, required=True)

key_post_args = reqparse.RequestParser()
key_post_args.add_argument("name", type=str, required=True)
#########################

#########################
#      DECORATORS
field_flavors = {
    "song_id": fields.Integer,
    "gov_name": fields.String,
    "nick_name": fields.String,
    "writer_name": fields.String,

    "raw_key": fields.String,
    "name": fields.String
}
#########################

#########################
#     HELPER FUNCS
def extract(gov_name, type):
    if type == "nick_name":
        nick_name = gov_name.split("-")[0].lower()
        return nick_name
    elif type == "writer_name":
        writer_name = gov_name.split("-")[1].lower()
        return writer_name

def createKey():
    raw_key = secrets.token_hex(32)
    return raw_key

def hashKey(key):
    hashed_key = hashlib.sha256(key.encode("utf8")).hexdigest()
    return hashed_key

def fileAllowed(file):
    allowed_exts = ["mp3", "wav", "m4a"]
    ext = file.rsplit(".", 1)[-1].lower() if "." in file else ""
    mime_type = mimetypes.guess_type(file)
    if ext in allowed_exts and mime_type in ["audio/mpeg", "audio/wav"]:
        return True
    return False
#########################

#########################
#       RESOURCES
class GetSong(Resource):
    @cache.cached()
    @marshal_with(field_flavors)
    def get(self, song_id):
        song = SongDB.query.filter_by(id=song_id).first()
        if not song:
            abort(404, message="Song not found")

        if not os.path.exists(song.path):
            return jsonify({"message": "File not found"}), 404

        return send_file(song.path, mimetype="audio/mpeg")

# ¡ ADMINS ONLY !
class PostSong(Resource):
    @marshal_with(field_flavors)
    def post(self):
        key = request.form.get("key")
        gov_name = request.form.get("gov_name")

        if not Keys.query.filter_by(admin_key=hashKey(key)).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        nick_name = extract(gov_name, "nick_name")
        writer_name = extract(gov_name, "writer_name")

        if "file" not in request.files:
            return jsonify({"message": "No file part"}), 400

        file = request.files.get("file")

        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        if not fileAllowed(file):
            return jsonify({"message": "Forbidden file"}), 403


        song = SongDB(gov_name=gov_name, nick_name=nick_name, writer_name=writer_name, path="")
        db.session.add(song)
        db.session.flush()

        filepath = os.path.join(UPLOAD_FOLDER, f"{id}.{file.filename.rsplit('.', 1)[-1]}")

        try:
            file.save(filepath)
            song.path = filepath
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            os.remove(filepath)
            return jsonify({"message": str(e)}), 500

        return song, 201

class PatchSong(Resource):
    @marshal_with(field_flavors)
    def patch(self):
        args = song_patch_args.parse_args()
        if not Keys.query.filter_by(admin_key=hashKey(args["admin_key"])).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        song = SongDB.query.filter_by(id=args["song_id"]).first()
        if not song:
            abort(404, message="Song not found")

        if args["gov_name"] != song.gov_name:
            song.gov_name = args["gov_name"]
            song.nick_name = extract(args["gov_name"], "nick_name")
            song.writer_name = extract(args["gov_name"], "writer_name")

        db.session.commit()

        return song, 200

class DeleteSong(Resource):
    def delete(self):
        args = song_del_args.parse_args()
        if not Keys.query.filter_by(admin_key=hashKey(args["admin_key"])).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        result = SongDB.query.filter_by(id=args["song_id"]).first()
        if not result:
            abort(404, message="Song not found")

        db.session.delete(result)
        db.session.commit()

        return "", 204

class IndexSongs(Resource):
    @cache.cached()
    @marshal_with(field_flavors)
    def get(self):
        songs = SongDB.query.all()

        song_list = [
            {
                "id": song.id,
                "gov_name": song.gov_name,
                "nick_name": song.nick_name,
                "writer_name": song.writer_name,
            }
            for song in songs
        ]

        return jsonify(song_list), 200

#########################
#       ENDPOINTS
api.add_resource(GetSong, "/song/get/<int:song_id>")
api.add_resource(PostSong, "/song/post")
api.add_resource(PatchSong, "/song/patch")
api.add_resource(DeleteSong, "/song/delete")

api.add_resource(IndexSongs, "/song/index/all")
#########################

#########################
if __name__ == "__main__":
    #with app.app_context(): # UNCOMMENT ON INITIAL CREATION/RECREATION
        #db.drop_all()
        #db.create_all()
    app.run(host="0.0.0.0", port=6969) # ¡¡¡ DON"T RUN ON DEBUG WHEN IN PRODUCTION !!!