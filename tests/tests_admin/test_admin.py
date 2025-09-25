import os
from datetime import datetime, timezone

from flask import url_for
from playwright.sync_api import expect
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError

from comparison_interface.db.connection import db
from comparison_interface.db.models import Comparison


def add_data():
    # add a participant
    participant_data = {
        'name': 'Tester One',
        'country': 'England',
        'allergies': 'Yes',
        'age': '30',
        'email': 'dummy@test',
        'accepted_ethics_agreement': '1',
    }
    participant_data['created_date'] = datetime(2025, 4, 5)
    db_engine = db.engines['study_db']
    db_meta = MetaData()
    db_meta.reflect(bind=db_engine)
    table = db_meta.tables["participant"]
    new_participant_sql = table.insert().values(**participant_data)
    try:
        # Insert the participant into the database
        with db_engine.begin() as connection:
            connection.execute(new_participant_sql)
    except SQLAlchemyError as e:
        raise RuntimeError(str(e))
    db.session.commit
    # add some comparisons
    comparison_data_list = [
        {
            'participant_id': 1,
            'item_1_id': 1,
            'item_2_id': 2,
            'selected_item_id': 1,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'participant_id': 1,
            'item_1_id': 3,
            'item_2_id': 1,
            'selected_item_id': 1,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'participant_id': 1,
            'item_1_id': 4,
            'item_2_id': 3,
            'selected_item_id': None,
            'state': 'skipped',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
    ]
    for comparison_data in comparison_data_list:
        comparison = Comparison(**comparison_data)
        db.session.add(comparison)
    db.session.commit()


def test_admin_page_requires_login(live_server, page):
    """
    GIVEN a flask app configured for testing and with ADMIN_ACCESS set to True
    WHEN the admin dashboard is requested by someone who is not logged in
    THEN the user is redirected to the login page
    """
    page.goto(url_for("admin.dashboard", _external=True))
    # should send us to login instead
    expect(page).to_have_url(url_for("security.login", _external=True) + "?next=/admin/dashboard")
    expect(page.locator("#email")).to_be_visible()
    expect(page.locator("#password")).to_be_visible()


def test_dashboard_displayed_when_logged_in(live_server, page):
    """
    GIVEN a flask app configured for testing and with ADMIN_ACCESS set to True
    WHEN the a user goes to the login page and logs in
    THEN the user is redirected to the admin dashboard page
    """
    # login
    page.goto(url_for("security.login", _external=True))
    page.get_by_label("Email Address").fill("test@example.co.uk")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()
    # should redirect to dashboard
    expect(page).to_have_url(url_for("admin.dashboard", _external=True))


def test_dashboard_content(live_server, page):
    """
    GIVEN a flask app configured for testing and with ADMIN_ACCESS set to True
    WHEN the a logged in user goes to the admin dashboard
    THEN the user sees current project stats and buttons for editing html pages and setting up a new study
    """
    add_data()
    # login (not part of test)
    page.goto(url_for("security.login", _external=True))
    page.get_by_label("Email Address").fill("test@example.co.uk")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()
    # test features of dashboard
    # the stats are showing correctly
    expect(page.get_by_text("Total Participants: 1")).to_be_visible()
    expect(page.get_by_text("Total Judgements: 3")).to_be_visible()
    expect(page.get_by_text("Skipped Judgements: 1")).to_be_visible()
    # only the correct pages are available for editing
    expect(page.get_by_role("button", name="Edit Instructions")).to_be_visible()
    expect(page.get_by_role("button", name="Edit Ethics Agreement")).to_be_visible()
    expect(page.get_by_role("button", name="Edit Site Polices")).not_to_be_visible()
    # there is a button to start a new study
    expect(page.get_by_role("button", name="Start New Study")).to_be_visible()


def test_new_study_requires_extra_check(live_server, page):
    """
    GIVEN a flask app configured for testing and with ADMIN_ACCESS set to True
    WHEN a logged in user start a new study but has not checked the box
    THEN the a new study is not started
    """
    # login (not part of test)
    page.goto(url_for("security.login", _external=True))
    page.get_by_label("Email Address").fill("test@example.co.uk")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()
    # start a new study
    page.get_by_role("button", name="Start New Study").click()
    # we should start with image uploads
    expect(page).not_to_have_url(url_for("admin.upload_images", _external=True))


def test_new_study_route_json_only(live_server, page):
    """
    GIVEN a flask app configured for testing and with ADMIN_ACCESS set to True
    WHEN a logged in user starts a new study
    THEN they are guided through the correct path to upload the files needed for a study
    """
    # login (not part of test)
    page.goto(url_for("security.login", _external=True))
    page.get_by_label("Email Address").fill("test@example.co.uk")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()
    # start a new study and check the confirmation box
    page.locator("#deletion_confirmation").check()
    page.get_by_role("button", name="Start New Study").click()
    # we should start with image uploads
    expect(page).to_have_url(url_for("admin.upload_images", _external=True))
    expect(page.get_by_text("Browse")).to_be_visible()
    # to get further we need to do some manipulation behind the scenes
    with open(
        os.path.join(live_server.app.root_path, live_server.app.config["IMAGE_UPLOAD_DIR"], "item_1.png"), mode="w"
    ) as _:
        pass
    page.get_by_role("button", name="Confirm").click()
    # now we have "uploaded" images we should be sent to the config file upload
    expect(page).to_have_url(url_for("admin.upload_config", _external=True))
    file_selector = page.locator('input[name="config_file"]')
    file_selector.set_input_files(os.path.join(live_server.app.root_path, "examples/config-equal-item-weights.json"))
    page.get_by_role("button", name="Upload").click()
    # now we should be on the setup study page with the create new study button available
    expect(page).to_have_url(url_for("admin.setup_study", _external=True))
    expect(page.get_by_role("button", name="Create New Study")).to_be_visible()


def test_new_study_route_json_and_csv(live_server, page):
    """
    GIVEN a flask app configured for testing and with ADMIN_ACCESS set to True
    WHEN a logged in user starts a new study
    THEN they are guided through the correct path to upload the files needed for a study
    """
    # login (not part of test)
    page.goto(url_for("security.login", _external=True))
    page.get_by_label("Email Address").fill("test@example.co.uk")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()
    # start a new study and check the confirmation box
    page.locator("#deletion_confirmation").check()
    page.get_by_role("button", name="Start New Study").click()
    # we should start with image uploads
    expect(page).to_have_url(url_for("admin.upload_images", _external=True))
    expect(page.get_by_text("Browse")).to_be_visible()
    # to get further we need to do some manipulation behind the scenes
    with open(
        os.path.join(live_server.app.root_path, live_server.app.config["IMAGE_UPLOAD_DIR"], "item_1.png"), mode="w"
    ) as _:
        pass
    page.get_by_role("button", name="Confirm").click()
    # now we have "uploaded" images we should be sent to the config file upload
    expect(page).to_have_url(url_for("admin.upload_config", _external=True))
    file_selector = page.locator('input[name="config_file"]')
    file_selector.set_input_files(
        os.path.join(live_server.app.root_path, "examples/csv_example/config-equal-item-weights.json")
    )
    page.get_by_role("button", name="Upload").click()
    # now we should be on the upload csv page
    expect(page).to_have_url(url_for("admin.upload_csv", _external=True))
    file_selector = page.locator('input[name="csv_file"]')
    file_selector.set_input_files(os.path.join(live_server.app.root_path, "examples/csv_example/example.csv"))
    page.get_by_role("button", name="Upload").click()

    # now we should be on the setup study page with the create new study button available
    expect(page).to_have_url(url_for("admin.setup_study", _external=True))
    expect(page.get_by_role("button", name="Create New Study")).to_be_visible()
