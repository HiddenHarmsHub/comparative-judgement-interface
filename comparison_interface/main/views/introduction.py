import os

from comparison_interface.configuration.website import Settings as WS

from .request import Request


class Introduction(Request):
    """Render the introduction page.

    This page either contains an iframe with a link to a google doc or the html from the location specified.
    """

    def get(self, _):
        """Request get handler."""
        if WS.configuration_has_key(WS.BEHAVIOUR_USER_INSTRUCTION_HTML, self._app):
            user_instruction_html = WS.get_behaviour_conf(WS.BEHAVIOUR_USER_INSTRUCTION_HTML, self._app)
            with open(os.path.join(self._app.root_path, user_instruction_html)) as input_file:
                html = input_file.read()
        else:
            folder = self._app.config['HTML_PAGES_DIR']
            with open(os.path.join(self._app.root_path, folder, 'instructions.html')) as input_file:
                html = input_file.read()

        if html.startswith('<html'):
            fragment = False
        else:
            fragment = True
        return self._render_template(
            'main/pages/introduction.html',
            {
                'fragment': fragment,
                'html_string': html,
                'introduction_continue_button': WS.get_text(WS.INTRODUCTION_CONTINUE_BUTTON_LABEL, self._app),
            },
        )
