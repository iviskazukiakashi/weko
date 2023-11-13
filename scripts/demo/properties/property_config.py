S_IDENTIFIER = '123'                                    # system identifier
S_FILE = '125'                                          # system file
NUMBER_OF_PAGES = '126'                                 # ページ数
RESOURCE_TYPE_SIMPLE = '127'                            # 資源タイプ（シンプル）
STUDY_ID = '301'                                        # 調査番号
TOPIC = '303'                                           # トピック
RELATED_PUBLICATIONS = '304'                            # 関連文献
URI = '305'                                             # URI
SAMPLING = '306'                                        # 抽出
GEOCOVER = '307'                                        # 調査地域
DISTRIBUTOR = '308'                                     # 配布者
UNIT_OF_ANALYSIS = '309'                                # 観察単位（英語統制語彙）
DATA_TYPE = '310'                                       # データタイプ（英語統制語彙）
ACCESS = '311'                                          # アクセス制限（日本語統制語彙）
RELATED_STUDY = '312'                                   # 関連研究
TIME_PERIOD = '313'                                     # 開始時点/終了時点
COLLECTION_METHOD = '314'                               # 調査方法（英語統制語彙）
SERIES = '315'                                          # シリーズ
UNIVERSE = '316'                                        # 母集団
TITLE = '1001'                                          # タイトル
ALTERNATIVE_TITLE = '1002'                              # その他のタイトル
LANGUAGE = '1003'                                       # 言語
OTHER_LANGUAGE = '1004'                                 # その他の言語
ACCESS_RIGHT = '1005'                                   # アクセス権
APC = '1006'                                            # APC
RIGHTS = '1007'                                         # 権利情報
RIGHTS_HOLDER = '1008'                                  # 権利者情報
SUBJECT = '1009'                                        # 主題
DESCRIPTION = '1010'                                    # 内容記述
PUBLISHER = '1011'                                      # 出版者
DATE = '1012'                                           # 日付
RESOURCE_TYPE = '1014'                                  # 資源タイプ
VERSION = '1015'                                        # バージョン情報
VERSION_TYPE = '1016'                                   # 出版タイプ
IDENTIFIER = '1017'                                     # 識別子
IDENTIFIER_REGISTRATION = '1018'                        # ID登録
RELATION = '1019'                                       # 関連情報
TEMPORAL = '1020'                                       # 時間的範囲
GEOLOCATION = '1021'                                    # 位置情報
FUNDING_REFERENCE = '1022'                              # 助成情報
SOURCE_ID = '1023'                                      # 収録物識別子
SOURCE_TITLE = '1024'                                   # 収録物名
VOLUME = '1025'                                         # 巻
ISSUE = '1026'                                          # 号
BIBLIO_INFO = '1027'                                    # 書誌情報
START_PAGE = '1028'                                     # 開始ページ
END_PAGE = '1029'                                       # 終了ページ
DISSERTATION_NUMBER = '1030'                            # 学位授与番号
DEGREE_NAME = '1031'                                    # 学位名
DATE_GRANTED = '1032'                                   # 学位授与年月日
DEGREE_GRANTOR = '1033'                                 # 学位授与機関
CONFERENCE = '1034'                                     # 会議記述
FILE = '1035'                                           # ファイル情報
FILE_PRICE = '1036'                                     # 課金ファイル情報
THUMBNAIL = '1037'                                      # サムネイル
CREATOR = '1038'                                        # 作成者
CONTRIBUTOR = '1039'                                    # 寄与者
FULL_NAME = '1040'                                      # 氏名
HEADING = '1041'                                        # 見出し
TEXT = '1042'                                           # テキスト
TEXTAREA = '1043'                                       # テキストエリア
LINK = '1044'                                           # リンク
CHECKBOX = '1045'                                       # チェックボックス
RADIOBUTTON = '1046'                                    # ラジオボタン
LISTBOX = '1047'                                        # リストボックス
PUBLISHERINFO = '1048'                                  # 出版者情報
DATE_LITERAL = '1049'                                   # 日付（文字列）
DCNDL_EDITION = '1050'                                  # 版
DCNDL_VOLUME_TITLE = '1051'                             # 部編名
DCNDL_ORIGINAL_LANGUAGE = '1052'                        # 原文の言語
DCTERMS_EXTENT = '1053'                                 # ページ数
JPCOAR_FORMAT = '1054'                                  # 大きさ
JPCOAR_HOLDING_AGENT = '1055'                           # 所蔵機関
JPCOAR_DATASET_SERIES = '1056'                          # データセットシリーズ
JPCOAR_CATALOG = '1057'                                 # カタログ
DATASET_USAGE = '3001'                                  # データ名
USER_INFORMATION = '3002'                               # 登録者情報
GUARANTOR = '3003'                                      # 保証人
ADVISOR = '3004'                                        # 指導教員
RESEARCH_TITLE = '3005'                                 # 研究題目
RESEARCH_PLAN = '3006'                                  # 研究計画
USAGE_REPORT_ID = '3007'                                # 利用報告ID
WF_ISSUED_DATE = '3008'                                 # WF起票日
APPLICATION_DATE = '3009'                               # 申請日
APPROVAL_DATE = '3010'                                  # 承認日
ITEM_TITLE = '3011'                                     # アイテムタイトル
CORRESPONDING_USAGE_APPLICATION_ID = '3012'             # 対応する利用申請のID
CORRESPONDING_OUTPUT_ID = '3013'                        # 対応する成果物のID
ANNUAL_REPORT = '3014'                                  # 年次報告
STOP_CONTINUE = '3015'                                  # 終了／継続
AUTHOR_NAME = '3016'                                    # 著者名
OUTPUT_TYPE = '3017'                                    # 成果物のタイプ
PUBLISHED_MEDIA_NAME = '3018'                           # 公表媒体名
PUBLISHED_DOI_URL = '3019'                              # 公表URL（DOI）
PUBLISHED_DATE = '3020'                                 # 公表年月日
SUMMARY = '3021'                                        # 要約

EXCLUSION_LIST = []
# Exclusion property id list. The ID set in the list will not be registered.
# e.g.: EXCLUSION_LIST = [3020, 3021] or EXCLUSION_LIST = [PUBLISHED_DATE, SUMMARY]

SPECIFIED_LIST = [1009,1011,1019,1022,1038,1039,1048,1049,1050,1051,1052,1053,1054,1055,1056,1057]
# Specified property id list. The ID set in the list will be deleted and registered.
# e.g.: SPECIFIED_LIST = [3020, 3021] or SPECIFIED_LIST = [PUBLISHED_DATE, SUMMARY]

DEFAULT_MAPPING = {
    'display_lang_type': None,
    'jpcoar_v1_mapping': None,
    'jpcoar_mapping': None,
    'junii2_mapping': None,
    'lido_mapping': None,
    'lom_mapping': None,
    'oai_dc_mapping': None,
    'spase_mapping': None
}

LANGUAGE_VAL2_1 = [None, 'ja', 'ja-Kana', 'ja-Latn', 'en', 'fr', 'it', 'de', 'es', 'zh-cn', 'zh-tw', 'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']
LANGUAGE_VAL2_2 = [None, 'ja', 'ja-Latn', 'en', 'ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 'bm', 'ba', 'eu', 'be', 'bn', 'bh', 'bi', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 'zh', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', 'eo', 'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'ff', 'gl', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'ia', 'id', 'ie', 'ga', 'ig', 'ik', 'io', 'is', 'it', 'iu', 'jv', 'kl', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 'rw', 'ky', 'kv', 'kg', 'ko', 'ku', 'kj', 'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv', 'gv', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'nd', 'ne', 'ng', 'nb', 'nn', 'no', 'ii', 'nr', 'oc', 'oj', 'cu', 'om', 'or', 'os', 'pa', 'pi', 'fa', 'pl', 'ps', 'pt', 'qu', 'rm', 'rn', 'ro', 'ru', 'sa', 'sc', 'sd', 'se', 'sm', 'sg', 'sr', 'gd', 'sn', 'si', 'sk', 'sl', 'so', 'st', 'es', 'su', 'sw', 'ss', 'sv', 'ta', 'te', 'tg', 'th', 'ti', 'bo', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty', 'ug', 'uk', 'ur', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'wo', 'fy', 'xh', 'yi', 'yo', 'za', 'zu']
LANGUAGE_VAL3 = [None, 'jpn', 'eng', 'aar', 'abk', 'afr', 'aka', 'amh','ara', 'arg', 'asm', 'ava', 'ave', 'aym', 'aze', 'bak','bam', 'bel', 'ben', 'bis', 'bod', 'bos', 'bre', 'bul','cat', 'ces', 'cha', 'che', 'chu', 'chv', 'cor', 'cos','cre', 'cym', 'dan', 'deu', 'div', 'dzo', 'ell', 'epo','est', 'eus', 'ewe', 'fao', 'fas', 'fij', 'fin', 'fra','fry', 'ful', 'gla', 'gle', 'glg', 'glv', 'grn', 'guj','hat', 'hau', 'heb', 'her', 'hin', 'hmo', 'hrv', 'hun','hye', 'ibo', 'ido', 'iii', 'iku', 'ile', 'ina', 'ind','ipk', 'isl', 'ita', 'jav', 'kal', 'kan', 'kas', 'kat','kau', 'kaz', 'khm', 'kik', 'kin', 'kir', 'kom', 'kon','kor', 'kua', 'kur', 'lao', 'lat', 'lav', 'lim', 'lin','lit', 'ltz', 'lub', 'lug', 'mah', 'mal', 'mar', 'mkd','mlg', 'mlt', 'mon', 'mri', 'msa', 'mya', 'nau', 'nav','nbl', 'nde', 'ndo', 'nep', 'nld', 'nno', 'nob', 'nor','nya', 'oci', 'oji', 'ori', 'orm', 'oss', 'pan', 'pli','pol', 'por', 'pus', 'que', 'roh', 'ron', 'run', 'rus','sag', 'san', 'sin', 'slk', 'slv', 'sme', 'smo', 'sna','snd', 'som', 'sot', 'spa', 'sqi', 'srd', 'srp', 'ssw','sun', 'swa', 'swe', 'tah', 'tam', 'tat', 'tel', 'tgk','tgl', 'tha', 'tir', 'ton', 'tsn', 'tso', 'tuk', 'tur','twi', 'uig', 'ukr', 'urd', 'uzb', 'ven', 'vie', 'vol','wln', 'wol', 'xho', 'yid', 'yor', 'zha', 'zho', 'zul']
COUNTRY_VAL = [None, 'JPN', 'ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ARE', 'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 'AZE', 'BDI', 'BEL', 'BEN', 'BES', 'BFA', 'BGD', 'BGR', 'BHR', 'BHS', 'BIH', 'BLM', 'BLR', 'BLZ', 'BMU', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN', 'BVT', 'BWA', 'CAF', 'CAN', 'CCK', 'CHE', 'CHL', 'CHN', 'CIV', 'CMR', 'COD', 'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB', 'CUW', 'CXR', 'CYM', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA', 'DNK', 'DOM', 'DZA', 'ECU', 'EGY', 'ERI', 'ESH', 'ESP', 'EST', 'ETH', 'FIN', 'FJI', 'FLK', 'FRA', 'FRO', 'FSM', 'GAB', 'GBR', 'GEO', 'GGY', 'GHA', 'GIB', 'GIN', 'GLP', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD', 'GRL', 'GTM', 'GUF', 'GUM', 'GUY', 'HKG', 'HMD', 'HND', 'HRV', 'HTI', 'HUN', 'IDN', 'IMN', 'IND', 'IOT', 'IRL', 'IRN', 'IRQ', 'ISL', 'ISR', 'ITA', 'JAM', 'JEY', 'JOR', 'KAZ', 'KEN', 'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR', 'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LTU', 'LUX', 'LVA', 'MAC', 'MAF', 'MAR', 'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD', 'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MNP', 'MOZ', 'MRT', 'MSR', 'MTQ', 'MUS', 'MWI', 'MYS', 'MYT', 'NAM', 'NCL', 'NER', 'NFK', 'NGA', 'NIC', 'NIU', 'NLD', 'NOR', 'NPL', 'NRU', 'NZL', 'OMN', 'PAK', 'PAN', 'PCN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRI', 'PRK', 'PRT', 'PRY', 'PSE', 'PYF', 'QAT', 'REU', 'ROU', 'RUS', 'RWA', 'SAU', 'SDN', 'SEN', 'SGP', 'SGS', 'SHN', 'SJM', 'SLB', 'SLE', 'SLV', 'SMR', 'SOM', 'SPM', 'SRB', 'SSD', 'STP', 'SUR', 'SVK', 'SVN', 'SWE', 'SWZ', 'SXM', 'SYC', 'SYR', 'TCA', 'TCD', 'TGO', 'THA', 'TJK', 'TKL', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV', 'TWN', 'TZA', 'UGA', 'UKR', 'UMI', 'URY', 'USA', 'UZB', 'VAT', 'VCT', 'VEN', 'VGB', 'VIR', 'VNM', 'VUT', 'WLF', 'WSM', 'YEM', 'ZAF', 'ZMB', 'ZWE']
AFFILIATION_SCHEME_VAL = [None, 'kakenhi', 'ISNI', 'Ringgold', 'GRID']
DATE_TYPE_VAL = [None, 'Accepted', 'Available', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid']
FILE_TYPE_VAL = [None, 'abstract', 'dataset', 'fulltext','iiif', 'software', 'summary', 'thumbnail', 'other']
DATEPICKER_URL = '/static/templates/weko_deposit/datepicker.html'
DATEPICKER_MULTI_FORMAT_URL = '/static/templates/weko_deposit/datepicker_multi_format.html'
DATALIST_URL = "/static/templates/weko_deposit/datalist.html"
AWARD_NUMBER_TYPE = [None,'JGN']
FUNDER_IDENTIFIER_TYPE_VAL = [None,'Crossref Funder','e-Rad_funder','GRID','ISNI','ROR','Other']
FUNDER_IDENTIFIER_TYPE_LBL = ['','Crossref Funder','e-Rad_funder','GRID【非推奨】','ISNI','ROR','Other']
NAME_TYPE_VAL = [None,'Personal','Organizational']
SUBJECT_SCHEME_LBL = ['','BSH','DDC','e-Rad_field','JEL','LCC','LCSH','MeSH','NDC','NDLC','NDLSH','SciVal','UDC','Other']
SUBJECT_SCHEME_VAL = [None,'BSH','DDC','e-Rad_field','JEL','LCC','LCSH','MeSH','NDC','NDLC','NDLSH','SciVal','UDC','Other']
RELATION_TYPE  = [
    None,
    'isVersionOf',
    'hasVersion',
    'isPartOf',
    'hasPart',
    'isReferencedBy',
    'references',
    'isFormatOf',
    'hasFormat',
    'isReplacedBy',
    'replaces',
    'isRequiredBy',
    'requires',
    'isSupplementedBy',
    'isSupplementTo',
    'isIdenticalTo',
    'isDerivedFrom',
    'isSourceOf',
    'isCitedBy',
    'Cites',
    'inSeries'
]
RELATION_ID_TYPE_LBL = [
    '',
    'ARK',
    'arXiv',
    'DOI',
    'HDL',
    'ICHUSHI',
    'ISBN',
    'J-GLOBAL',
    'Local',
    'PISSN',
    'EISSN',
    'ISSN【非推奨】',
    'NAID',
    'NCID',
    'PMID【現在不使用】',
    'PURL',
    'SCOPUS',
    'URI',
    'WOS',
    'CRID'
]
RELATION_ID_TYPE_VAL = [
    None,
    'ARK',
    'arXiv',
    'DOI',
    'HDL',
    'ICHUSHI',
    'ISBN',
    'J-GLOBAL',
    'Local',
    'PISSN',
    'EISSN',
    'ISSN',
    'NAID',
    'NCID',
    'PMID',
    'PURL',
    'SCOPUS',
    'URI',
    'WOS',
    'CRID'
]

HOLDING_AGENT_NAMEID_SCHEMA_VAL=[None,'kakenhi', 'ISNI', 'Ringgold', 'GRID', 'ROR', 'FANO', 'ISIL', 'MARC', 'OCLC']
HOLDING_AGENT_NAMEID_SCHEMA_LBL=['','kakenhi【非推奨】', 'ISNI', 'Ringgold', 'GRID【非推奨】', 'ROR', 'FANO', 'ISIL', 'MARC', 'OCLC']
