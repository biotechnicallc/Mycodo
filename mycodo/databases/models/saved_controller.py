# coding=utf-8
from marshmallow_sqlalchemy import ModelSchema

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Saved_Controller(CRUDMixin, db.Model):
    __tablename__ = "saved_controller"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    recipe_id = db.Column(db.String, nullable=False,default='')
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='Custom Function')
    position_y = db.Column(db.Integer, default=0)
    device = db.Column(db.Text, default='')

    is_activated = db.Column(db.Boolean, default=False)
    log_level_debug = db.Column(db.Boolean, default=False)

    custom_options = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)

class FunctionSchema(ModelSchema):
    class Meta:
        model = Saved_Controller