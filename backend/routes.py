#Also Called Controllers

from flask import current_app as app
from flask import render_template, request, redirect

@app.route('/Home', methods=['GET', 'POST'])
def index():
    return"welcome to the home page"