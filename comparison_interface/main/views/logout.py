from .request import Request


class Logout(Request):
    """Logout the user from the platform.

    Clears the session and redirects the user to the user registration page.
    """

    def get(self, _):
        """Request get handler."""
        self._session.clear()
        return self._redirect('.user_registration')
