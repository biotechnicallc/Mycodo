from marshmallow_sqlalchemy import ModelSchema

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db

class Output(CRUDMixin, db.Model):
    __tablename__ = "recipe"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    
    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class OutputSchema(ModelSchema):
    class Meta:
        model = Recipe


