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

"""API for weko-index-tree."""

import os
from copy import deepcopy
from datetime import date, datetime
from functools import partial

from redis.exceptions import RedisError
from flask import current_app, json
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_accounts.models import Role
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import case, func, literal_column
from weko_groups.api import Group
from weko_redis.redis import RedisConnection

from .models import Index
from .utils import cached_index_tree_json, check_doi_in_index, \
    check_restrict_doi_with_indexes, filter_index_list_by_role, \
    get_index_id_list, get_publish_index_id_list, get_tree_json, \
    get_user_roles, is_index_locked, reset_tree, sanitize, save_index_trees_to_redis


class Indexes(object):
    """Define API for index tree creation and update."""

    @classmethod
    def create(cls, pid=None, indexes=None):
        """Create the indexes. Delete all indexes before creation.

        :param pid: parent index id.
        :param indexes: the index information.
        :returns: The :class:`Index` instance lists or None.
        """
        def _add_index(data):
            with db.session.begin_nested():
                index = Index(**data)
                db.session.add(index)
            db.session.commit()

        if not isinstance(indexes, dict):
            return

        data = dict()
        is_ok = True
        try:
            cid = indexes.get('id')

            if not cid:
                return

            data["id"] = cid
            data["parent"] = pid
            data["index_name"] = indexes.get('value')
            data["index_name_english"] = indexes.get('value')
            data["index_link_name_english"] = data["index_name_english"]
            data["owner_user_id"] = current_user.get_id()
            role = cls.get_account_role()
            data["browsing_role"] = \
                ",".join(list(map(lambda x: str(x['id']), role)))
            data["contribute_role"] = data["browsing_role"]

            data["more_check"] = False
            data["display_no"] = current_app.config[
                'WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER']

            data["coverpage_state"] = False
            data["recursive_coverpage_check"] = False

            group_list = ''
            groups = Group.query.all()
            for group in groups:
                if not group_list:
                    group_list = str(group.id)
                else:
                    group_list = group_list + ',' + str(group.id)

            data["browsing_group"] = group_list
            data["contribute_group"] = group_list

            if int(pid) == 0:
                pid_info = cls.get_root_index_count()
                data["position"] = 0 if not pid_info else \
                    (0 if pid_info.position_max is None
                     else pid_info.position_max + 1)
            else:
                pid_info = cls.get_index(pid, with_count=True)

                if pid_info:
                    data["position"] = 0 if pid_info.position_max is None \
                        else pid_info.position_max + 1
                    iobj = pid_info.Index
                    data["harvest_public_state"] = iobj.harvest_public_state

                    data["display_format"] = iobj.display_format

                    if iobj.recursive_public_state:
                        data["public_state"] = iobj.public_state
                        data["public_date"] = iobj.public_date
                        data["recursive_public_state"] = \
                            iobj.recursive_public_state
                    if iobj.recursive_browsing_role:
                        data["browsing_role"] = iobj.browsing_role
                        data["recursive_browsing_role"] = \
                            iobj.recursive_browsing_role
                    if iobj.recursive_contribute_role:
                        data["contribute_role"] = iobj.contribute_role
                        data["recursive_contribute_role"] = \
                            iobj.recursive_contribute_role
                    if iobj.recursive_browsing_group:
                        data["browsing_group"] = iobj.browsing_group
                        data["recursive_browsing_group"] = \
                            iobj.recursive_browsing_group
                    if iobj.recursive_contribute_group:
                        data["contribute_group"] = iobj.contribute_group
                        data["recursive_contribute_group"] = \
                            iobj.recursive_contribute_group

                else:
                    return

            _add_index(data)
        except IntegrityError as ie:
            if 'uix_position' in ''.join(ie.args):
                try:
                    pid_info = cls.get_index(pid, with_count=True)
                    data["position"] = 0 if not pid_info else \
                        (pid_info.position_max + 1
                         if pid_info.position_max is not None else 0)
                    _add_index(data)
                except SQLAlchemyError as ex:
                    is_ok = False
                    current_app.logger.debug(ex)
            else:
                is_ok = False
                current_app.logger.debug(ie)
        except Exception as ex:
            is_ok = False
            current_app.logger.debug(ex)
        finally:
            del data
            if not is_ok:
                db.session.rollback()
        return is_ok

    @classmethod
    def update(cls, index_id, **data):
        """
        Update the index detail info.

        :param index_id: Identifier of the index.
        :param detail: new index info for update.
        :return: Updated index info
        """
        try:
            with db.session.begin_nested():
                index = cls.get_index(index_id)
                if not index:
                    return

                for k, v in data.items():
                    if isinstance(getattr(index, k), int):
                        if isinstance(v, str) and len(v) == 0:
                            continue
                    if isinstance(v, dict):
                        v = ",".join(map(lambda x: str(x["id"]), v["allow"]))
                    if "public_date" in k:
                        if len(v) > 0:
                            v = datetime.strptime(v, '%Y%m%d')
                        else:
                            v = None
                    if v is not None and (
                            "index_name" in k or "index_name_english" in k):
                        v = sanitize(v)
                    if "have_children" in k:
                        continue
                    setattr(index, k, v)
                recs_group = {
                    'recursive_coverpage_check': partial(
                        cls.set_coverpage_state_resc, index_id,
                        getattr(index, "coverpage_state")),
                    'recursive_public_state': partial(
                        cls.set_public_state_resc, index_id,
                        getattr(index, "public_state"),
                        getattr(index, "public_date")),
                    'recursive_browsing_group': partial(
                        cls.set_browsing_group_resc, index_id,
                        getattr(index, "browsing_group")),
                    'recursive_browsing_role': partial(
                        cls.set_browsing_role_resc, index_id,
                        getattr(index, "browsing_role")),
                    'recursive_contribute_group': partial(
                        cls.set_contribute_group_resc, index_id,
                        getattr(index, "contribute_group")),
                    'recursive_contribute_role': partial(
                        cls.set_contribute_role_resc, index_id,
                        getattr(index, "contribute_role")),
                    'biblio_flag': partial(
                        cls.set_online_issn_resc, index_id,
                        getattr(index, "online_issn"))                        
                }
                for recur_key, recur_update_func in recs_group.items():
                    if getattr(index, recur_key):
                        recur_update_func()
                    setattr(index, recur_key, False)
                index.owner_user_id = current_user.get_id()
                db.session.merge(index)
            db.session.commit()
            cls.update_set_info(index)
            return index
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def delete(cls, index_id, del_self=False):
        """
        Delete the index by index id.

        :param index_id: Identifier of the index.
        :return: bool True: Delete success None: Delete failed
        """
        try:
            if del_self:
                with db.session.begin_nested():
                    slf = cls.get_index(index_id)
                    if not slf:
                        return

                    query = db.session.query(Index).filter(
                        Index.parent == index_id)
                    obj_list = query.all()
                    dct = query.update(
                        {
                            Index.parent: slf.parent,
                            Index.owner_user_id: current_user.get_id(),
                            Index.updated: datetime.utcnow()
                        },
                        synchronize_session='fetch')
                    db.session.delete(slf)
                    db.session.commit()
                    p_lst = [o.id for o in obj_list]
                    cls.delete_set_info('move', index_id, p_lst)
                    return p_lst
            else:
                with db.session.no_autoflush:
                    recursive_t = cls.recs_query(pid=index_id)
                    obj = db.session.query(recursive_t). \
                        union_all(db.session.query(
                            Index.parent,
                            Index.id,
                            literal_column("''", db.Text).label("path"),
                            literal_column("''", db.Text).label("name"),
                            literal_column("''", db.Text).label(
                                "name_en"),
                            literal_column("0", db.Integer).label("lev"),
                            Index.public_state,
                            Index.public_date,
                            Index.comment,
                            Index.browsing_role,
                            Index.browsing_group,
                            Index.harvest_public_state
                        ).filter(Index.id == index_id)).all()

                if obj:
                    p_lst = [o.cid for o in obj]
                    with db.session.begin_nested():
                        e = 0
                        batch = 100
                        while e <= len(p_lst):
                            s = e
                            e = e + batch
                            dct = db.session.query(Index).filter(
                                Index.id.in_(p_lst[s:e])). \
                                delete(synchronize_session='fetch')
                    db.session.commit()
                    cls.delete_set_info('delete', index_id, p_lst)
                    return p_lst
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None
        return 0

    @classmethod
    def delete_by_action(cls, action, index_id):
        """
        Delete_by_action.

        :param action: action of the index.
        :param index_id: Identifier of the index.
        :param path: path of the index.
        :return: bool True: Delete success None: Delete failed
        """
        from weko_deposit.api import WekoDeposit
        if "move" == action:
            result = cls.delete(index_id, True)
        else:
            result = cls.delete(index_id)
            if result:
                # delete indexes all
                for i in result:
                    WekoDeposit.delete_by_index_tree_id(i)
        return result

    @classmethod
    def move(cls, index_id, **data):
        """Move."""
        def _update_index(new_position, parent=None):
            with db.session.begin_nested():
                index = Index.query.filter_by(id=index_id).one()
                index.position = new_position
                index.owner_user_id = user_id
                flag_modified(index, 'position')
                flag_modified(index, 'owner_user_id')
                if parent:
                    index.parent = parent
                    flag_modified(index, 'parent')
                db.session.merge(index)

        def _swap_position(i, index_tree, next_index_tree):
            # move the index in position i to temp
            next_index_tree.position = -1
            db.session.merge(next_index_tree)
            # move current index to position i
            temp_position = index_tree.position
            index_tree.position = i
            db.session.merge(index_tree)
            # move the index in position i to new temp
            next_index_tree.position = temp_position
            db.session.merge(next_index_tree)

        def _re_order_tree(new_position):
            with db.session.begin_nested():
                nlst = Index.query.filter_by(parent=parent). \
                    order_by(
                    Index.position).with_for_update().all()

                moved_items = list(
                    filter(lambda item: item.id == index_id, nlst))
                if moved_items:
                    current_index = nlst.index(moved_items[0])
                    if new_position != current_index \
                            or new_position != moved_items[0].position:
                        del nlst[current_index]
                        nlst.insert(new_position, moved_items[0])

                        for i, index_tree in enumerate(nlst):
                            if index_tree.position != i:
                                if i + 1 < len(nlst):
                                    is_swap = False
                                    for next_index_tree in nlst[i + 1:]:
                                        if next_index_tree.position == i:
                                            _swap_position(
                                                i, index_tree, next_index_tree)
                                            is_swap = True
                                            break
                                    if not is_swap:
                                        index_tree.position = i
                                        db.session.merge(index_tree)
                                else:
                                    index_tree.position = i
                                    db.session.merge(index_tree)

        ret = {
            'is_ok': True,
            'msg': ''}
        user_id = current_user.get_id()

        if isinstance(data, dict):
            pre_parent = data.get('pre_parent')
            parent = data.get('parent')
            if not pre_parent or not parent:
                ret['is_ok'] = False
                ret['msg'] = _('Select an index to move.')
                return ret

            if index_id == int(parent):
                ret['is_ok'] = False
                ret['msg'] = _('Fail move an index.')
                return ret

            try:
                new_position = int(data.get('position'))
                if int(parent) == 0:
                    parent_info = cls.get_root_index_count()
                else:
                    parent_info = cls.get_index(parent,
                                                with_count=True)
                position_max = parent_info.position_max + 1 \
                    if parent_info.position_max is not None else 0

                # Validator
                if is_index_locked(parent) or is_index_locked(pre_parent):
                    ret['is_ok'] = False
                    ret['msg'] = _('Index Delete is in progress '
                                   'on another device.')
                    return ret
                if check_doi_in_index(index_id) and parent_info[0] != 0 and \
                        check_restrict_doi_with_indexes([parent]):
                    ret['is_ok'] = False
                    ret['msg'] = _('The index cannot be kept private because '
                                   'there are links from items that have a '
                                   'DOI.')
                    return ret

                # move index on the same hierarchy
                if str(pre_parent) == str(parent):
                    if new_position >= position_max:
                        new_position = position_max + 1
                        try:
                            _update_index(new_position)
                            db.session.commit()
                        except IntegrityError as ie:
                            if 'uix_position' in ''.join(ie.args):
                                try:
                                    new_position += 1
                                    _update_index(new_position)
                                    db.session.commit()
                                except SQLAlchemyError as ex:
                                    ret['is_ok'] = False
                                    ret['msg'] = str(ex)
                                    current_app.logger.debug(ex)
                            else:
                                ret['is_ok'] = False
                                ret['msg'] = str(ie)
                                current_app.logger.debug(ie)
                        except Exception as ex:
                            ret['is_ok'] = False
                            ret['msg'] = str(ex)
                            current_app.logger.debug(ex)
                        finally:
                            if not ret['is_ok']:
                                db.session.rollback()
                    else:
                        try:
                            _re_order_tree(new_position)
                            db.session.commit()
                        except Exception as ex:
                            ret['is_ok'] = False
                            ret['msg'] = str(ex)
                            current_app.logger.debug(ex)
                        finally:
                            if not ret['is_ok']:
                                db.session.rollback()
                else:
                    index = Index.query.filter_by(id=index_id).one()
                    try:
                        _update_index(position_max, parent)
                        _re_order_tree(new_position)
                        db.session.commit()
                        cls.update_set_info(index)
                    except IntegrityError as ie:
                        if 'uix_position' in ''.join(ie.args):
                            try:
                                if int(parent) == 0:
                                    parent_info = cls.get_root_index_count()
                                else:
                                    parent_info = \
                                        cls.get_index(parent, with_count=True)
                                position_max = parent_info.position_max + 1 \
                                    if parent_info.position_max is not None \
                                    else 0
                                _update_index(position_max)
                                cls.update_set_info(index)
                            except SQLAlchemyError as ex:
                                ret['is_ok'] = False
                                ret['msg'] = str(ex)
                                current_app.logger.debug(ex)
                        else:
                            ret['is_ok'] = False
                            ret['msg'] = str(ie)
                            current_app.logger.debug(ie)
                    except Exception as ex:
                        ret['is_ok'] = False
                        ret['msg'] = str(ex)
                        current_app.logger.debug(ex)
                    finally:
                        if not ret['is_ok']:
                            db.session.rollback()
            except Exception as ex:
                ret['is_ok'] = False
                ret['msg'] = str(ex)
                current_app.logger.debug(ex)
        return ret

    @classmethod
    @cached_index_tree_json(timeout=None,)
    def get_index_tree(cls, pid=0):
        """Get index tree json."""
        return get_tree_json(cls.get_recursive_tree(pid), pid)

    @classmethod
    def get_browsing_info(cls):
        """Get browsing information of all indexes."""
        browsing_info = {}
        indexes = cls.get_public_indexes()
        for index in indexes:
            browsing_info[str(index.id)] = {
                'index_name': index.index_name,
                'parent': str(index.parent),
                'public_date': index.public_date,
                'harvest_public_state': index.harvest_public_state,
                'browsing_role': index.browsing_role.split(',')
            }
        return browsing_info

    @classmethod
    def get_browsing_tree(cls, pid=0):
        """Get browsing tree."""
        if pid == 0:
            try:
                redis_connection = RedisConnection()
                datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
                v = datastore.get("index_tree_view_" + os.environ.get('INVENIO_WEB_HOST_NAME')).decode("UTF-8")
                tree = json.loads(str(v, encoding='utf-8'))
            except RedisError:
                tree = cls.get_index_tree(pid)
                save_index_trees_to_redis(tree)
        else:
            tree = cls.get_index_tree(pid)
        reset_tree(tree=tree)
        return tree

    @classmethod
    def get_more_browsing_tree(cls, pid=0, more_ids=[]):
        """Get more browsing tree."""
        tree = cls.get_index_tree(pid)
        reset_tree(tree=tree, more_ids=more_ids)
        return tree

    @classmethod
    def get_browsing_tree_ignore_more(cls, pid=0):
        """Get browsing tree ignore more."""
        if pid == 0:
            try:
                redis_connection = RedisConnection()
                datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
                v = datastore.get("index_tree_view_" + os.environ.get('INVENIO_WEB_HOST_NAME')).decode("UTF-8")
                tree = json.loads(str(v, encoding='utf-8'))
            except RedisError:
                tree = cls.get_index_tree(pid)
                save_index_trees_to_redis(tree)
        else:
            tree = cls.get_index_tree(pid)
        reset_tree(tree=tree, ignore_more=True)
        return tree

    @classmethod
    def get_browsing_tree_paths(cls, index_id: int = 0):
        """Get browsing tree paths.

        Args:
            pid (int, optional): Index identifier. Defaults to 0.

        Returns:
            [type]: [description]

        """
        if not index_id:
            index_id = 0
        tree = cls.get_browsing_tree_ignore_more(index_id)
        return get_index_id_list(tree, [])

    @classmethod
    def get_contribute_tree(cls, pid, root_node_id=0):
        """Get Contrbute tree."""
        from weko_deposit.api import WekoRecord
        record = WekoRecord.get_record_by_pid(pid)
        tree = cls.get_index_tree(root_node_id)
        if record.get('_oai'):
            reset_tree(tree=tree, path=record.get('path'))
        else:
            reset_tree(tree=tree, path=[])

        return tree

    @classmethod
    def get_recursive_tree(cls, pid: int = 0):
        """Get recursive tree."""
        with db.session.begin_nested():
            recursive_t = cls.recs_tree_query(pid)
            if pid != 0:
                recursive_t = cls.recs_root_tree_query(pid)
            qlst = [
                recursive_t.c.pid,
                recursive_t.c.cid,
                recursive_t.c.position,
                recursive_t.c.name,
                recursive_t.c.link_name,
                recursive_t.c.index_link_enabled,
                recursive_t.c.public_state,
                recursive_t.c.public_date,
                recursive_t.c.browsing_role,
                recursive_t.c.contribute_role,
                recursive_t.c.browsing_group,
                recursive_t.c.contribute_group,
                recursive_t.c.more_check,
                recursive_t.c.display_no,
                recursive_t.c.coverpage_state,
                recursive_t.c.recursive_coverpage_check]
            obj = db.session.query(*qlst). \
                order_by(recursive_t.c.lev,
                         recursive_t.c.pid,
                         recursive_t.c.cid).all()
        return obj

    @classmethod
    def get_index_with_role(cls, index_id):
        """Get Index with role."""
        def _get_allow_deny(allow, role, browse_flag=False):
            alw = []
            deny = []
            if isinstance(role, list):
                while role:
                    tmp = role.pop(0)
                    if 'Administrator' not in tmp["name"] or not browse_flag:
                        if str(tmp["id"]) in allow:
                            alw.append(tmp)
                        else:
                            deny.append(tmp)
            return alw, deny

        def _get_group_allow_deny(allow_group_id=[], groups=[]):
            allow = []
            deny = []
            if not groups:
                return allow, deny
            for group in groups:
                if str(group.id) in allow_group_id:
                    allow.append({'id': str(group.id), 'name': group.name})
                else:
                    deny.append({'id': str(group.id), 'name': group.name})

            return allow, deny

        index = dict(cls.get_index(index_id))

        role = cls.get_account_role()
        allow = index["browsing_role"].split(',') \
            if len(index["browsing_role"]) else []
        allow, deny = _get_allow_deny(allow, deepcopy(role), True)
        index["browsing_role"] = dict(allow=allow, deny=deny)

        allow = index["contribute_role"].split(',') \
            if len(index["contribute_role"]) else []
        allow, deny = _get_allow_deny(allow, role)
        index["contribute_role"] = dict(allow=allow, deny=deny)

        if index["public_date"]:
            index["public_date"] = index["public_date"].strftime('%Y%m%d')

        group_list = Group.query.all()

        allow_group_id = index["browsing_group"].split(',') \
            if len(index["browsing_group"]) else []
        allow_group, deny_group = _get_group_allow_deny(allow_group_id,
                                                        deepcopy(group_list))
        index["browsing_group"] = dict(allow=allow_group, deny=deny_group)

        allow_group_id = index["contribute_group"].split(',') \
            if len(index["contribute_group"]) else []
        allow_group, deny_group = _get_group_allow_deny(allow_group_id,
                                                        deepcopy(group_list))
        index["contribute_group"] = dict(allow=allow_group, deny=deny_group)

        return index

    @classmethod
    def get_index(cls, index_id, with_count=False):
        """Get index."""
        with db.session.begin_nested():
            if with_count:
                stmt = db.session.query(Index.parent, func.max(Index.position).
                                        label('position_max')) \
                    .filter(Index.parent == index_id) \
                    .group_by(Index.parent).subquery()
                obj = db.session.query(Index, stmt.c.position_max). \
                    outerjoin(stmt, Index.id == stmt.c.parent). \
                    filter(Index.id == index_id).one_or_none()
            else:
                obj = db.session.query(Index). \
                    filter_by(id=index_id).one_or_none()

        return obj

    @classmethod
    def get_index_by_name(cls, index_name="", pid=0):
        """Validation importing zip file.

        :argument
            index_name   -- {str} index_name query
            pid          -- {number} parent index id
        :return
            return       -- index id import item

        """
        with db.session.begin_nested():
            obj = db.session.query(Index). \
                filter_by(index_name=index_name, parent=pid).one_or_none()
        return obj

    @classmethod
    def get_index_by_all_name(cls, index_name=""):
        """Get index by index name (jp, eng).

        :argument
            index_name   -- {str} Index name.
        :return
            return       -- index object

        """
        with db.session.begin_nested():
            obj = db.session.query(Index). \
                filter(db.or_(Index.index_name_english == index_name,
                              Index.index_name == index_name)).first()
        return obj

    @classmethod
    def get_root_index_count(cls):
        """Get root index."""
        with db.session.begin_nested():
            obj = db.session.query(Index.parent,
                                   func.max(Index.position).
                                   label('position_max')). \
                filter_by(parent=0).group_by(Index.parent).one_or_none()
        return obj

    @classmethod
    def get_account_role(cls):
        """Get account role."""
        def _get_dict(x):
            dt = dict()
            for k, v in x.__dict__.items():
                if not k.startswith('__') and not k.startswith('_') \
                        and "description" not in k:
                    if not v:
                        v = ""
                    if isinstance(v, int) or isinstance(v, str):
                        dt[k] = v
            return dt

        try:
            with db.session.no_autoflush:
                role = Role.query.all()
            return list(map(_get_dict, role)) \
                + [{"id": -98, "name": "Authenticated User"}] \
                + [{"id": -99, "name": "Guest"}]
        except SQLAlchemyError:
            return

    @classmethod
    def get_path_list(cls, node_lst):
        """
        Get index tree info.

        :param node_lst: Identifier list of the index.
        :return: the list of index.
        """
        recursive_t = cls.recs_query()
        q = db.session.query(recursive_t).filter(
            recursive_t.c.cid.in_(node_lst)).all()
        return q

    @classmethod
    def get_path_name(cls, index_ids):
        """
        Get index title info.

        :param node_path: List of the Index Identifiers.
        :return: the list of index.
        """
        node_paths = [cls.get_full_path(item) for item in index_ids]
        recursive_t = cls.recs_query()
        q = db.session.query(recursive_t).filter(
            recursive_t.c.path.in_(node_paths)). \
            order_by(recursive_t.c.path).all()
        return filter_index_list_by_role(q)

    @classmethod
    def get_self_list(cls, index_id, community_id=None):
        """
        Get index list info.

        :param node_path: Identifier of the index.
        :return: the list of index.
        """
        if community_id:
            from invenio_communities.models import Community
            community_obj = Community.get(community_id)
            recursive_t = cls.recs_query()
            query = db.session.query(recursive_t).filter(db.or_(
                recursive_t.c.cid == index_id, recursive_t.c.pid == index_id))
            if not get_user_roles()[0]:
                query = query.filter(recursive_t.c.public_state)
            q = query.order_by(recursive_t.c.path).all()
            lst = list()
            if index_id != '0':
                for item in q:
                    if item.cid == community_obj.root_node_id \
                            and item.pid == '0':
                        lst.append(item)
                    if item.pid != '0':
                        lst.append(item)
                return lst
        else:
            recursive_t = cls.recs_query()
            query = db.session.query(recursive_t).filter(
                db.or_(recursive_t.c.pid == index_id,
                       recursive_t.c.cid == index_id))
            if not get_user_roles()[0]:
                query = query.filter(recursive_t.c.public_state)
            q = query.order_by(recursive_t.c.path).all()
            return q

    @classmethod
    def get_self_path(cls, node_id):
        """Get index view path info.

        :param node_id: Identifier of the index.
        :return: the type of Index.
        """
        try:
            recursive_t = cls.recs_query()
            return db.session.query(recursive_t).filter(
                recursive_t.c.cid == str(node_id)).one_or_none()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return False

    @classmethod
    def get_child_list_recursive(cls, pid):
        """
        Get index list info.

        :param pid: pid of the index.
        :return: the list of index.
        """
        def recursive_p():
            recursive_p = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
            ).filter(Index.id == pid). \
                cte(name="recursive_p", recursive=True)

            rec_alias = aliased(recursive_p, name="recursive")
            test_alias = aliased(Index, name="test")
            recursive_p = recursive_p.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    func.cast(test_alias.id, db.Text) + '/' + rec_alias.c.path,
                ).filter(test_alias.id == rec_alias.c.pid)
            )
            path_index_searchs = db.session.query(recursive_p).filter_by(
                pid=0).one()
            return path_index_searchs.path
        path_index_searchs = recursive_p()

        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid"),
            func.cast(path_index_searchs, db.Text).label("path"),
            Index.public_state.label("public_state"),
        ).filter(Index.id == pid). \
            cte(name="recursive_t", recursive=True)

        rec_alias = aliased(recursive_t, name="rec")
        test_alias = aliased(Index, name="t")
        recursive_t = recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id,
                rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                test_alias.public_state,
            ).filter(test_alias.parent == rec_alias.c.cid)
        )
        query = db.session.query(recursive_t)
        q = query.order_by(recursive_t.c.path).all()
        return [str(item.cid) for item in q]

    @classmethod
    def recs_reverse_query(cls, pid=0):
        """Init select condition of index.

        :return: the query of db.session.
        """
        _id = str(pid)
        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid"),
            func.cast(Index.id, db.Text).label("path"),
            Index.index_name.label("name"),
            Index.index_name_english.label("name_en"),
            literal_column("1", db.Integer).label("lev"),
            Index.public_state.label("public_state"),
            Index.public_date.label("public_date"),
            Index.comment.label("comment"),
            Index.browsing_role.label("browsing_role"),
            Index.browsing_group.label("browsing_group"),
            Index.harvest_public_state.label("harvest_public_state")
        ).filter(Index.id == pid). \
            cte(name='recursive_t_' + _id, recursive=True)

        rec_alias = aliased(recursive_t, name="rec_" + _id)
        test_alias = aliased(Index, name="t_" + _id)
        return recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id,
                rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                case([(func.length(test_alias.index_name) == 0, None)],
                     else_=rec_alias.c.name + '-/-' + test_alias.index_name),
                rec_alias.c.name_en + '-/-' + test_alias.index_name_english,
                rec_alias.c.lev + 1,
                test_alias.public_state,
                test_alias.public_date,
                test_alias.comment,
                test_alias.browsing_role,
                test_alias.browsing_group,
                test_alias.harvest_public_state,
            ).filter(test_alias.id == rec_alias.c.pid)
        )

    @classmethod
    def recs_query(cls, pid=0):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        # !!! Important !!!
        # If add/delete columns in here,
        # please add/delete columns in Indexes.delete function, too.
        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid"),
            func.cast(Index.id, db.Text).label("path"),
            Index.index_name.label("name"),
            # add by ryuu at 1108 start
            Index.index_name_english.label("name_en"),
            # add by ryuu at 1108 end
            literal_column("1", db.Integer).label("lev"),
            Index.public_state.label("public_state"),
            Index.public_date.label("public_date"),
            Index.comment.label("comment"),
            Index.browsing_role.label("browsing_role"),
            Index.browsing_group.label("browsing_group"),
            Index.harvest_public_state.label("harvest_public_state")
        ).filter(Index.parent == pid). \
            cte(name="recursive_t", recursive=True)

        rec_alias = aliased(recursive_t, name="rec")
        test_alias = aliased(Index, name="t")
        recursive_t = recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id,
                rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                case([(func.length(test_alias.index_name) == 0, None)],
                     else_=rec_alias.c.name + '-/-' + test_alias.index_name),
                # add by ryuu at 1108 start
                rec_alias.c.name_en + '-/-' + test_alias.index_name_english,
                # add by ryuu at 1108 end
                rec_alias.c.lev + 1,
                test_alias.public_state,
                test_alias.public_date,
                test_alias.comment,
                test_alias.browsing_role,
                test_alias.browsing_group,
                test_alias.harvest_public_state,
            ).filter(test_alias.parent == rec_alias.c.cid)
        )

        return recursive_t

    @classmethod
    def recs_tree_query(cls, pid=0, ):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        lang = current_i18n.language
        if lang == 'ja':
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(
                    Index.id,
                    db.Text).label("path"),
                case([(func.length(func.coalesce(Index.index_name, '')) == 0,
                       Index.index_name_english)],
                     else_=Index.index_name).label('name'),
                case([(func.length(func.coalesce(Index.index_link_name, '')) == 0,
                       Index.index_link_name_english)],
                     else_=Index.index_link_name).label('link_name'),
                Index.index_link_enabled,
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                Index.coverpage_state,
                Index.recursive_coverpage_check,
                literal_column(
                    "1",
                    db.Integer).label("lev")).filter(
                Index.parent == pid). cte(
                        name="recursive_t",
                recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path
                    + '/'
                    + func.cast(
                        test_alias.id,
                        db.Text),
                    case([(func.length(
                        func.coalesce(test_alias.index_name, '')) == 0,
                        test_alias.index_name_english)],
                        else_=test_alias.index_name).label('name'),
                    case([(func.length(
                        func.coalesce(test_alias.index_link_name, '')) == 0,
                        test_alias.index_link_name_english)],
                        else_=test_alias.index_link_name).label('link_name'),
                    test_alias.index_link_enabled,
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    test_alias.coverpage_state,
                    test_alias.recursive_coverpage_check,
                    rec_alias.c.lev
                    + 1).filter(
                    test_alias.parent == rec_alias.c.cid))
        else:
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
                Index.index_name_english.label("name"),
                Index.index_link_name_english.label("link_name"),
                Index.index_link_enabled,
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                Index.coverpage_state,
                Index.recursive_coverpage_check,
                literal_column("1", db.Integer).label("lev")).filter(
                Index.parent == pid). \
                cte(name="recursive_t", recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                    test_alias.index_name_english,
                    test_alias.index_link_name_english,
                    test_alias.index_link_enabled,
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    test_alias.coverpage_state,
                    test_alias.recursive_coverpage_check,
                    rec_alias.c.lev + 1).filter(
                    test_alias.parent == rec_alias.c.cid)
            )

        return recursive_t

    @classmethod
    def recs_root_tree_query(cls, pid=0):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        lang = current_i18n.language
        if lang == 'ja':
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(
                    Index.id,
                    db.Text).label("path"),
                case([(func.length(func.coalesce(Index.index_name, '')) == 0,
                       Index.index_name_english)],
                     else_=Index.index_name).label('name'),
                case([(func.length(func.coalesce(Index.index_link_name, '')) == 0,
                       Index.index_link_name_english)],
                     else_=Index.index_link_name).label('link_name'),
                Index.index_link_enabled,
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                Index.coverpage_state,
                Index.recursive_coverpage_check,
                literal_column(
                    "1",
                    db.Integer).label("lev")).filter(
                Index.id == pid). cte(
                        name="recursive_t",
                recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path
                    + '/'
                    + func.cast(
                        test_alias.id,
                        db.Text),
                    case([(func.length(func.coalesce(
                        test_alias.index_name, '')) == 0,
                        test_alias.index_name_english)],
                        else_=test_alias.index_name),
                    case([(func.length(func.coalesce(
                        test_alias.index_link_name, '')) == 0,
                        test_alias.index_link_name_english)],
                        else_=test_alias.index_link_name),
                    test_alias.index_link_enabled,
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    test_alias.coverpage_state,
                    test_alias.recursive_coverpage_check,
                    rec_alias.c.lev
                    + 1).filter(
                    test_alias.parent == rec_alias.c.cid))
        else:
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
                Index.index_name_english.label("name"),
                Index.index_link_name_english.label("link_name"),
                Index.index_link_enabled,
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                Index.coverpage_state,
                Index.recursive_coverpage_check,
                literal_column("1", db.Integer).label("lev")).filter(
                Index.id == pid). \
                cte(name="recursive_t", recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                    test_alias.index_name_english,
                    test_alias.index_link_name_english,
                    test_alias.index_link_enabled,
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    test_alias.coverpage_state,
                    test_alias.recursive_coverpage_check,
                    rec_alias.c.lev + 1).filter(
                    test_alias.parent == rec_alias.c.cid)
            )

        return recursive_t

    @classmethod
    def get_harvest_public_state(cls, paths):
        """Check harvest_public_state of recursive index tree.

        Args:
            paths ([type]): [description]
        """
        def _query(path):
            return db.session. \
                query(func.every(Index.harvest_public_state).label(
                    'parent_state')).filter(Index.id.in_(path))

        try:
            _paths = deepcopy(paths)
            last_path = _paths.pop(-1).split('/')
            qry = _query(last_path)
            for i in range(len(_paths)):
                _paths[i] = _paths[i].split('/')
                _paths[i] = _query(_paths[i])
            smt = qry.union_all(*_paths).subquery()
            result = db.session.query(
                func.bool_or(
                    smt.c.parent_state).label('parent_state')).one()
            return result.parent_state
        except Exception as se:
            current_app.logger.debug(se)
            return False

    @classmethod
    def is_index(cls, path):
        ret = False

        if ":" in path:
            ret = True
        else:
            try:
                _n = int(path)
                current_app.logger.debug(path)
                _idx = cls.get_index(_n)
                if _idx is not None:
                    ret = True
                else:
                    ret = False
            except ValueError:
                ret = False

        return ret

    @classmethod
    def is_public_state(cls, paths):
        """Check have public state."""
        def _query(path):
            return db.session. \
                query(func.every(Index.public_state).label(
                    'parent_state')).filter(Index.id.in_(path))

        try:
            _paths = deepcopy(paths)
            last_path = _paths.pop(-1).split('/')
            qry = _query(last_path)
            for i in range(len(_paths)):
                _paths[i] = _paths[i].split('/')
                _paths[i] = _query(_paths[i])
            smt = qry.union_all(*_paths).subquery()
            result = db.session.query(
                func.bool_or(
                    smt.c.parent_state).label('parent_state')).one()
            return result.parent_state
        except Exception as se:
            current_app.logger.debug(se)
            return False

    @classmethod
    def is_public_state_and_not_in_future(cls, ids):
        """Check have public state and open date not in future."""
        def _query(_id):
            recursive_t = cls.recs_reverse_query(_id)
            return db.session.query(func.every(db.and_(
                recursive_t.c.public_state,
                db.or_(
                    recursive_t.c.public_date.is_(None),
                    recursive_t.c.public_date <= date.today()
                ))).label('parent_state'))

        try:
            _ids = deepcopy(ids)
            qry = _query(_ids.pop(-1))
            for i in range(len(_ids)):
                _ids[i] = _query(_ids[i])

            smt = qry.union_all(*_ids).subquery()
            result = db.session.query(
                func.bool_or(smt.c.parent_state).label('parent_state')).one()

            return result.parent_state
        except Exception as se:
            print(se)
            current_app.logger.debug(se)
            return False

    @classmethod
    def set_item_sort_custom(cls, index_id, sort_json={}):
        """Set custom sort."""
        sort_dict_db = {}

        for k, v in sort_json.items():
            try:
                i = int(v)
                if i > 0:
                    sort_dict_db[k] = i
            except BaseException:
                pass

        try:
            with db.session.begin_nested():
                index = cls.get_index(index_id)
                if not index:
                    return
                index.item_custom_sort = sort_dict_db
                db.session.merge(index)
            db.session.commit()
            return index
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def update_item_sort_custom_es(cls, index_path, sort_json=[]):
        """Set custom sort.

        :param index_path selected index path
        :param sort_json custom setted item sort

        """
        try:
            upd_item_sort_q = {
                "query": {
                    "match": {
                        "path.tree": "@index"
                    }
                }
            }
            es_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
            es_doc_type = current_app.config['INDEXER_DEFAULT_DOCTYPE']
            query_q = json.dumps(upd_item_sort_q).replace("@index", index_path)
            query_q = json.loads(query_q)
            indexer = RecordIndexer()
            res = indexer.client.search(
                index=es_index,
                body=query_q)

            for d in sort_json:
                for h in res.get("hits").get("hits"):
                    if int(
                            h.get('_source').get('control_number')) == int(
                            d.get("id")):
                        body = {
                            'doc': {
                                'custom_sort': d.get('custom_sort'),
                            }
                        }
                        indexer.client.update(
                            index=es_index,
                            doc_type=es_doc_type,
                            id=h.get("_id"),
                            body=body
                        )
                        break

        except Exception as ex:
            current_app.logger.debug(ex)
        return

    @classmethod
    def get_item_sort(cls, index_id):
        """Get items sort.

        :param index_id: search index id
        :return: sort list

        """
        item_custom_sort = db.session.query(
            Index.item_custom_sort).filter(
            Index.id == index_id).one_or_none()

        return item_custom_sort[0] if item_custom_sort else None

    @classmethod
    def have_children(cls, index_id):
        """Have children."""
        return Index.get_children(index_id)

    @classmethod
    def get_coverpage_state(cls, indexes: list):
        """
        Get coverpage state from indexes id.

        :param indexes: item's indexes id.
        """
        try:
            for item in Index.query.filter(Index.id.in_(indexes)).all():
                if item.coverpage_state:
                    return True

        except Exception as ex:
            current_app.logger.debug(ex)
        return False

    @classmethod
    def set_coverpage_state_resc(cls, index_id, state):
        """
        Set coverpage state for all index's children.

        :param index_id: search index id
        :param state: coverpage state of search index id
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.coverpage_state: state},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_coverpage_state_resc(index.id, state)

    @classmethod
    def set_public_state_resc(cls, index_id, state, date):
        """
        Set public state and public date for all index's children.

        :param index_id: search index id
        :param state: state of index
        :param date: date of index
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.public_state: state, Index.public_date: date},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_public_state_resc(index.id, state, date)

    @classmethod
    def set_contribute_role_resc(cls, index_id, contribute_role):
        """
        Set contribute role all index's children.

        :param index_id: search index id
        :param contribute_role: contribute role
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.contribute_role: contribute_role},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_contribute_role_resc(index.id, contribute_role)

    @classmethod
    def set_contribute_group_resc(cls, index_id, contribute_group):
        """
        Set contribute group for all index's children.

        :param index_id: search index id
        :param contribute_group: contribute group
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.contribute_group: contribute_group},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_contribute_group_resc(index.id, contribute_group)

    @classmethod
    def set_browsing_role_resc(cls, index_id, browsing_role):
        """
        Set coverpage state for all index's children.

        :param index_id: search index id
        :param browsing_role: browsing role
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.browsing_role: browsing_role},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_browsing_role_resc(index.id, browsing_role)

    @classmethod
    def set_browsing_group_resc(cls, index_id, browsing_group):
        """
        Set browsing group for all index's children.

        :param index_id: search index id
        :param browsing_group: browsing group
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.browsing_group: browsing_group},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_browsing_group_resc(index.id, browsing_group)

    @classmethod
    def set_online_issn_resc(cls, index_id, online_issn):
        """
        Set Online ISSN for all index's children.

        :param index_id: search index id
        :param online_issn: Online ISSN
        """
        Index.query.filter_by(parent=index_id). \
            update({Index.online_issn: online_issn},
                   synchronize_session='fetch')
        for index in Index.query.filter_by(parent=index_id).all():
            cls.set_online_issn_resc(index.id, online_issn)

    @classmethod
    def get_index_count(cls):
        """Get the total number of indexes."""
        return Index.query.count()

    @classmethod
    def get_child_list(cls, index_id):
        """
        Get index list info.

        :param index_id: Index identifier number.
        :return: The list of index.
        """
        recursive_t = cls.recs_query()
        query = db.session.query(recursive_t).filter(
            db.or_(recursive_t.c.pid == index_id,
                   recursive_t.c.cid == index_id))
        if not get_user_roles()[0]:
            query = query.filter(recursive_t.c.public_state)
        q = query.order_by(recursive_t.c.path).all()
        return q

    @classmethod
    def get_child_id_list(cls, index_id=0):
        """Get child id list without recursive."""
        q = Index.query.filter_by(parent=index_id). \
            order_by(Index.position).all()
        return [x.id for x in filter_index_list_by_role(q)]

    @classmethod
    def get_list_path_publish(cls, index_id):
        """
        Get list index path of index publish.

        :param index_id: Identifier of the index.
        :return: the list of index_path.
        """
        tree_path = get_publish_index_id_list(cls.get_index_tree(index_id),
                                              [])
        return tree_path

    @classmethod
    def get_public_indexes(cls):
        """Get child id list without recursive."""
        query = Index.query.filter_by(public_state=True).order_by(
            Index.updated.desc())
        return query.all()

    @classmethod
    def get_all_indexes(cls):
        """Get all indexes."""
        query = Index.query.all()
        return query

    @classmethod
    def get_all_parent_indexes(cls, index_id) -> list:
        """Get all parent indexes.

        Args:
            index_id ():

        Returns:
            [list]: parent indexes list.

        """
        # Define a CTE with recursive=True for the top portion of the query
        topq = Index.query.filter(Index.id == index_id)
        topq = topq.cte('cte', recursive=True)
        # Define the bottom part of the query by joining it with the top part
        bottomq = Index.query.join(topq, Index.id == topq.c.parent)
        # applying a union function
        recursive_q = topq.union(bottomq)
        # Get index data
        index_list = db.session.query(recursive_q).order_by(
            recursive_q.c.id).all()
        return index_list

    @classmethod
    def get_full_path_reverse(cls, index_id=0):
        """Get full path of index.

        :param index_id: Identifier of the index.
        :return: path.
        """
        recursive_t = cls.recs_reverse_query(index_id)
        qlst = [recursive_t.c.path]
        obj = db.session.query(*qlst).order_by(recursive_t.c.pid).first()
        return obj.path if obj else ''

    @classmethod
    def get_full_path(cls, index_id=0):
        """Get full path of index.

        :param index_id: Identifier of the index.
        :return: path.
        """
        reverse_path = cls.get_full_path_reverse(index_id)
        return '/'.join(reversed(reverse_path.split('/')))

    @classmethod
    def get_harverted_index_list(cls):
        """Get full path of index.

        :return: path.
        """
        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid")
        ).filter(
            Index.parent == 0,
            Index.harvest_public_state.is_(True)
        ).cte(name="recursive_t", recursive=True)

        rec_alias = aliased(recursive_t, name="rec")
        test_alias = aliased(Index, name="t")
        recursive_t = recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id
            ).filter(
                test_alias.parent == rec_alias.c.cid,
                test_alias.harvest_public_state.is_(True))
        )

        ret = []
        with db.session.begin_nested():
            qlst = [recursive_t.c.cid]
            indexes = db.session.query(*qlst). \
                order_by(recursive_t.c.pid).all()
            for idx in indexes:
                ret.append(str(idx[0]))
        return ret

    @classmethod
    def update_set_info(cls, index):
        """Create / Update oaiset setting."""
        from .tasks import update_oaiset_setting
        index_data = dict(index)
        index_data.pop('public_date')
        index_info = Indexes.get_path_name([index_data["id"]])[0]
        if index_info:
            index_info = index_info[:5]
        update_oaiset_setting.delay(index_info, index_data)

    @classmethod
    def delete_set_info(cls, action, index_id, id_list):
        """Delete oaiset setting."""
        if action == 'move':  # move items to parent index
            pass
        else:  # delete all index
            from .tasks import delete_oaiset_setting
            delete_oaiset_setting.delay(id_list)

    @classmethod
    def get_public_indexes_list(cls):
        """Get list id of public indexes.

        :return: path.
        """
        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid")
        ).filter(
            Index.parent == 0,
            Index.public_state.is_(True)
        ).filter(
            db.or_(Index.public_date.is_(None),
                   Index.public_date < datetime.utcnow())
        ).cte(name="recursive_t", recursive=True)

        rec_alias = aliased(recursive_t, name="rec")
        test_alias = aliased(Index, name="t")
        recursive_t = recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id
            ).filter(
                test_alias.parent == rec_alias.c.cid,
                test_alias.public_state.is_(True)
            ).filter(
                db.or_(test_alias.public_date.is_(None),
                       test_alias.public_date < datetime.utcnow()))
        )

        ids = []
        with db.session.begin_nested():
            qlst = [recursive_t.c.cid]
            indexes = db.session.query(*qlst). \
                order_by(recursive_t.c.pid).all()
            for idx in indexes:
                ids.append(str(idx[0]))
        return ids
