# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Data views for weko-accounts."""

# the templates and static folders as well as the test case.

from flask import Blueprint, render_template, request, Flask, current_app
from flask_babelex import gettext as _


blueprint = Blueprint(
    'weko_accounts',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix="/weko",
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_accounts/index.html",
        module_name=_('WEKO-Accounts'))
