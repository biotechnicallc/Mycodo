# coding=utf-8
from marshmallow_sqlalchemy import ModelSchema
from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import func


class Device(CRUDMixin, db.Model):
    __tablename__ = "device"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    device_id = db.Column(db.String, nullable=False, unique=True, default="")
    cloudflare_token = db.Column(db.String, nullable=False, default="")

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class DeviceSchema(ModelSchema):
    class Meta:
        model = Device

