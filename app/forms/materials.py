from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class UploadMaterialForm(FlaskForm):
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    file = FileField("File", validators=[FileRequired(message="Please choose a file to upload.")])
    submit = SubmitField("Upload")