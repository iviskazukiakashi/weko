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

"""Module of weko-records-ui utils."""

import base64
from datetime import datetime, timedelta
from decimal import Decimal
from typing import NoReturn, Tuple

from flask import current_app, request
from flask_babelex import gettext as _
from invenio_db import db
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from passlib.handlers.oracle import oracle10
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping

from .models import FileOnetimeDownload, FilePermission
from .permissions import check_create_usage_report, check_user_group_permission


def check_items_settings():
    """Check items setting."""
    settings = AdminSettings.get('items_display_settings')
    current_app.config['EMAIL_DISPLAY_FLG'] = settings.items_display_email
    current_app.config['ITEM_SEARCH_FLG'] = settings.items_search_author
    if hasattr(settings, 'item_display_open_date'):
        current_app.config['OPEN_DATE_DISPLAY_FLG'] = \
            settings.item_display_open_date


def get_record_permalink(record):
    """
    Get latest doi/cnri's value of record.

    :param record: index_name_english
    :return: pid value of doi/cnri.
    """
    doi = record.pid_doi
    cnri = record.pid_cnri

    if doi and cnri:
        if doi.updated > cnri.updated:
            return doi.pid_value
        else:
            return cnri.pid_value
    elif doi or cnri:
        return doi.pid_value if doi else cnri.pid_value

    return None


def get_groups_price(record: dict) -> list:
    """Get the prices of Billing files set in each group.

    :param record: Record metadata.
    :return: The prices of Billing files set in each group.
    """
    groups_price = list()
    for _, value in record.items():
        if isinstance(value, dict):
            attr_value = value.get('attribute_value_mlt')
            if attr_value and isinstance(attr_value, list):
                for attr in attr_value:
                    group_price = attr.get('groupsprice')
                    file_name = attr.get('filename')
                    if file_name and group_price:
                        result_data = {
                            'file_name': file_name,
                            'groups_price': group_price
                        }
                        groups_price.append(result_data)

    return groups_price


def get_billing_file_download_permission(groups_price: list) -> dict:
    """Get billing file download permission.

    :param groups_price: The prices of Billing files set in each group
    :return:Billing file permission dictionary.
    """
    billing_file_permission = dict()
    for data in groups_price:
        file_name = data.get('file_name')
        group_price_list = data.get('groups_price')
        if file_name and isinstance(group_price_list, list):
            is_ok = False
            for group_price in group_price_list:
                if isinstance(group_price, dict):
                    group_id = group_price.get('group')
                    is_ok = check_user_group_permission(group_id)
                    if is_ok:
                        break
            billing_file_permission[file_name] = is_ok

    return billing_file_permission


def get_min_price_billing_file_download(groups_price: list,
                                        billing_file_permission: dict) -> dict:
    """Get min price billing file download.

    :param groups_price: The prices of Billing files set in each group
    :param billing_file_permission: Billing file permission dictionary.
    :return:Billing file permission dictionary.
    """
    min_prices = dict()
    for data in groups_price:
        file_name = data.get('file_name')
        group_price_list = data.get('groups_price')
        if not billing_file_permission.get(file_name):
            continue
        if file_name and isinstance(group_price_list, list):
            min_price = None
            for group_price in group_price_list:
                if isinstance(group_price, dict):
                    price = group_price.get('price')
                    group_id = group_price.get('group')
                    is_ok = check_user_group_permission(group_id)
                    try:
                        price = Decimal(price)
                    except Exception as error:
                        current_app.logger.debug(error)
                        price = None
                    if is_ok and price \
                            and (not min_price or min_price > price):
                        min_price = price
            if min_price:
                min_prices[file_name] = min_price

    return min_prices


def is_billing_item(item_type_id):
    """Checks if item is a billing item based on its meta data schema."""
    item_type = ItemTypes.get_by_id(id_=item_type_id)
    if item_type:
        properties = item_type.schema['properties']
        for meta_key in properties:
            if properties[meta_key]['type'] == 'object' and \
               'groupsprice' in properties[meta_key]['properties'] or \
                properties[meta_key]['type'] == 'array' and 'groupsprice' in \
                    properties[meta_key]['items']['properties']:
                return True
        return False


def soft_delete(recid):
    """Soft delete item."""
    try:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=recid).first()
        if not pid:
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid', object_uuid=recid).first()
        if pid.status == PIDStatus.DELETED:
            return

        versioning = PIDVersioning(child=pid)
        if not versioning.exists:
            return
        all_ver = versioning.children.all()
        draft_pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value="{}.0".format(pid.pid_value.split(".")[0])
        ).one_or_none()

        if draft_pid:
            all_ver.append(draft_pid)

        for ver in all_ver:
            depid = PersistentIdentifier.query.filter_by(
                pid_type='depid', object_uuid=ver.object_uuid).first()
            if depid:
                rec = RecordMetadata.query.filter_by(
                    id=ver.object_uuid).first()
                dep = WekoDeposit(rec.json, rec)
                dep['path'] = []
                dep.indexer.update_path(dep, update_revision=False)
                FeedbackMailList.delete(ver.object_uuid)
                dep.remove_feedback_mail()
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=ver.object_uuid)
            for p in pids:
                p.status = PIDStatus.DELETED
            db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex


def restore(recid):
    """Restore item."""
    try:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=recid).first()
        if not pid:
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid', object_uuid=recid).first()
        if pid.status != PIDStatus.DELETED:
            return

        versioning = PIDVersioning(child=pid)
        if not versioning.exists:
            return
        all_ver = versioning.children.all()
        draft_pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value="{}.0".format(pid.pid_value.split(".")[0])
        ).one_or_none()

        if draft_pid:
            all_ver.append(draft_pid)

        for ver in all_ver:
            ver.status = PIDStatus.REGISTERED
            depid = PersistentIdentifier.query.filter_by(
                pid_type='depid', object_uuid=ver.object_uuid).first()
            if depid:
                depid.status = PIDStatus.REGISTERED
                rec = RecordMetadata.query.filter_by(id=ver.object_uuid).first()
                dep = WekoDeposit(rec.json, rec)
                dep.indexer.update_path(dep, update_revision=False)
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=ver.object_uuid)
            for p in pids:
                p.status = PIDStatus.REGISTERED
            db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex


def get_list_licence():
    """Get list license.

    @return:
    """
    list_license_result = []
    list_license_from_config = \
        current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
    for license_obj in list_license_from_config:
        list_license_result.append({'value': license_obj.get('value', ''),
                                    'name': license_obj.get('name', '')})
    return list_license_result


def get_license_pdf(license, item_metadata_json, pdf, file_item_id, footer_w,
                    footer_h, cc_logo_xposition, item):
    """Get license pdf.

    @param license:
    @param item_metadata_json:
    @param pdf:
    @param file_item_id:
    @param footer_w:
    @param footer_h:
    @param cc_logo_xposition:
    @param item:
    @return:
    """
    from .views import blueprint
    license_icon_pdf_location = \
        current_app.config['WEKO_RECORDS_UI_LICENSE_ICON_PDF_LOCATION']
    if license == 'license_free':
        txt = item_metadata_json[file_item_id][0].get('licensefree')
        if txt is None:
            txt = ''
        pdf.multi_cell(footer_w, footer_h, txt, 0, 'L', False)
    else:
        src = blueprint.root_path + license_icon_pdf_location + item['src_pdf']
        txt = item['txt']
        lnk = item['href_pdf']
        pdf.multi_cell(footer_w, footer_h, txt, 0, 'L', False)
        pdf.ln(h=2)
        pdf.image(
            src,
            x=cc_logo_xposition,
            y=None,
            w=0,
            h=0,
            type='',
            link=lnk)


def get_pair_value(name_keys, lang_keys, datas):
    """Get pairs value of name and language.

    :param name_keys:
    :param lang_keys:
    :param datas:
    :return:
    """
    if len(name_keys) == 1 and len(lang_keys) == 1:
        if isinstance(datas, list):
            for data in datas:
                for name, lang in get_pair_value(name_keys, lang_keys, data):
                    yield name, lang
        elif isinstance(datas, dict) and (
                name_keys[0] in datas or lang_keys[0] in datas):
            yield datas.get(name_keys[0], ''), datas.get(lang_keys[0], '')
    else:
        if isinstance(datas, list):
            for data in datas:
                for name, lang in get_pair_value(name_keys, lang_keys, data):
                    yield name, lang
        elif isinstance(datas, dict):
            for name, lang in get_pair_value(name_keys[1:], lang_keys[1:],
                                             datas.get(name_keys[0])):
                yield name, lang


def hide_item_metadata(record):
    """Hiding emails and hidden item metadata.

    :param record:
    :return:
    """
    from weko_items_ui.utils import get_ignore_item, hide_meta_data_for_role
    check_items_settings()

    record['weko_creator_id'] = record.get('owner')

    if hide_meta_data_for_role(record):
        list_hidden = get_ignore_item(record['item_type_id'])
        record = hide_by_itemtype(record, list_hidden)

        if not current_app.config['EMAIL_DISPLAY_FLG']:
            record = hide_by_email(record)

        return True

    record.pop('weko_creator_id')
    return False


def hide_item_metadata_email_only(record):
    """Hiding emails only.

    :param name_keys:
    :param lang_keys:
    :param datas:
    :return:
    """
    from weko_items_ui.utils import hide_meta_data_for_role
    check_items_settings()

    record['weko_creator_id'] = record.get('owner')

    if hide_meta_data_for_role(record) and \
            not current_app.config['EMAIL_DISPLAY_FLG']:
        record = hide_by_email(record)

        return True

    record.pop('weko_creator_id')
    return False


def hide_by_email(item_metadata):
    """Hiding emails.

    :param item_metadata:
    :return:
    """
    subitem_keys = current_app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS']

    # Hidden owners_ext.email
    if item_metadata.get('_deposit') and \
            item_metadata['_deposit'].get('owners_ext'):
        del item_metadata['_deposit']['owners_ext']['email']

    for item in item_metadata:
        _item = item_metadata[item]
        if isinstance(_item, dict) and \
                _item.get('attribute_value_mlt'):
            for _idx, _value in enumerate(_item['attribute_value_mlt']):
                for key in subitem_keys:
                    if key in _value.keys():
                        del _item['attribute_value_mlt'][_idx][key]

    return item_metadata


def hide_by_itemtype(item_metadata, hidden_items):
    """Hiding item type metadata.

    :param item_metadata:
    :param hidden_items:
    :return:
    """
    def del_hide_sub_metadata(keys, metadata):
        """Delete hide metadata."""
        if isinstance(metadata, dict):
            data = metadata.get(keys[0])
            if data:
                if len(keys) > 1:
                    del_hide_sub_metadata(keys[1:], data)
                else:
                    del metadata[keys[0]]
        elif isinstance(metadata, list):
            count = len(metadata)
            for index in range(count):
                del_hide_sub_metadata(keys, metadata[index])

    for hide_key in hidden_items:
        if isinstance(hide_key, str) \
                and item_metadata.get(hide_key):
            del item_metadata[hide_key]
        elif isinstance(hide_key, list) and \
                item_metadata.get(hide_key[0]):
            del_hide_sub_metadata(
                hide_key[1:],
                item_metadata[
                    hide_key[0]]['attribute_value_mlt'])

    return item_metadata


def is_show_email_of_creator(item_type_id):
    """Check setting show/hide email for 'Detail' and 'PDF Cover Page' screen.

    :param item_type_id: item type id of current record.
    :return: True/False, True: show, False: hide.
    """
    def get_creator_id(item_type_id):
        type_mapping = Mapping.get_record(item_type_id)
        item_map = get_mapping(type_mapping, "jpcoar_mapping")
        creator = 'creator.creatorName.@value'
        creator_id = None
        if creator in item_map:
            creator_id = item_map[creator].split('.')[0]
        return creator_id

    def item_type_show_email(item_type_id):
        # Get flag of creator's email hide from item type.
        creator_id = get_creator_id(item_type_id)
        if not creator_id:
            return None
        item_type = ItemTypes.get_by_id(item_type_id)
        schema_editor = item_type.render.get('schemaeditor', {})
        schema = schema_editor.get('schema', {})
        creator = schema.get(creator_id)
        if not creator:
            return None
        properties = creator.get('properties', {})
        creator_mails = properties.get('creatorMails', {})
        items = creator_mails.get('items', {})
        properties = items.get('properties', {})
        creator_mail = properties.get('creatorMail', {})
        is_hide = creator_mail.get('isHide', None)
        return is_hide

    def item_setting_show_email():
        # Display email from setting item admin.
        settings = AdminSettings.get('items_display_settings')
        is_display = settings.items_display_email
        return is_display

    is_hide = item_type_show_email(item_type_id)
    is_display = item_setting_show_email()
    return not is_hide and is_display


def check_and_create_usage_report(record, file_object):
    """Check and create usage report.

    :param file_object:
    :param record:
    :return:
    """
    access_role = file_object.get('accessrole', '')
    if 'open_restricted' in access_role:
        permission = check_create_usage_report(record, file_object)
        if permission is not None:
            from weko_workflow.utils import create_usage_report
            activity_id = create_usage_report(
                permission.usage_application_activity_id)
            if activity_id is not None:
                FilePermission.update_usage_report_activity_id(permission,
                                                               activity_id)


def generate_one_time_download_url(
    file_name: str, record_id: str, guest_mail: str
) -> str:
    """Generate one time download URL.

    :param file_name: File name
    :param record_id: File Version ID
    :param guest_mail: guest email
    :return:
    """
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    download_pattern = current_app.config[
        'WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN']
    current_date = datetime.now().strftime("%Y-%m-%d")
    hash_value = download_pattern.format(file_name, record_id, guest_mail,
                                         current_date)
    secret_token = oracle10.hash(secret_key, hash_value)

    token_pattern = "{} {} {} {}"
    token = token_pattern.format(record_id, guest_mail, current_date,
                                 secret_token)
    token_value = base64.b64encode(token.encode()).decode()
    host_name = request.host_url
    url = "{}record/{}/file/onetime/{}?token={}" \
        .format(host_name, record_id, file_name, token_value)
    return url


def parse_one_time_download_token(token: str) -> Tuple[str, Tuple]:
    """Parse onetime download token

    @param token:
    @return:
    """
    error = _("Token is invalid.")
    if token is None:
        return error, ()
    try:
        decode_token = base64.b64decode(token.encode()).decode()
        param = decode_token.split(" ")
        if not param or len(param) != 4:
            return error, ()

        return "", (param[0], param[1], param[2], param[3])
    except Exception as err:
        current_app.logger.error(err)
        return error, ()


def validate_onetime_download_token(
    file_name: str, record_id: str, guest_mail: str, date: str, token: str
) -> Tuple[bool, str]:
    """Validate onetime download token.

    @param file_name:
    @param record_id:
    @param guest_mail:
    @param date:
    @param token:
    @return:
    """
    token_invalid = _("Token is invalid.")
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    download_deadline = current_app.config['WEKO_RECORDS_UI_DOWNLOAD_DEADLINE']
    downloads_max = current_app.config['WEKO_RECORDS_UI_DOWNLOADS_MAX']
    download_pattern = current_app.config[
        'WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN']
    hash_value = download_pattern.format(file_name, record_id, guest_mail, date)
    if not oracle10.verify(secret_key, token, hash_value):
        current_app.logger.debug('Validate token error: {}'.format(hash_value))
        return False, token_invalid
    try:
        download_date = datetime.strptime(date, "%Y-%m-%d").date() + timedelta(
            download_deadline)
        current_date = datetime.now().date()
        if current_date > download_date:
            return False, _("The download expiration date has expired.")

        file_downloads = FileOnetimeDownload.find(
            file_name=file_name, record_id=record_id, user_mail=guest_mail
        )
        if file_downloads and len(file_downloads) > 0:
            download_count = file_downloads[0].download_count
            if download_count >= downloads_max:
                return False, _(
                    "The maximum number of downloads has been exceeded.")
        return True, ""
    except Exception as err:
        current_app.logger.error('Validate onetime download token error:')
        current_app.logger.error(err)
        return False, token_invalid


def get_onetime_download_count(file_name: str, record_id: str,
                               user_mail: str) -> NoReturn:
    """Get onetime download count.

    @param file_name:
    @param record_id:
    @param user_mail:
    @return:
    """
    file_downloads = FileOnetimeDownload.find(
        file_name=file_name, record_id=record_id, user_mail=user_mail
    )
    return file_downloads


def update_onetime_download_count(file_name: str, record_id: str,
                                  user_mail: str) -> NoReturn:
    """Update onetime download count.

    @param file_name:
    @param record_id:
    @param user_mail:
    @return:
    """
    return FileOnetimeDownload.update_download_count(
        file_name=file_name, record_id=record_id, user_mail=user_mail
    )
