from flask import redirect, render_template, url_for

from ..configuration.website import Settings as WS


class Request:
    """Base class for views."""

    def __init__(self, app, session) -> None:
        """Make the provided app and session available to requests.

        Args:
            app (_type_): _description_
            session (_type_): _description_
        """
        self._app = app
        self._session = session

    @staticmethod
    def process(handler, request):
        """Process the request."""
        if request.method == 'GET':
            return handler.get(request)
        if request.method == 'POST':
            return handler.post(request)

        raise "Method not implemented."

    def get(self, request):
        """To be implemented by inheriting classes."""
        raise "Method not implemented."

    def post(self, request):
        """To be implemented by inheriting classes."""
        raise "Method not implemented."

    def get_layout_text(self):
        """Get the application layout configuration text.

        Returns:
            dict: Layout configured text
        """
        render_instructions = WS.should_render(WS.BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE, self._app)
        render_ethics_agreement = WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self._app)
        render_site_policies = WS.should_render(WS.BEHAVIOUR_RENDER_SITE_POLICIES, self._app)
        render_site_cookies = WS.should_render(WS.BEHAVIOUR_RENDER_COOKIE_BANNER, self._app)

        return {
            'website_title': WS.get_text(WS.WEBSITE_TITLE, self._app),
            'introduction_page_title': WS.get_text(WS.PAGE_TITLE_INTRODUCTION, self._app),
            'ethics_agreement_page_title': WS.get_text(WS.PAGE_TITLE_ETHICS_AGREEMENT, self._app),
            'policies_page_title': WS.get_text(WS.PAGE_TITLE_POLICIES, self._app),
            'user_registration_page_title': WS.get_text(WS.PAGE_TITLE_USER_REGISTRATION, self._app),
            'logout_page_title': WS.get_text(WS.PAGE_TITLE_LOGOUT, self._app),
            'item_preference_page_title': WS.get_text(WS.PAGE_TITLE_ITEM_PREFERENCE, self._app),
            'rank_page_title': WS.get_text(WS.PAGE_TITLE_RANK, self._app),
            'site_cookies_accept_button_label': WS.get_text(WS.SITE_COOKIES_ACCEPT_BUTTON_LABEL, self._app),
            'site_cookies_title': WS.get_text(WS.SITE_COOKIES_TITLE, self._app),
            'site_cookies_text': WS.get_text(WS.SITE_COOKIES_TEXT, self._app),
            'render_user_instructions': render_instructions,
            'render_user_ethics_agreement': render_ethics_agreement,
            'render_site_policies': render_site_policies,
            'render_cookie_banner': render_site_cookies,
        }

    def _valid_session(self):
        """Verify that the the user session is valid."""
        if "user_id" not in self._session or "group_ids" not in self._session:
            return False
        return True

    def _render_template(self, template: str, args: dict = None):
        """Render a HTML template using flask and Jinja2.

        Args:
            template (str): view html template location
            args (dict, optional): args used to render the template
        """
        if args is None or len(args) == 0:
            return render_template(template, **self.get_layout_text())
        return render_template(template, **{**args, **self.get_layout_text()})

    def _redirect(self, url: str, **values):
        """Redirect the web page to a new location.

        Args:
            url (str): Url to redirect to

        Returns:
            Redirect the user to the provided URL
        """
        return redirect(url_for(url, **values))
