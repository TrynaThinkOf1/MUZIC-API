#######################################
#       ZEVI BERLIN - 12/19/2024      #
#                                     #
#           Music Server API          #
#######################################

#########################
# IMPORT EXT. LIBRARIES
from flask import Flask, request
from flask_restful import Api, Resource, marshal_with, reqparse, fields, abort
from flask_sqlalchemy import SQLAlchemy
# IMPORT INCL. LIBRARIES
import secrets, hashlib
# IMPORT LOCAL LIBRARIES
#########################

#########################
#     INITIALIZATION
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databases.db'
db = SQLAlchemy(app)
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
    admin_key = db.Column(db.String, unique=True)
#########################

#########################
#    ARGS & PARSERS
song_get_args = reqparse.RequestParser()
song_get_args.add_argument('key', type=str, required=True)
song_get_args.add_argument('song_id', type=int)

song_post_args = reqparse.RequestParser()
song_post_args.add_argument('admin_key', type=str, required=True)
song_post_args.add_argument('gov_name', type=str, required=True)

song_patch_args = reqparse.RequestParser()
song_patch_args.add_argument('admin_key', type=str, required=True)
song_patch_args.add_argument('gov_name', type=str, required=True)

song_del_args = reqparse.RequestParser()
song_del_args.add_argument('admin_key', type=str, required=True)
#########################

#########################
#      DECORATORS
field_flavors = {
    "song_id": fields.Integer,
    "raw_key": fields.String
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
class SongResource(Resource):
    @marshal_with(field_flavors)
    def get(self):
        args = song_get_args.parse_args()
        song = SongDB.query.filter_by(id=args['song_id']).first()
        if not song:
            abort(404, message="Song not found")

        if hashKey(args['key']) not in Keys.query.all():
            abort(404, message="Key not valid")

        return song

    # ¡ ADMINS ONLY !
    @marshal_with(field_flavors)
    def post(self):
        args = song_post_args.parse_args()
        if not Keys.query.filter_by(admin_key=hashKey(args['admin_key'])).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        id = getNextSongID()
        gov_name = args['gov_name']
        nick_name = extract(args['gov_name'], 'nick_name')
        writer_name = extract(args['gov_name'],'writer_name')
        path = AHAHAHAHAHHAHFBJSAUFTDIUAKYGJHBKWDVUYFO8AGILU BHDGIAGKWJDBSVCUYO7TOYAIHLWJDS GCILAUWYO87ILUWAKYEH BD

        song = SongDB(id=id, gov_name=gov_name, nick_name=nick_name, writer_name=writer_name, path=path)
        db.session.add(song)
        db.session.commit()

        return song, 201

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

        if not Keys.query.filter_by(key=hashed_key).first():
            new_key = Keys(key=hashed_key)
            db.session.add(new_key)
            db.session.commit()

            return {"song_id": None, "raw_key": raw_key}, 201
        else:
            abort(409, message="Key already exists, try again. (WHAT ARE THE ODDS???!?!?!?!?!)")

#########################
#       ENDPOINTS
api.add_resource(SongResource, '/song')
api.add_resource(KeyResource, '/key')
#########################

#########################

#########################

#########################
if __name__ == "__main__":
    with app.app_context(): # UNCOMMENT ON INITIAL CREATION/RECREATION
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=6969) # ¡¡¡ DON'T RUN ON DEBUG WHEN IN PRODUCTION !!!