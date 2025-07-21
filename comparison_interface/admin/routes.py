import os
import shutil
from tempfile import TemporaryDirectory

import markdown
from flask import current_app, redirect, render_template, send_file, url_for
from flask_security import auth_required
from werkzeug.utils import secure_filename

from comparison_interface.admin import blueprint, forms
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.export import Exporter
from comparison_interface.db.models import Comparison, Participant, WebsiteControl
from comparison_interface.db.setup import Setup as DBSetup


@blueprint.route('/dashboard', methods=['GET'])
@blueprint.route('/', methods=['GET'])
@auth_required('session', within=10)
def dashboard():
    """Show the admin dashboard."""
    print(db.session.query(WebsiteControl).count())
    if db.session.query(WebsiteControl).count() == 1:
        current_app.config[WS.CONFIGURATION_LOCATION] = db.session.query(WebsiteControl).first().configuration_file
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
        active_study = True
    else:
        website_title = 'No active study'
        active_study = False
    if not active_study:
        data = {
            "website_title": website_title,
        }
        return render_template("dashboard.html", **data)

    participant_count = db.session.query(Participant).count()
    if participant_count > 0:
        latest_registration = db.session.query(Participant).order_by(Participant.participant_id.desc()).first().created_date
    else:
        latest_registration = 'No participants yet'
    total_judgements = db.session.query(Comparison).count()
    skipped_judgements = db.session.query(Comparison).where(Comparison.state == 'skipped').count()
    # get the pages we are expecting from the config
    local_file_edits = True
    if local_file_edits is True:
        edit_instructions = WS.should_render(WS.BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE, current_app)
        edit_ethics_agreement = WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, current_app)
        edit_site_policies = WS.should_render(WS.BEHAVIOUR_RENDER_SITE_POLICIES, current_app)
    if not edit_instructions and not edit_ethics_agreement and not edit_site_policies:
        local_file_edits = False
    data = {
        "local_file_edits": local_file_edits,
        "edit_instructions": edit_instructions,
        "edit_ethics_agreement": edit_ethics_agreement,
        "edit_site_policies": edit_site_policies,
        "active_study": active_study,
        "website_title": website_title,
        "participant_count": participant_count,
        "latest_registration": latest_registration,
        "total_judgements": total_judgements,
        "skipped_judgements": skipped_judgements,
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


@blueprint.route('/setup-study', methods=['GET', 'POST'])
@auth_required('session', within=10)
def setup_study():
    print('+++++++++++++++++')
    print(current_app)
    form = forms.CreateStudyForm()
    """Set up a new study."""
    if form.deletion_confirmation.data is True:  # form validation prevents submission if not checked
        conf_file = os.listdir(os.path.join(current_app.root_path, current_app.config['CONFIG_UPLOAD_DIR']))[0]
        conf = os.path.join( current_app.config['CONFIG_UPLOAD_DIR'], conf_file)
        print(conf)
        ConfigValidation(current_app).check_config_path(conf)
        WS.set_configuration_location(current_app, conf)
        ConfigValidation(current_app).validate()

        # 2. Configure database
        current_app.logger.info("Resetting website database")
        s = DBSetup(current_app)
        s.exec()
        return redirect(url_for("admin.dashboard"))
    elif len(os.listdir(os.path.join(current_app.root_path, current_app.config['IMAGE_UPLOAD_DIR']))) == 0:
        return redirect(url_for("admin.upload_images"))
    elif len(os.listdir(os.path.join(current_app.root_path, current_app.config['CONFIG_UPLOAD_DIR']))) == 0:
        return redirect(url_for("admin.upload_config"))
    if WS.CONFIGURATION_LOCATION in current_app.config:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = 'No active study'
    data = {
        "website_title": website_title,
        "form": form,
    }
    return render_template("create_study.html", **data)


@blueprint.route('/upload-images', methods=['GET', 'POST'])
@auth_required('session', within=10)
def upload_images():
    """Image uploading."""
    form = forms.ImageUploadForm()
    if form.image_files.data:
        if form.validate_on_submit():
            for file in form.image_files.data:
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.root_path, current_app.config['IMAGE_UPLOAD_DIR'], filename))
            return redirect(url_for("admin.setup_study"))
    if WS.CONFIGURATION_LOCATION in current_app.config:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = 'No active study'
    data = {
        "website_title": website_title,
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
    if WS.CONFIGURATION_LOCATION in current_app.config:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = 'No active study'
    data = {
        "website_title": website_title,
        "form": form,
    }
    return render_template("config-uploader.html", **data)


@blueprint.route('/export', methods=['POST'])
@auth_required('session', within=10)
def download_data():
    """Download the study database."""
    temp_dir = TemporaryDirectory()
    zip_path = os.path.join(temp_dir.name, 'database_export')

    dir = Exporter(current_app).create_data_directory(temp_dir.name)
    shutil.make_archive(zip_path, 'zip', dir)

    return send_file(f'{zip_path}.zip', download_name='downloaded_data.zip', as_attachment=True)


@blueprint.route('/edit-page', methods=['GET', 'POST'])
@auth_required('session', within=10)
def edit_page():
    """Edit a html page."""
    form = forms.EditHtmlPageForm()
    dir = current_app.config['HTML_PAGES_DIR']
    if form.md_text.data:
        print('======')
        print(form.page_type.data)
        print('======')
        md_text = form.md_text.data
        html = markdown.markdown(md_text)
        filename = form.page_type.data
        # save the text to the file
        with open(os.path.join(current_app.root_path, dir, f'{filename}.html'), mode='w', encoding='utf-8') as output:
            output.write(html)
        with open(os.path.join(current_app.root_path, dir, f'{filename}.md'), mode='w', encoding='utf-8') as output:
            output.write(md_text)

        return redirect(url_for("admin.dashboard"))
    else:
        form_data = {
            "page_type": "instructions",
        }
        filename = "instructions"
        if os.path.exists(os.path.join(current_app.root_path, dir, f'{filename}.md')):
            with open(os.path.join(current_app.root_path, dir, f'{filename}.md'), mode='r') as input:
                current_text = input.read()
            form_data["current_text"] = current_text
        form = forms.EditHtmlPageForm(**form_data)
    if WS.CONFIGURATION_LOCATION in current_app.config:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = 'No active study'

    data = {
        "website_title": website_title,
        "form": form,
    }
    return render_template("edit_page.html", **data)
