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

"""Blueprint for weko-index-tree."""

from datetime import date, timedelta
from operator import itemgetter

from flask import Blueprint, current_app, jsonify, request, session
from flask_login import current_user

from .api import Indexes
from .config import WEKO_INDEX_TREE_RSS_COUNT_LIMIT, \
    WEKO_INDEX_TREE_RSS_DEFAULT_COUNT, WEKO_INDEX_TREE_RSS_DEFAULT_INDEX_ID, \
    WEKO_INDEX_TREE_RSS_DEFAULT_LANG, WEKO_INDEX_TREE_RSS_DEFAULT_PAGE, \
    WEKO_INDEX_TREE_RSS_DEFAULT_TERM, WEKO_INDEX_TREE_STATE_PREFIX
from .utils import generate_path, get_elasticsearch_records_data_by_indexes

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    url_prefix='/indextree',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_index_tree',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint_api.route('/rss.xml', methods=['GET'])
def get_rss_data():
    """Get rss data based on term.

    Returns:
        xml -- RSS data

    """
    from weko_gridlayout.utils import build_rss_xml
    from weko_items_ui.utils import find_hidden_items

    data = request.args

    index_id = int(data.get('index_id'))
    if index_id < WEKO_INDEX_TREE_RSS_DEFAULT_INDEX_ID:
        index_id = WEKO_INDEX_TREE_RSS_DEFAULT_INDEX_ID
    page = int(data.get('page') or WEKO_INDEX_TREE_RSS_DEFAULT_PAGE)
    if page < WEKO_INDEX_TREE_RSS_DEFAULT_PAGE:
        page = WEKO_INDEX_TREE_RSS_DEFAULT_PAGE
    count = int(data.get('count') or WEKO_INDEX_TREE_RSS_DEFAULT_COUNT)
    if count < 0 or count > WEKO_INDEX_TREE_RSS_COUNT_LIMIT:
        count = WEKO_INDEX_TREE_RSS_DEFAULT_COUNT
    term = int(data.get('term') or WEKO_INDEX_TREE_RSS_DEFAULT_TERM)
    if term <= 0:
        term = WEKO_INDEX_TREE_RSS_DEFAULT_TERM
    lang = data.get('lang') or WEKO_INDEX_TREE_RSS_DEFAULT_LANG

    idx_tree_ids = [idx.cid for idx in Indexes.get_recursive_tree(index_id)]
    current_date = date.today()
    end_date = current_date.strftime("%Y-%m-%d")
    start_date = (current_date - timedelta(days=term)).strftime("%Y-%m-%d")
    records_data = get_elasticsearch_records_data_by_indexes(idx_tree_ids,
                                                             start_date,
                                                             end_date)

    hits = records_data.get('hits')
    es_data = hits.get('hits')
    item_id_list = list(map(itemgetter('_id'), es_data))
    idx_tree_full_ids = generate_path(Indexes.get_recursive_tree(index_id))
    hidden_items = find_hidden_items(item_id_list, idx_tree_full_ids)

    rss_data = []
    for es_item in es_data:
        if es_item['_id'] in hidden_items:
            continue
        rss_data.append(es_item)

    return build_rss_xml(data=rss_data,
                         index_id=index_id,
                         page=page,
                         count=count,
                         term=term,
                         lang=lang)


@blueprint_api.route('/indextree/set_expand', methods=['POST'])
def set_expand():
    """Set expand list index tree id."""
    data = request.get_json(force=True)
    index_id = data.get("index_id")
    key = current_app.config.get(
        "WEKO_INDEX_TREE_STATE_PREFIX",
        WEKO_INDEX_TREE_STATE_PREFIX
    )
    session_data = session.get(key, [])
    if session_data:
        if index_id in session_data:
            session_data.remove(index_id)
        else:
            session_data.append(index_id)
    else:
        session_data.append(index_id)
    session[key] = session_data

    return jsonify(success=True)
