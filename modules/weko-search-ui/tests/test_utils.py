import pytest
import json
import os

from weko_records.api import ItemTypes
from weko_search_ui.utils import (
    validation_file_open_date,
    check_import_items,
    unpackage_import_file,
    read_stats_csv,
    handle_check_date,
    get_list_key_of_iso_date,
    get_item_type,
)
from unittest.mock import patch, Mock
from weko_search_ui import WekoSearchUI
from flask_babelex import Babel

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

@pytest.fixture()
def test_records():
    results = []
    #
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord00.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord01.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord02.json"),
            "output": "",
        }
    )
    # 存在しない日付が設定されている
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "noExistentDate00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    # 日付がYYYY-MM-DD でない
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat01.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat02.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )

    return results


def test_validation_file_open_date(app, test_records):
    for t in test_records:
        filepath = t.get("input")
        result = t.get("output")
        with open(filepath, encoding="utf-8") as f:
            ret = json.load(f)
        with app.app_context():
            assert validation_file_open_date(ret) == result


@pytest.fixture()
def test_list_records():
    tmp = []
    results = []
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records00.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records00_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records01.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records01_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records02.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records02_result.json"
            ),
        }
    )

    for t in tmp:
        with open(t.get("input"), encoding="utf-8") as f:
            input_data = json.load(f)
        with open(t.get("output"), encoding="utf-8") as f:
            output_data = json.load(f)
        results.append({"input": input_data, "output": output_data})
    return results

@pytest.fixture()
def mocker_itemtype(mocker):
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15

    mocker.patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type)
    


def test_handle_check_date(app, test_list_records, mocker_itemtype):
    for t in test_list_records:
        input_data = t.get("input")
        output_data = t.get("output")
        with app.app_context():
            ret = handle_check_date(input_data)
            assert ret == output_data


# def test_read_stats_csv():
#     from flask import Flask, current_app
#     app = Flask(__name__)
#     app.config.update(
#         SECRET_KEY='SECRET_KEY',
#         TESTING=True,
#         INDEX_IMG='indextree/36466818-image.jpg',
#     )
#     Babel(app)
#     WekoSearchUI(app)
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
#     with app.app_context():
#         assert read_stats_csv(os.path.join(FIXTURE_DIR,'importdata00/items.csv'),'items.csv') == ''

# @pytest.fixture()
# def test_unpacked_importdata():
#     files = []
#     files.append({'data_path': os.path.join(FIXTURE_DIR,'importdata00'),'csv_file_name':'items.csv','force_new':False})
#     return files

# def test_unpackage_import_file(test_unpacked_importdata):
#     from flask import Flask, current_app
#     app = Flask(__name__)
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
#     with app.app_context():
#         for file in test_unpacked_importdata:
#             assert unpackage_import_file(file.get('data_path'),file.get('csv_file_name'),file.get('force_new'))==''

@pytest.fixture()
def test_importdata():
    files = [os.path.join(FIXTURE_DIR,'import00.zip')
    ]
    return files

def test_check_import_items(app,test_importdata,mocker_itemtype):
    app.config['WEKO_SEARCH_UI_IMPORT_TMP_PREFIX'] = 'importtest'
    with app.app_context():
        for file in test_importdata:
            assert check_import_items(file,False,False)==''


def test_get_list_key_of_iso_date():
    form = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type", "form00.json"
    )
    result = [
        "item_1617186660861.subitem_1522300722591",
        "item_1617187056579.bibliographicIssueDates.bibliographicIssueDate",
        "item_1617187136212.subitem_1551256096004",
        "item_1617605131499.fileDate.fileDateValue",
    ]
    with open(form, encoding="utf-8") as f:
        df = json.load(f)
    assert get_list_key_of_iso_date(df) == result


def test_get_item_type(mocker_itemtype):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_get_item_type_result.json"
    )
    with open(filepath, encoding="utf-8") as f:
        except_result = json.load(f)
    result = get_item_type(15)
    assert result['is_lastest']==except_result['is_lastest']
    assert result['name']==except_result['name']
    assert result['item_type_id']==except_result['item_type_id']
    assert result['schema']==except_result['schema']
    assert result==except_result
    