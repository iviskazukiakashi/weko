# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Flask extension for weko-items-ui."""

from . import config
from .permissions import item_permission
from .views import blueprint, check_ranking_show


class _WekoItemsUIState(object):
    """WekoItemsUI state."""

    def __init__(self, app, permission):
        """Initialize state.

        :param app: The Flask application.
        :param permission: The permission to restrict access.
        """
        self.app = app
        self.permission = permission


class WekoItemsUI(object):
    """weko-items-ui extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        :param app: The Flask application.
        """
        self.init_config(app)
        app.register_blueprint(blueprint)
        state = _WekoItemsUIState(app, item_permission)
        app.extensions['weko-items-ui'] = state
        app.jinja_env.globals.update(check_ranking_show=check_ranking_show)

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_PAGE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_ITEMS_UI_BASE_TEMPLATE',
                app.config['BASE_PAGE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_ITEMS_UI_'):
                app.config.setdefault(k, getattr(config, k))
