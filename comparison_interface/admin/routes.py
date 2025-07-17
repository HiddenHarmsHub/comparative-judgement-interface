import os
from flask import current_app, redirect, render_template, request, url_for
from flask_security import auth_required
from werkzeug.utils import secure_filename

from comparison_interface.admin import blueprint
from comparison_interface.admin import forms
from comparison_interface.configuration.website import Settings as WS


@blueprint.route('/dashboard', methods=['GET'])
@blueprint.route('/', methods=['GET'])
@auth_required('session', within=10)
def dashboard():
    """Show the admin dashboard."""
    config_upload_form = forms.ConfigUploadForm()
    image_upload_form = forms.ImageUploadForm()
    data = {
        "website_title": WS.get_text(WS.WEBSITE_TITLE, current_app),
        "config_upload_form": config_upload_form,
        "image_upload_form": image_upload_form,
    }
    return render_template("dashboard.html", **data)


@blueprint.route('/new-study', methods=['POST'])
@auth_required('session', within=10)
def new_study():
    """Start a new study by deleting any existing files and redirecting to setup-study."""
    for filename in os.listdir(os.path.join(current_app.root_path, current_app.config['IMAGE_UPLOAD_DIR'])):
        filepath = os.path.join(current_app.root_path, current_app.config['IMAGE_UPLOAD_DIR'], filename)
        os.unlink(filepath)
    for filename in os.listdir(os.path.join(current_app.root_path, current_app.config['CONFIG_UPLOAD_DIR'])):
        filepath = os.path.join(current_app.root_path, current_app.config['CONFIG_UPLOAD_DIR'], filename)
        os.unlink(filepath)
    return redirect(url_for("admin.setup_study"))


@blueprint.route('/setup-study', methods=['GET'])
@auth_required('session', within=10)
def setup_study():
    """Set up a new study."""
    if len(os.listdir(os.path.join(current_app.root_path, current_app.config['IMAGE_UPLOAD_DIR']))) == 0:
        return redirect(url_for("admin.upload_images"))
    elif len(os.listdir(os.path.join(current_app.root_path, current_app.config['CONFIG_UPLOAD_DIR']))) == 0:
        return redirect(url_for("admin.upload_config"))
    return


@blueprint.route('/upload-images', methods=['GET', 'POST'])
@auth_required('session', within=10)
def upload_images():
    """Image uploading."""
    form = forms.ImageUploadForm()
    print(form.image_files.data)
    if form.image_files.data:
        if form.validate_on_submit():
            for file in form.image_files.data:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.root_path, current_app.config['IMAGE_UPLOAD_DIR'], filename))
            return redirect(url_for("admin.setup_study"))
    data = {
        "website_title": WS.get_text(WS.WEBSITE_TITLE, current_app),
        "form": form,
    }
    return render_template("image-uploader.html", **data)


@blueprint.route('/upload-config', methods=['GET', 'POST'])
@auth_required('session', within=30)
def upload_config():
    """Upload a new config file."""
    form = forms.ConfigUploadForm()
    if form.config_file.data:
        if form.validate_on_submit():
            filename = secure_filename(form.config_file.data.filename)
            form.config_file.data.save(
                os.path.join(current_app.root_path, current_app.config['CONFIG_UPLOAD_DIR'], filename)
            )
            return redirect(url_for("admin.setup_study"))
    data = {
        "website_title": WS.get_text(WS.WEBSITE_TITLE, current_app),
        "form": form,
    }
    return render_template("config-uploader.html", **data)