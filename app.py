from comparison_interface import create_app
from werkzeug.middleware.proxy_fix import ProxyFix

app = create_app()

# Tell Flask to use X-Script-Name header as SCRIPT_NAME
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
