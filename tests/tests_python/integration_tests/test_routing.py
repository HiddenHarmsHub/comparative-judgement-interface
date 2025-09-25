def test_render_404(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights
    WHEN a route which does not exist is requested
    THEN a 404 page is shown
    """
    response = equal_weight_client.get("/not-exist")
    assert response.status_code == 404


def test_render_home_no_login(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights and no logged in participant
    WHEN the route location is requested
    THEN the registration page is shown
    """
    response = equal_weight_client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: User Registration' in response.data


def test_render_participant_register(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights and no logged in participant
    WHEN the route location is requested
    THEN the registration page is shown
    """
    response = equal_weight_client.get("/register")
    assert response.status_code == 200
    assert b'Comparison Software: User Registration' in response.data


def test_render_introduction(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights
    WHEN the introduction page is requested
    THEN the appropriate page is displayed
    """
    response = equal_weight_client.get("/introduction")
    assert response.status_code == 200
    assert b'<h1>User Instructions</h1>' in response.data


def test_render_ethics_agreement(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights
    WHEN the ethics agreement page is requested
    THEN the appropriate page is displayed
    """
    response = equal_weight_client.get("/ethics-agreement")
    assert response.status_code == 200
    assert b'<h1>Ethics Agreement</h1>' in response.data


def test_render_policies(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights
    WHEN the policies page is requested
    THEN the appropriate page is displayed
    """
    response = equal_weight_client.get("/policies")
    assert response.status_code == 200
    assert b'<h1>Site Policies</h1>' in response.data


def test_render_logout(equal_weight_client):
    """
    GIVEN a flask app configured for testing with equal weights and a logged in participant
    WHEN the participant logs out
    THEN they are redirected to the registration page and the session is cleared
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    response = equal_weight_client.get("/logout", follow_redirects=True)
    # Logout should redirect to the register page
    assert response.status_code == 200
    assert response.request.path == "/register"
    # there should be no session data
    with equal_weight_client.session_transaction() as session:
        assert 'participant_id' not in session
