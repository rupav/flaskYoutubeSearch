from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


class Video(db.Model):
    """ Video Table """
    __tablename__ = "video"

    id = db.Column(db.String(20), primary_key=True)
    published_at = db.Column(db.DateTime, index=True)
    title = db.Column(db.String(80))
    desc = db.Column(db.String(255))

    def __repr__(self):
        return '<Video {}: {}>'.format(self.id, self.title)


class Thumbnail(db.Model):
    """ Thumbnail Table """
    __tablename__ = "thumbnail"

    id = db.Column(db.String(20), db.ForeignKey('video.id'), primary_key=True)
    type = db.Column(db.String(10), default="default", primary_key=True)
    url = db.Column(db.String(100))
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)

    video = db.relationship("Video", backref=db.backref('thumbnail'))


def connect_to_db(app, dbURI):
    """ Connect the database to our Flask app. """

    # Configure to use the database
    app.config['SQLALCHEMY_DATABASE_URI'] = dbURI
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.app = app
    db.init_app(app)
