from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Link(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    code = db.Column(db.String(16), unique=True, nullable=True)
    long_url = db.Column(db.Text, nullable=False)
