import os

from ..configuration.website import Settings as WS
from .request import Request


class Ethics(Request):
    """Render the ethics agreement page.

    This page either contains an iframe with a link to a google doc or the html from the location specified.
    """

    def get(self, _):
        """Request get handler."""
        if WS.configuration_has_key(WS.BEHAVIOUR_ETHICS_AGREEMENT_LINK, self._app):
            return self._render_template(
                'pages/ethics.html',
                {
                    'google_doc': True,
                    'ethics_agreement_link': WS.get_behaviour_conf(WS.BEHAVIOUR_ETHICS_AGREEMENT_LINK, self._app),
                    'ethics_agreement_back_button': WS.get_text(WS.ETHICS_AGREEMENT_BACK_BUTTON_LABEL, self._app),
                },
            )
        # otherwise we are have html to inject instead
        ethics_agreement_html = WS.get_behaviour_conf(WS.BEHAVIOUR_ETHICS_AGREEMENT_HTML, self._app)
        with open(os.path.join(self._app.root_path, ethics_agreement_html)) as input_file:
            html_fragment = input_file.read()

        return self._render_template(
            'pages/ethics.html',
            {
                'google_doc': False,
                'html_string': html_fragment,
                'ethics_agreement_back_button': WS.get_text(WS.ETHICS_AGREEMENT_BACK_BUTTON_LABEL, self._app),
            },
        )
