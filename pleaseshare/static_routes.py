"""
Static routes that do not need the application object to work
"""

import flask

static_pages = flask.Blueprint('static', __name__,
                               template_folder='templates')

@static_pages.route("/about")
def about():
    """About page"""
    return flask.render_template("about.html")

@static_pages.route("/contact")
def contact():
    """Contact page"""
    return flask.render_template("contact.html")

@static_pages.route("/tos")
def tos():
    """Terms of service"""
    return flask.render_template("tos.html")

@static_pages.route("/help")
def help():
    """Help"""
    return flask.render_template("help.html")




