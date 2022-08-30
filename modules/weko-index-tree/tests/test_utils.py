import json
import pytest

from datetime import date, datetime
from functools import wraps
from operator import itemgetter

import redis
from redis import sentinel
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import Bool, Exists, Q, QueryString
from flask import Markup, current_app, session
from flask_babelex import get_locale
from flask_babelex import gettext as _
from flask_babelex import to_user_timezone, to_utc
from flask_login import current_user
from invenio_cache import current_cache
from invenio_i18n.ext import current_i18n
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import RecordsSearch
from simplekv.memory.redisstore import RedisStore
from invenio_accounts.testutils import login_user_via_session, login_user_via_view

from weko_index_tree.models import Index
from weko_workflow.models import Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from weko_admin.utils import is_exists_key_in_redis
from weko_groups.models import Group
from weko_redis.redis import RedisConnection
from weko_index_tree import utils


# from .config import WEKO_INDEX_TREE_STATE_PREFIX
# from .errors import IndexBaseRESTError, IndexDeletedRESTError
# from .models import Index


# def get_index_link_list(pid=0):
#     def _get_index_link(res, tree):
def test_get_index_link_list(records):
    def _get_index_link(res, index):
            if index.index_link_enabled:
                res.append((index.id, index.index_link_name))
            if index.have_children(index.id):
                _get_index_link(res, index.parent)

    indices_id_list = [idx['id'] for idx in Index.get_all()]

    for index_id in indices_id_list:
        num = Index.get_index_by_id(index_id)
        
        res = []
        _get_index_link(res, num)    
        
        assert res
        

# def is_index_tree_updated():
def test_is_index_tree_updated(app):
    current_app = app
    assert current_app.config['WEKO_INDEX_TREE_UPDATED']


# def cached_index_tree_json(timeout=50, key_prefix='index_tree_json'):
#     def caching(f):
#         def wrapper(*args, **kwargs):
# def reset_tree(tree, path=None, more_ids=None, ignore_more=False):
# def get_tree_json(index_list, root_id):
#     def get_user_list_expand():
#     def generate_index_dict(index_element, is_root):
#     def get_children(parent_index_id):


# def get_user_roles():
#     def _check_admin():
def test_get_user_roles(users):
    for user in users:
        def _check_admin(c_user):
            result = False
            for role in c_user.roles:
                if 'Administrator' in str(role):
                    result = True
            return result
    
        if _check_admin(user['obj']):
            assert user['isAdmin']
        else:
            assert not user['isAdmin']
    


# def get_user_groups():
def test_get_user_groups(users):
    for user in users:
        if user['obj'].groups:
            assert len(user['obj'].groups) != 0
        else:
            assert len(user['obj'].groups) == 0



# def check_roles(user_role, roles):
def test_check_roles(users):
    testKeyWordEmail = "noroleuser@test.org"
    for user in users:
        if user['obj'].roles:
            assert user['email'] != testKeyWordEmail
        else:
            assert user['email'] == testKeyWordEmail


# def check_groups(user_group, groups):
def test_check_groups(users):
    for user in users:
        if user['hasGroup']:
            assert len(user['obj'].groups) > 0
        else:
            assert len(user['obj'].groups) == 0


# def filter_index_list_by_role(index_list):
#     def _check(index_data, roles, groups):
def test_filter_index_list_by_role(indices, users):
    for user in users:
        result = []
        for index in indices:
            if index.browsing_role in user['obj'].roles or \
                    index.browsing_group in [x.group.name for x in user['obj'].groups]:
                if index.public_state and (
                        index.public_date is None
                        or (isinstance(index.public_date, datetime)
                                and date.today() >= index.public_date.date()
                        )):
                    result.append(index)
        if "contributor" in user['email'] or user["hasGroup"]:
            assert len(result) != 0
        else:
            assert len(result) == 0


# def reduce_index_by_role(tree, roles, groups, browsing_role=True, plst=None):


# def get_index_id_list(indexes, id_list=None):
def test_get_index_id_list(indices):
    index_id_list = []
    for index in indices:
        if index.id == 'more':
            continue

        if index.parent is not None:
            if index.parent != '' and index.parent != '0':
                index_id_list.append(f"{index.parent}/{index.id}")
        else:
            index_id_list.append(index.id)

    assert 'more' not in index_id_list
    assert len(index_id_list) == 5
 

# def get_publish_index_id_list(indexes, id_list=None):
def test_get_publish_index_id_list(indices):
    published_index_id_list = []
    not_published_index_id_list = []

    for index in indices:
        if index.public_state:
            if index.id == 'more':
                continue

            if index.parent is not None:
                if index.parent != '' and index.parent != '0':
                    published_index_id_list.append(f"{index.parent}/{index.id}")
            else:
                published_index_id_list.append(index.id)
        else:
            not_published_index_id_list.append(index.id)

    assert 'more' not in published_index_id_list
    assert 'more' not in not_published_index_id_list
    assert len(published_index_id_list) == 4
    assert len(not_published_index_id_list) == 1


# def reduce_index_by_more(tree, more_ids=None):


# def get_admin_coverpage_setting():
def test_get_admin_coverpage_setting(pdfcoverpage):
    from weko_records_ui.models import PDFCoverPageSettings

    isAvailable = 'disable'
        
    setting = PDFCoverPageSettings.find(1)
    
    if setting:
        isAvailable = setting.avail

    assert isAvailable == 'enable'


# def get_elasticsearch_records_data_by_indexes(index_ids, start_date, end_date):
def test_get_elasticsearch_records_data_by_indexes(records):
    from weko_search_ui.query import item_search_factory
    
    search_results = records['search_query_result']

    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']

    result = None

    search_instance, _qs_kwargs = item_search_factory(
        None,
        records_search,
        start_date,
        end_date,
        index_ids,
        True
    )
    search_result = search_instance.execute()
    result = search_result.to_dict()

    raise BaseException

# def generate_path(index_ids):


# def get_index_id(activity_id):
def test_get_index_id(users, db_register):
    from weko_workflow.api import WorkFlow
    from weko_index_tree.api import Indexes

    activity = db_register['activity']
    activity_id = activity.activity_id
    
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(activity_id)
    
    index_tree_id = workflow_detail.index_tree_id

    if index_tree_id:
        index_result = Indexes.get_index(index_tree_id)
        if not index_result:
            index_tree_id = None
    else:
        index_tree_id = None

    assert index_tree_id


# def sanitize(s):


# def count_items(indexes_aggr):
def test_count_items(users, db_register):

    def get_index_public_state(index_id):
        index = Index.get_index_by_id(index_id)
        return index.public_state
    
    private_count = 0
    public_count = 0

    all_indices = Index().get_all()

    for idx in all_indices:
        if get_index_public_state(idx['id']):
            public_count += 1
    
    # This 'index_private' is not saved in db.session and is directly from conftest.py
    if db_register['indices']['index_private']:
        private_count += 1

    assert private_count
    assert public_count


# def recorrect_private_items_count(agp):
# def check_doi_in_index(index_id):
# def get_record_in_es_of_index(index_id, recursively=True):
# def check_doi_in_list_record_es(index_id):
# def check_restrict_doi_with_indexes(index_ids):
# def check_has_any_item_in_index_is_locked(index_id):
# def check_index_permissions(record=None, index_id=None, index_path_list=None,
#     def _check_index_permission(index_data) -> bool:
#     def _check_index_permission_for_doi(index_data) -> bool:
#     def _check_for_index_groups(_index_groups):
#     def _convert_index_path(list_index):
#     def _get_record_index_list():
#     def _get_parent_lst():


# def check_doi_in_index_and_child_index(index_id, recursively=True):
def test_check_doi_in_index_and_child_index(redis_connect, db, records):
    indices_id_list = [idx['id'] for idx in Index.get_all()]
    child_idx_list = [x for x in records['indices'] if x.parent]

    parent_id = int(indices_id_list[0])
    
    child_index = Index(
        public_state=True,
        index_name='child_index',
        parent=parent_id
    )

    child_idx_list.append(child_index)

    qs1 = "relation_version_is_last"
    qs2 = "publish_status"
    records = records['search_query_result']['hits']['hits']

    source_check_records = []
    metadata_check_records = []

    for source_check in records:
        if source_check['_source'][qs1] == True and source_check['_source'][qs2] == '0':
            source_check_records.append(source_check)

    for metadata_check in records:
        if metadata_check['_source']['_item_metadata'][qs1] == True and metadata_check['_source']['_item_metadata'][qs2] == '0':
            metadata_check_records.append(metadata_check)

    assert source_check_records
    assert metadata_check_records


# def __get_redis_store():
def test___get_redis_store(redis_connect, db):
    if redis_connect.connection(db, kv=True):
        assert redis_connect
    else:
        assert not redis_connect


# def lock_all_child_index(index_id: str, value: str):
def test_lock_all_child_index(redis_connect, db, records):
    indices_id_list = [idx['id'] for idx in Index.get_all()]
    child_list = [x for x in records['indices'] if x.parent]

    parent_id = int(indices_id_list[0])
    
    child_index = Index(
        public_state=True,
        index_name='child_index',
        parent=parent_id
    )

    child_list.append(child_index)
    
    datastore = redis_connect.connection(db, kv=True)
    lock_key_prefix = "lock_index_"
    locked_index_key = f'{lock_key_prefix}{child_list[0].index_name}'
    
    datastore.put(locked_index_key, json.dumps({'1':'a'}).encode('utf-8'), ttl_secs=5)

    assert datastore.redis.exists(f'{lock_key_prefix}{child_index.index_name}')


# def unlock_index(index_key):
def test_unlock_index(redis_connect, db, records):
    
    def unlock_index(key):
        unlock_result = None
        locked_key = f"lock_index_{key}"
        datastore = redis_connect.connection(db, kv=True)

        if datastore.redis.exists(locked_key):
            datastore.delete(locked_key)
            unlock_result = True
        else:
            unlock_result = False
        
        return unlock_result

    unlock_check = False

    for index in records['indices']:
        if unlock_index(index.index_name):
            unlock_check = True
            assert unlock_check
        else:
            assert not unlock_check


# def validate_before_delete_index(index_id):


# def is_index_locked(index_id):
def test_is_index_locked(redis_connect, db, records):

    def is_exists_key_in_redis_and_is_locked(key):
        locked_key = f"lock_index_{key}"
        datastore = redis_connect.connection(db, kv=True)
        return datastore.redis.exists(locked_key)

    result = False

    for index in records['indices']:
        if is_exists_key_in_redis_and_is_locked(index.index_name):
            result = True
            assert result
        else:
            assert not result


# def perform_delete_index(index_id, record_class, action: str):
#         record_class (Indexes): Record object.
#             res = record_class.get_self_path(index_id)
#                 result = record_class. \
# def get_doi_items_in_index(index_id, recursively=False):
    """Check if any item in the index is locked by import process.

    @param index_id:
    @return:
    """

# def get_editing_items_in_index(index_id, recursively=False):