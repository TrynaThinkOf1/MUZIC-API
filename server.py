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
import pathlib
# IMPORT LOCAL LIBRARIES
#########################

#########################
#     INITIALIZATION
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///songs.db'
db = SQLAlchemy(app)

songs_dir = pathlib.Path(__file__).parent / "songs"
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
    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    key = db.Column(db.String, unique=True, nullable=False)
    admin_key = db.Column(db.String, unique=True, nullable=False)
#########################

#########################
#    ARGS & PARSERS
song_get_args = reqparse.RequestParser()
song_get_args.add_argument('key', type=str, required=True)
song_get_args.add_argument('song_id', type=int)
#########################

#########################
#      DECORATORS
field_flavors = {
    "key": fields.String,
    "song_id": fields.Integer
}

# TODO: ADD A WRAPPER FUNCTION TO REQUIRE KEY
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
#########################

#########################
#       RESOURCES
class SongResource(Resource):
    @marshal_with(field_flavors)
    def get(self, song_id):
        key = song_get_args.parse_args()['key']
        song = SongDB.query.filter_by(id=song_id).first()
        if not song:
            abort(404, message="Song not found")

        if key not in Keys.query.all():
            abort(404, message="Key not valid")

        return song

    # ¡ ADMINS ONLY !
    @marshal_with(field_flavors)
    def post(self, gov_name):
        args = song_get_args.parse_args()
        if not Keys.query.filter_by(admin_key=args['key']).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        id = getNextSongID()
        gov_name = args['gov_name']
        nick_name = extract(args['gov_name'], 'nick_name')
        writer_name = extract(args['gov_name'],'writer_name')
        path = None #TODO: Figure out path shit

        song = SongDB(id=id, gov_name=gov_name, nick_name=nick_name, writer_name=writer_name, path=path)
        db.session.add(song)
        db.session.commit()

        return song, 201

    @marshal_with(field_flavors)
    def put(self, song_id):
        args = song_get_args.parse_args()
        if not Keys.query.filter_by(admin_key=args['key']).first():
            abort(403, message="You're not allowed to do that, silly billy!")

        song = SongDB.query.filter_by(id=song_id).first()
        if not song:
            abort(404, message="Song not found")

        if args['gov_name'] != song.gov_name:
            song.gov_name = args['gov_name']
            song.nick_name = extract(args['gov_name'], 'nick_name')
            song.writer_name = extract(args['gov_name'], 'writer_name')

        db.session.commit()

        return song, 200
#########################
#       ENDPOINTS
api.add_resource(SongResource, '/songs/<int:song_id>')
#########################

#########################

#########################

#########################
if __name__ == "__main__":
    with app.app_context(): # UNCOMMENT ON INITIAL CREATION/RECREATION
        db.create_all() #        ^
    app.run(debug=True, host="0.0.0.0", port=6969) # ¡¡¡ DON'T RUN ON DEBUG WHEN IN PRODUCTION !!!