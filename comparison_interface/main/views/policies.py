import os

from comparison_interface.configuration.website import Settings as WS
from .request import Request


class Policies(Request):
    """Render the policies page.

    This page either contains an iframe with a link to a google doc or the html from the location specified.
    """

    def get(self, _):
        """Request get handler."""
        site_policies_html = WS.get_behaviour_conf(WS.BEHAVIOUR_SITE_POLICIES_HTML, self._app)
        with open(os.path.join(self._app.root_path, site_policies_html)) as input_file:
            html = input_file.read()

        if html.startswith('<html'):
            fragment = False
        else:
            fragment = True
        return self._render_template(
            'main/pages/policies.html',
            {
                'fragment': fragment,
                'html_string': html,
                'site_policies_back_button': WS.get_text(WS.SITE_POLICIES_BACK_BUTTON_LABEL, self._app),
            },
        )
