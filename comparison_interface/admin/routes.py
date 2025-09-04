import json
import os
import shutil
from json.decoder import JSONDecodeError
from tempfile import TemporaryDirectory

import markdown
from flask import Response, current_app, redirect, render_template, request, send_file, url_for
from flask_security import auth_required
from marshmallow import ValidationError
from werkzeug.utils import secure_filename

from comparison_interface.admin import blueprint, forms
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.export import Exporter
from comparison_interface.db.models import Comparison, Participant, WebsiteControl
from comparison_interface.db.setup import Setup as DBSetup


@blueprint.route("/", methods=["GET"])
@auth_required("session", within=10)
def admin_root():
    """Redirect to admin/dashboard."""
    return redirect(url_for("admin.dashboard"))


@blueprint.route("/dashboard", methods=["GET"])
@auth_required("session", within=10)
def dashboard():
    """Show the admin dashboard."""
    form = forms.StartStudyForm()
    if db.session.query(WebsiteControl).count() == 1 and os.path.exists(
        os.path.join(current_app.root_path, db.session.query(WebsiteControl).first().configuration_file)
    ):
        current_app.config[WS.CONFIGURATION_LOCATION] = db.session.query(WebsiteControl).first().configuration_file
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
        active_study = True
    else:
        website_title = "No active study"
        active_study = False
    if active_study is False:
        data = {
            "website_title": website_title,
            "form": form,
        }
        return render_template("dashboard.html", **data)
    participant_count = db.session.query(Participant).count()
    if participant_count > 0:
        latest_registration = (
            db.session.query(Participant).order_by(Participant.participant_id.desc()).first().created_date
        )
        latest_registration_date = (
            f"{latest_registration.date()} {latest_registration.hour}:{latest_registration.minute}"
        )
    else:
        latest_registration_date = "No participants yet"
    date_created = db.session.query(WebsiteControl).first().setup_exec_date
    date_study_created = f"{date_created.date()} {date_created.hour}:{date_created.minute}"
    total_judgements = db.session.query(Comparison).count()
    skipped_judgements = db.session.query(Comparison).where(Comparison.state == "skipped").count()

    # get the pages we are expecting from the config
    local_file_edits = True
    if local_file_edits is True:
        edit_instructions = WS.should_render(WS.BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE, current_app)
        if edit_instructions and WS.configuration_has_key(WS.BEHAVIOUR_USER_INSTRUCTION_HTML, current_app):
            edit_instructions = False
        edit_ethics_agreement = WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, current_app)
        if edit_ethics_agreement and WS.configuration_has_key(WS.BEHAVIOUR_ETHICS_AGREEMENT_HTML, current_app):
            edit_ethics_agreement = False
        edit_site_policies = WS.should_render(WS.BEHAVIOUR_RENDER_SITE_POLICIES, current_app)
        if edit_site_policies and WS.configuration_has_key(WS.BEHAVIOUR_SITE_POLICIES_HTML, current_app):
            edit_site_policies = False
    if not edit_instructions and not edit_ethics_agreement and not edit_site_policies:
        local_file_edits = False

    data = {
        "date_study_created": date_study_created,
        "local_file_edits": local_file_edits,
        "edit_instructions": edit_instructions,
        "edit_ethics_agreement": edit_ethics_agreement,
        "edit_site_policies": edit_site_policies,
        "active_study": active_study,
        "website_title": website_title,
        "participant_count": participant_count,
        "latest_registration": latest_registration_date,
        "total_judgements": total_judgements,
        "skipped_judgements": skipped_judgements,
        "form": form,
    }

    return render_template("dashboard.html", **data)


@blueprint.route("/logged-out", methods=["GET"])
def logged_out():
    """Display a post log out page."""
    if WS.CONFIGURATION_LOCATION in current_app.config and current_app.config[WS.CONFIGURATION_LOCATION] is not None:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
        has_current_study = True
    else:
        website_title = "No active study"
        has_current_study = False
    data = {
        "logged_out": True,
        "has_current_study": has_current_study,
        "website_title": website_title,
    }
    return render_template("logged-out.html", **data)


@blueprint.route("/new-study", methods=["POST"])
@auth_required("session", within=10)
def new_study():
    """Start a new study by deleting any existing files and redirecting to setup-study."""
    form = forms.StartStudyForm()
    if form.deletion_confirmation.data is True:  # form validation prevents submission if not checked
        for filename in os.listdir(os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"])):
            filepath = os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"], filename)
            os.unlink(filepath)
        for filename in os.listdir(os.path.join(current_app.root_path, current_app.config["CONFIG_UPLOAD_DIR"])):
            filepath = os.path.join(current_app.root_path, current_app.config["CONFIG_UPLOAD_DIR"], filename)
            os.unlink(filepath)
        return redirect(url_for("admin.setup_study"))
    return redirect(url_for("admin.dashboard"))


@blueprint.route("/setup-study", methods=["GET", "POST"])
@auth_required("session", within=10)
def setup_study():
    """Set up a new study."""
    form = forms.CreateStudyForm()
    form.uploads_complete.data
    if form.uploads_complete.data == "true":
        uploaded_files = os.listdir(os.path.join(current_app.root_path, current_app.config["CONFIG_UPLOAD_DIR"]))
        if len(uploaded_files) == 1:
            conf_path = uploaded_files[0]
        else:
            conf_path = ''
        conf = os.path.join(current_app.config["CONFIG_UPLOAD_DIR"], conf_path)
        ConfigValidation(current_app).check_config_path(conf)
        WS.set_configuration_location(current_app, conf)
        ConfigValidation(current_app).validate()

        # 2. Configure database
        current_app.logger.info("Resetting website database")
        s = DBSetup(current_app)
        s.exec()
        return redirect(url_for("admin.dashboard"))
    if len(os.listdir(os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"]))) == 0:
        return redirect(url_for("admin.upload_images"))
    elif len(os.listdir(os.path.join(current_app.root_path, current_app.config["CONFIG_UPLOAD_DIR"]))) == 0:
        return redirect(url_for("admin.upload_config"))
    if WS.CONFIGURATION_LOCATION in current_app.config and current_app.config[WS.CONFIGURATION_LOCATION] is not None:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = "No active study"
    data = {
        "website_title": website_title,
        "form": form,
    }
    return render_template("create_study.html", **data)


@blueprint.route("/process", methods=["POST"])
@auth_required("session", within=10)
def process():
    """Filepond image uploader."""
    file_names = []
    for key in request.files:
        file = request.files[key]
        filename = secure_filename(file.filename)
        file_names.append(filename)
        try:
            file.save(os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"], filename))
        except Exception:
            print("save fail: " + filename)
    return json.dumps({"filename": [f for f in file_names]})


@blueprint.route("/revert", methods=["DELETE"])
@auth_required("session", within=10)
def revert():
    """Filepond image deletion."""
    basepath = os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"])
    try:
        parsed = json.loads(request.data)
        filename = secure_filename(parsed["filename"][0])
    except JSONDecodeError:
        filename = secure_filename(request.data.decode())
    filepath = os.path.normpath(os.path.join(basepath, filename))
    if not filepath.startswith(basepath):
        return Response("Access not permitted.", 403)
    try:
        os.remove(filepath)
    except Exception:
        print("delete fail: " + filename)
    return json.dumps({"filename": filename})


@blueprint.route("/load/<item>", methods=["GET"])
@auth_required("session", within=10)
def load(item):
    """Load the details of the currently uploaded images."""
    basepath = os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"])
    filename = secure_filename(item)
    filepath = os.path.normpath(os.path.join(basepath, filename))
    if not filepath.startswith(basepath):
        return Response("Access not permitted.", 403)
    return send_file(filepath)


@blueprint.route("/current-files", methods=["GET"])
@auth_required("session", within=10)
def current_files():
    """Get the filenames of the currently uploaded images."""
    dirpath = os.path.join(current_app.root_path, current_app.config["IMAGE_UPLOAD_DIR"])
    files = os.listdir(dirpath)
    return json.dumps({"filenames": "|".join(files)})


@blueprint.route("/upload-images", methods=["GET", "POST"])
@auth_required("session", within=10)
def upload_images():
    """Image uploading."""
    form = forms.ImageUploadForm()
    if request.method == "POST":
        return redirect(url_for("admin.setup_study"))
    # we may have been redirected here and if so we should clear the current config file because it will
    # have failed the validation
    for filename in os.listdir(os.path.join(current_app.root_path, current_app.config["CONFIG_UPLOAD_DIR"])):
        filepath = os.path.join(current_app.root_path, current_app.config["CONFIG_UPLOAD_DIR"], filename)
        os.unlink(filepath)
    if WS.CONFIGURATION_LOCATION in current_app.config and current_app.config[WS.CONFIGURATION_LOCATION] is not None:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = "No active study"
    data = {
        "website_title": website_title,
        "form": form,
    }
    return render_template("image-uploader.html", **data)


def process_image_errors(errors):
    """Organise the image errors for displaying on the screen."""
    processed_errors = {}
    missing_images = []
    for field in errors:
        for group_pos in errors[field]:
            group_number = group_pos + 1
            for item_pos in errors[field][group_pos]["items"]:
                item_number = item_pos + 1
                for subfield in errors[field][group_pos]["items"][item_pos]:
                    message = "; ".join(errors[field][group_pos]["items"][item_pos][subfield])
                    if "Image " in message and " not found " in message:
                        missing_images.append(message[6 : message.find(" not found ")])
                    else:
                        processed_errors[f"group {group_number}, item {item_number}, {subfield}"] = message
    return processed_errors, missing_images


def process_errors(errors):
    """Organise the errors for displaying on the screen."""
    processed_errors = {}
    all_missing_images = []
    for typ in errors:
        if typ == "groups":
            image_errors, missing_images = process_image_errors(errors)
        else:
            for field in errors[typ]:
                if typ in ["behaviourConfiguration", "websiteTextConfiguration"]:
                    processed_errors[field] = "; ".join(errors[typ][field])
                else:
                    image_errors, missing_images = process_image_errors(errors[typ])
        processed_errors.update(image_errors)
        all_missing_images.extend(missing_images)
    return processed_errors, all_missing_images


@blueprint.route("/upload-csv", methods=["GET", "POST"])
@auth_required("session", within=30)
def upload_csv():
    """Upload an image csv file."""
    form = forms.CsvUploadForm()
    if WS.CONFIGURATION_LOCATION in current_app.config and current_app.config[WS.CONFIGURATION_LOCATION] is not None:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = "No active study"
    data = {
        "website_title": website_title,
        "form": form,
    }
    if form.csv_file.data:
        if form.validate_on_submit():
            filename = secure_filename(form.csv_file.data.filename)
            relative_filepath = os.path.join(current_app.config["CONFIG_UPLOAD_DIR"], filename)
            filepath = os.path.join(current_app.root_path, relative_filepath)
            form.csv_file.data.save(filepath)
            # we need the config path set to the upload directory when dealing with csv based image configs
            ConfigValidation(current_app).check_config_path(current_app.config["CONFIG_UPLOAD_DIR"])
            WS.set_configuration_location(current_app, current_app.config["CONFIG_UPLOAD_DIR"])
            try:
                ConfigValidation(current_app).validate()
            except ValidationError as err:
                data["errors"], data["missing_images"] = process_errors(err.messages)
                WS.set_configuration_location(current_app, None)
                return render_template("csv-uploader.html", **data)
            return redirect(url_for("admin.setup_study"))
    return render_template("csv-uploader.html", **data)


@blueprint.route("/upload-config", methods=["GET", "POST"])
@auth_required("session", within=30)
def upload_config():
    """Upload a new config file."""
    form = forms.ConfigUploadForm()
    if WS.CONFIGURATION_LOCATION in current_app.config and current_app.config[WS.CONFIGURATION_LOCATION] is not None:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
    else:
        website_title = "No active study"
    data = {
        "website_title": website_title,
        "form": form,
    }
    if form.config_file.data:
        if form.validate_on_submit():
            filename = secure_filename(form.config_file.data.filename)
            relative_filepath = os.path.join(current_app.config["CONFIG_UPLOAD_DIR"], filename)
            filepath = os.path.join(current_app.root_path, relative_filepath)
            form.config_file.data.save(filepath)
            # we have to save it first because validation works off a file location
            ConfigValidation(current_app).check_config_path(relative_filepath)
            WS.set_configuration_location(current_app, relative_filepath)
            # if this also requires a csv file then redirect for that
            try:
                ConfigValidation(current_app).validate()
            except NotADirectoryError:
                return redirect(url_for("admin.upload_csv"))
            except ValidationError as err:
                data["errors"], data["missing_images"] = process_errors(err.messages)
                WS.set_configuration_location(current_app, None)
                return render_template("config-uploader.html", **data)
            return redirect(url_for("admin.setup_study"))
    return render_template("config-uploader.html", **data)


@blueprint.route("/export", methods=["POST"])
@auth_required("session", within=10)
def download_data():
    """Download the study database."""
    temp_dir = TemporaryDirectory()
    zip_path = os.path.join(temp_dir.name, "database_export")

    dir = Exporter(current_app).create_data_directory(temp_dir.name)
    shutil.make_archive(zip_path, "zip", dir)

    return send_file(f"{zip_path}.zip", download_name="downloaded_data.zip", as_attachment=True)


@blueprint.route("/edit-page", methods=["GET", "POST"])
@auth_required("session", within=10)
def edit_page():
    """Edit the markdown behind an html page."""
    form = forms.EditHtmlPageForm()
    folder = current_app.config["HTML_PAGES_DIR"]
    if form.md_text.data:
        md_text = form.md_text.data
        html = markdown.markdown(md_text)
        filename = form.page_type.data
        # save the text to the file
        with open(
            os.path.join(current_app.root_path, folder, f"{filename}.html"), mode="w", encoding="utf-8"
        ) as output:
            output.write(html)
        with open(os.path.join(current_app.root_path, folder, f"{filename}.md"), mode="w", encoding="utf-8") as output:
            output.write(md_text)

        return redirect(url_for("admin.dashboard"))
    else:
        form_data = {
            "page_type": form.page_type.data,
        }
        filename = form.page_type.data
        if os.path.exists(os.path.join(current_app.root_path, folder, f"{filename}.md")):
            with open(os.path.join(current_app.root_path, folder, f"{filename}.md"), mode="r") as input:
                current_text = input.read()
            form_data["current_text"] = current_text
        form = forms.EditHtmlPageForm(**form_data)
    if WS.CONFIGURATION_LOCATION in current_app.config and current_app.config[WS.CONFIGURATION_LOCATION] is not None:
        website_title = WS.get_text(WS.WEBSITE_TITLE, current_app)
        if filename == "instructions":
            page_name = WS.get_text(WS.PAGE_TITLE_INTRODUCTION, current_app)
        elif filename == "ethics":
            page_name = WS.get_text(WS.PAGE_TITLE_ETHICS_AGREEMENT, current_app)
        elif filename == "policies":
            page_name = WS.get_text(WS.PAGE_TITLE_POLICIES, current_app)
        else:
            page_name = filename
    else:
        website_title = "No active study"
        page_name = filename

    data = {
        "page_name": page_name,
        "website_title": website_title,
        "form": form,
    }
    return render_template("edit_page.html", **data)
