from comparison_interface.db.connection import db
from comparison_interface.db.models import Participant, ParticipantStudy
from comparison_interface.main.views import register


def test_page_links_all_true(equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights and all of the options for header links set to true
    WHEN the registration page is displayed
    THEN the correct page links appear in the header (this is really testing the base request)
    """
    with equal_weight_client:
        response = equal_weight_client.get("/register")
        assert b'href="/introduction"' in response.data
        assert b'href="/ethics-agreement"' in response.data
        assert b'href="/policies"' in response.data
        assert b'href="/logout"' in response.data


def test_page_links_all_false(mocker, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights and all of the options for header links set to false
    WHEN the registration page is displayed
    THEN the correct page links appear in the header (this is really testing the base request)
    """
    should_render = mocker.patch.object(register.WS, 'should_render')
    # 1 for the ethics button on the form (same setting as header)
    # 3 for the request items for the header
    # 1 for the cookie banner
    should_render.side_effect = [False, False, False, False, True]
    with equal_weight_client:
        response = equal_weight_client.get("/register")
        assert b'href="/introduction"' not in response.data
        assert b'href="/ethics-agreement"' not in response.data
        assert b'href="/policies"' not in response.data
        assert b'href="/logout"' in response.data


def test_register_participant_with_escape_route_on(equal_weight_client, participant_data):
    """
    GIVEN a flask app configured for testing and equal weights and with the escape route on
    WHEN a new participant registers on the site
    THEN the participant is stored in the database for study 1 with the study cycle count set at 0 and is redirected
    to the item selection page
    """
    with equal_weight_client:
        response = equal_weight_client.post("/register", data=participant_data)

        # Check that there was a redirect to the next page.
        assert response.status_code == 302
        assert b'href="/selection/items"' in response.data

        # Verify the participant was inserted into the database with the cycle count set as 0 and added to the session
        with equal_weight_client.session_transaction() as session:
            participant = db.session.scalars(db.select(Participant).order_by(Participant.participant_id.desc())).first()
            assert participant.current_study_id == 1
            assert isinstance(participant.participant_id, int)
            assert participant.participant_id == session['participant_id']
            participant_studies = db.session.scalars(
                db.select(ParticipantStudy).where(ParticipantStudy.participant_id == participant.participant_id)
            ).all()
            assert len(participant_studies) == 1
            assert participant_studies[0].completed_cycles == 0


def test_register_participant_with_escape_route_off(mocker, equal_weight_client, participant_data):
    """
    GIVEN a flask app configured for testing and equal weights and with the escape route off
    WHEN a new participant registers on the site
    THEN the participant is stored in the database with cycle count set to None and is redirected to the item
    selection page
    """
    with equal_weight_client:
        escape_route_setting = mocker.patch.object(register.WS, 'get_study_conf')
        escape_route_setting.side_effect = [False, False]
        response = equal_weight_client.post("/register", data=participant_data)

        # Check that there was a redirect to the next page.
        assert response.status_code == 302
        assert b'href="/selection/items"' in response.data

        # Verify the participant was inserted into the database with the cycle count set as 0 and added to the session
        with equal_weight_client.session_transaction() as session:
            participant = db.session.scalars(db.select(Participant).order_by(Participant.participant_id.desc())).first()
            assert participant.current_study_id == 1
            assert isinstance(participant.participant_id, int)
            assert participant.participant_id == session['participant_id']
            participant_studies = db.session.scalars(
                db.select(ParticipantStudy).where(ParticipantStudy.participant_id == participant.participant_id)
            ).all()
            assert len(participant_studies) == 1
            assert participant_studies[0].completed_cycles == 0
