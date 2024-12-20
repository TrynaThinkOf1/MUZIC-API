#######################################
#       ZEVI BERLIN - 12/19/2024      #
#                                     #
#           Music Server API          #
#######################################

#########################
# IMPORT EXT. LIBRARIES
from flask import Flask, request, jsonify
from flask_restful import Api, Resource, marshal_with, reqparse, fields, abort
from flask_sqlalchemy import SQLAlchemy
# IMPORT INCL. LIBRARIES
import secrets, hashlib, os

from werkzeug.utils import send_file

# IMPORT LOCAL LIBRARIES
#########################

#########################
#     INITIALIZATION
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databases.db'
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'songs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#########################

#########################
#       DATABASES
class SongDB(db.Model):
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    gov_name = db.Column(db.String, nullable=False)
    nick_name = db.Column(db.String, nullable=False)
    writer_name = db.Column(db.String, nullable=False)
    path = db.Column(db.String, nullable=False)

    def __repr__(self):
        return "<Song {}>".format(self.id)

class Keys(db.Model):
    key = db.Column(db.String, unique=True, primary_key=True)
    name = db.Column(db.String, nullable=False)

    admin_key = db.Column(db.String, unique=True)
#########################

#########################
#    ARGS & PARSERS
song_get_args = reqparse.RequestParser()
#song_get_args.add_argument('key', type=str, required=True)
song_get_args.add_argument('song_id', type=int)

song_post_args = reqparse.RequestParser()
song_post_args.add_argument('admin_key', type=str, required=True)
song_post_args.add_argument('gov_name', type=str, required=True)

song_patch_args = reqparse.RequestParser()
song_patch_args.add_argument('admin_key', type=str, required=True)
song_patch_args.add_argument('gov_name', type=str, required=True)

song_del_args = reqparse.RequestParser()
song_del_args.add_argument('admin_key', type=str, required=True)

key_post_args = reqparse.RequestParser()
key_post_args.add_argument('name', type=str, required=True)
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
def getNextSongID():
    max_id = db.session.query(db.func.max(SongDB.id)).scalar()
    return (max_id + 1) if max_id is not None else 0

def extract(gov_name, type):
    if type == "nick_name":
        nick_name = gov_name.split("-")[0].lower()
        return nick_name
    elif type == "writer_name":
        writer_name = gov_name.split("-")[1].lower()
        return writer_name

def hashKey(key):
    hashed_key = hashlib.sha256(key.encode("utf8")).hexdigest()
    return hashed_key

def fileAllowed(file):
    allowed_exts = ["mp3", "wav"]

    return "." in file and file.split(".")[-1] in allowed_exts
#########################

#########################
#       RESOURCES
class GetSong(Resource):
    @marshal_with(field_flavors)
    def get(self):
        args = song_get_args.parse_args()
        song = SongDB.query.filter_by(id=args['song_id']).first()
        if not song:
            abort(404, message="Song not found")

        #if hashKey(args['key']) not in Keys.query.all():
            #abort(404, message="Key not valid")

        #if not os.path.exists(song.path):
            #return jsonify({"message": "File not found"}), 404

        return song #send_file(song.path, mimetype="audio/mpeg")

# ¡ ADMINS ONLY !
class PostSong(Resource):
    @marshal_with(field_flavors)
    def post(self):
        args = song_post_args.parse_args()
        if not Keys.query.filter_by(admin_key=hashKey(args['admin_key'])).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        # FILE STUFF
        if 'file' not in request.files:
            return jsonify({"message": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"message": "No selected file"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        #########

        id = getNextSongID()
        gov_name = args['gov_name']
        nick_name = extract(args['gov_name'], 'nick_name')
        writer_name = extract(args['gov_name'],'writer_name')

        song = SongDB(id=id, gov_name=gov_name, nick_name=nick_name, writer_name=writer_name, path=filepath)
        db.session.add(song)
        db.session.commit()

        return song, 201

class PatchSong(Resource):
    @marshal_with(field_flavors)
    def patch(self):
        args = song_patch_args.parse_args()
        if not Keys.query.filter_by(admin_key=hashKey(args['admin_key'])).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        song = SongDB.query.filter_by(id=args['song_id']).first()
        if not song:
            abort(404, message="Song not found")

        if args['gov_name'] != song.gov_name:
            song.gov_name = args['gov_name']
            song.nick_name = extract(args['gov_name'], 'nick_name')
            song.writer_name = extract(args['gov_name'], 'writer_name')

        db.session.commit()

        return song, 200

class DeleteSong(Resource):
    def delete(self):
        args = song_del_args.parse_args()
        if not Keys.query.filter_by(admin_key=hashKey(args['admin_key'])).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        result = SongDB.query.filter_by(id=args['song_id']).first()
        if not result:
            abort(404, message="Song not found")

        db.session.delete(result)
        db.session.commit()

        return "", 204

class KeyResource(Resource):
    @marshal_with(field_flavors)
    def post(self):
        raw_key = secrets.token_hex(32)
        hashed_key = hashKey(raw_key)
        args = key_post_args.parse_args()

        if not Keys.query.filter_by(key=hashed_key).first():
            new_key = Keys(key=hashed_key, name=args['name'])
            db.session.add(new_key)
            db.session.commit()

            return {"song_id": None, "raw_key": raw_key}, 201
        else:
            abort(409, message="Key already exists, try again. (WHAT ARE THE ODDS???!?!?!?!?!)")

#########################
#       ENDPOINTS
api.add_resource(GetSong, '/song/get')
api.add_resource(PostSong, '/song/post')
api.add_resource(PatchSong, '/song/patch')
api.add_resource(DeleteSong, '/song/delete')

api.add_resource(KeyResource, '/key/create')
#########################

#########################

#########################

#########################
if __name__ == "__main__":
    #with app.app_context(): # UNCOMMENT ON INITIAL CREATION/RECREATION
        #db.drop_all()
        #db.create_all()
    app.run(debug=True, host="0.0.0.0", port=6969) # ¡¡¡ DON'T RUN ON DEBUG WHEN IN PRODUCTION !!!