# coding=utf-8
from marshmallow_sqlalchemy import ModelSchema

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class CustomController(CRUDMixin, db.Model):
    __tablename__ = "recipes"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, default='')
    Inputs = db.Column(db.Text, default='')
    Outputs = db.Column(db.Text, default='')
    Functions = db.Column(db.Text, default='')
    Custom_Options = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class FunctionSchema(ModelSchema):
    class Meta:
        model = Recipes

