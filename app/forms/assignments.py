from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class AssignmentForm(FlaskForm):
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    due_date = DateTimeField("Due Date", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    priority = SelectField("Priority", choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium")
    status = SelectField(
        "Status",
        choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")],
        default="pending",
    )
    attachment = FileField(
        "Attachment",
        validators=[FileAllowed(["pdf", "docx", "pptx", "txt", "jpg", "jpeg", "png"], "Unsupported file type.")],
    )
    submit = SubmitField("Save Assignment")


class ExamForm(FlaskForm):
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    exam_date = DateTimeField("Exam Date & Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=255)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save Exam")