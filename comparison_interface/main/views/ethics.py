import os

from comparison_interface.configuration.website import Settings as WS
from .request import Request


class Ethics(Request):
    """Render the ethics agreement page.

    This page either contains an iframe with a link to a google doc or the html from the location specified.
    """

    def get(self, _):
        """Request get handler."""
        ethics_agreement_html = WS.get_behaviour_conf(WS.BEHAVIOUR_ETHICS_AGREEMENT_HTML, self._app)
        with open(os.path.join(self._app.root_path, ethics_agreement_html)) as input_file:
            html = input_file.read()

        if html.startswith('<html'):
            fragment = False
        else:
            fragment = True
        return self._render_template(
            'main/pages/ethics.html',
            {
                'fragment': fragment,
                'html_string': html,
                'ethics_agreement_back_button': WS.get_text(WS.ETHICS_AGREEMENT_BACK_BUTTON_LABEL, self._app),
            },
        )
