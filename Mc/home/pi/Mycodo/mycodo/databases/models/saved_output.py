# coding=utf-8
from marshmallow_sqlalchemy import ModelSchema

from mycodo.databases import CRUDMixin
from mycodo.databases import set_uuid
from mycodo.mycodo_flask.extensions import db


class Saved_Output(CRUDMixin, db.Model):
    __tablename__ = "saved_output"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, unique=True, primary_key=True)
    recipe_id = db.Column(db.String, nullable=False,default='')
    unique_id = db.Column(db.String, nullable=False, unique=True, default=set_uuid)  # ID for influxdb entries
    output_type = db.Column(db.Text, default='wired')  # Options: 'command', 'wired', 'wireless_rpi_rf', 'pwm'
    name = db.Column(db.Text, default='Output')
    position_y = db.Column(db.Integer, default=0)
    size_y = db.Column(db.Integer, default=2)
    log_level_debug = db.Column(db.Boolean, default=False)

    # Interface options
    interface = db.Column(db.Text, default='')
    location = db.Column(db.Text, default='')

    # I2C1
    i2c_location = db.Column(db.Text, default=None)  # Address location for I2C communication
    i2c_bus = db.Column(db.Integer, default='')  # I2C bus the sensor is connected to

    # FTDI
    ftdi_location = db.Column(db.Text, default=None)  # Device location for FTDI communication

    # SPI
    uart_location = db.Column(db.Text, default=None)  # Device location for UART communication
    baud_rate = db.Column(db.Integer, default=None)  # Baud rate for UART communication

    custom_options = db.Column(db.Text, default='')

    def __repr__(self):
        return "<{cls}(id={s.id})>".format(s=self, cls=self.__class__.__name__)


class SavedOutputSchema(ModelSchema):
    class Meta:
        model = Saved_Output