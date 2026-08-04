from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class SubjectForm(FlaskForm):
    name = StringField(
        "Subject Name",
        validators=[DataRequired(), Length(min=1, max=100)],
    )
    color = StringField(
        "Color",
        validators=[
            DataRequired(),
            Regexp(r"^#[0-9A-Fa-f]{6}$", message="Must be a valid hex color, e.g. #2563EB"),
        ],
        default="#2563EB",
    )
    icon = StringField("Icon", validators=[Length(max=50)])
    submit = SubmitField("Save Subject")