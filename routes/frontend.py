from flask import Blueprint
from flask import render_template

from utils.doc_utils import BlueprintDocumentation

frontend_bp = Blueprint('frontend', __name__)
frontend_docs = BlueprintDocumentation(frontend_bp, 'Frontend')
dir = "www/"


@frontend_bp.route("/index")
@frontend_bp.route("/")
def index():
    return render_template(dir + "index.html")


@frontend_bp.route("/home")
def home():
    return render_template(dir + "home.html")


@frontend_bp.route("/creation")
def creation():
    return render_template(dir +"creation.html")


@frontend_bp.route("/explore")
def explore():
    return render_template(dir +"explore.html")


@frontend_bp.route("/analytics")
def analytics():
    return render_template(dir +"analytics.html")


@frontend_bp.route("/about")
def about():
    return render_template(dir +"about.html")