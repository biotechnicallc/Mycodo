# coding=utf-8
from marshmallow_sqlalchemy import ModelSchema
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func


class Recipes(CRUDMixin, db.Model):
    __tablename__ = "recipes"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    recipe_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)
    name = db.Column(db.Text, nullable=False, default="Name")
    icon = db.Column(db.Text, nullable=False, default="default.png")
    current = db.Column(db.Boolean ,nullable=False,default=False)
    enabled = db.Column(db.Boolean ,nullable=False,default=False)
    start_date = db.Column(db.DATETIME,nullable=False,default=func.func.now())
    end_date = db.Column(db.DATETIME, nullable=False,default=func.func.now())
    
    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class FunctionSchema(ModelSchema):
    class Meta:
        model = Recipes

