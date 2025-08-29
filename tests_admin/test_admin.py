from flask import url_for
from playwright.sync_api import expect


def test_registration_page_loads(live_server, page):
    page.goto(url_for('main.participant_registration', _external=True))
    expect(page).to_have_title('Comparison Software: User Registration')


def test_admin_page_requires_login(live_server, page):
    page.goto(url_for('admin.dashboard', _external=True))
    expect(page.locator('#email')).to_be_visible()
    expect(page.locator('#password')).to_be_visible()


def test_dashboard_displayed_when_logged_in(live_server, page):
    page.goto(url_for('admin.dashboard', _external=True))
    # should send us to login instead
    expect(page).to_have_url(url_for('security.login', _external=True) + '?next=/admin/dashboard')
    # login
    page.get_by_label('Email Address').fill('test@example.co.uk')
    page.get_by_label('Password').fill('password')
    page.get_by_role('button', name='Login').click()
    # should redirect to dashboard
    expect(page).to_have_url(url_for('admin.dashboard', _external=True))





