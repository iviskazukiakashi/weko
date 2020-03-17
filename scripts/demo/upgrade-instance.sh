#!/usr/bin/env bash

main() {

mkdir -p ../../modules/weko-workflow/weko_workflow/alembic
cp -a ../../scripts/demo/alembic/. ../../modules/weko-workflow/weko_workflow/alembic/
docker-compose exec -u root web invenio alembic upgrade heads


bash backup.sh


git checkout sp31 && git pull


docker-compose build && docker-compose up -d && docker-compose exec web ./scripts/populate-instance.sh
docker-compose exec web invenio collect -v && docker-compose exec web invenio assets build


bash restore.sh


curl -XPUT 'http://elasticsearch:9200/tenant2-weko-item-v1.0.0' -H 'Content-Type: application/json' -d '
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "index.mapping.total_fields.limit": 10000,
    "analysis": {
      "tokenizer": {
        "ja_tokenizer": {
          "type": "kuromoji_tokenizer",
          "mode": "search"
        },
        "ngram_tokenizer": {
          "type": "nGram",
          "min_gram": 2,
          "max_gram": 3,
          "token_chars": [
            "letter",
            "digit"
          ]
        }
      },
      "char_filter": {
        "weko_char_filter": {
          "type": "mapping",
          "mappings_path": "kui.txt"
        }
      },
      "analyzer": {
        "default": {
          "tokenizer": "ja_tokenizer",
          "filter": [
            "kuromoji_baseform",
            "kuromoji_part_of_speech",
            "cjk_width",
            "stop",
            "kuromoji_stemmer",
            "lowercase"
          ],
          "char_filter": [
            "weko_char_filter"
          ]
        },
        "ngram_analyzer": {
          "type": "custom",
          "char_filter": [
            "weko_char_filter",
            "html_strip"
          ],
          "tokenizer": "ngram_tokenizer",
          "filter": [
            "cjk_width",
            "lowercase"
          ]
        },
        "wk_analyzer": {
          "type": "custom",
          "char_filter": [
            "html_strip"
          ],
          "tokenizer": "standard",
          "filter": [
            "standard",
            "lowercase",
            "stop",
            "cjk_width"
          ]
        },
        "paths": {
          "tokenizer": "path_hierarchy"
        }
      }
    }
  },
  "mappings": {
    "item-v1.0.0": {
      "properties": {
        "path": {
          "type": "keyword",
          "index": true,
          "fields": {
            "tree": {
              "type": "text",
              "fielddata": true,
              "analyzer": "paths"
            }
          }
        },
        "item_type_id": {
          "type": "keyword",
          "index": true
        },
        "itemtype": {
          "type": "text",
          "fielddata": true,
          "copy_to": [
            "search_other"
          ]
        },
        "publish_status": {
          "type": "keyword",
          "index": true
        },
        "publish_date": {
          "type": "date",
          "format": "yyyy-MM-dd||yyyy-MM||yyyy"
        },
        "_oai": {
          "type": "object",
          "properties": {
            "id": {
              "type": "keyword",
              "index": true
            },
            "sets": {
              "type": "keyword",
              "index": true
            },
            "updated": {
              "type": "date"
            }
          }
        },
        "control_number": {
          "type": "integer",
          "index": true
        },
        "title": {
          "type": "keyword",
          "index": true,
          "copy_to": [
            "search_title"
          ]
        },
        "feedback_mail_list": {
          "type": "nested",
          "properties": {
            "author_id": {
              "type": "keyword",
              "index": true
            },
            "email": {
              "type": "keyword",
              "index": true
            }
          }
        },
        "alternative": {
          "type": "keyword",
          "index": true,
          "copy_to": [
            "search_title"
          ]
        },
        "creator": {
          "type": "object",
          "properties": {
            "nameIdentifier": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_creator"
              ]
            },
            "creatorName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_creator"
              ]
            },
            "familyName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_creator"
              ]
            },
            "givenName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_creator"
              ]
            },
            "creatorAlternative": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_creator"
              ]
            },
            "affiliation": {
              "type": "object",
              "properties": {
                "nameIdentifier": {
                  "type": "keyword",
                  "index": true,
                  "copy_to": [
                    "search_identifier"
                  ]
                },
                "affiliationName": {
                  "type": "keyword",
                  "index": true,
                  "copy_to": [
                    "search_other"
                  ]
                }
              }
            }
          }
        },
        "contributor": {
          "type": "object",
          "properties": {
            "@attributes": {
              "type": "object",
              "properties": {
                "contributorType": {
                  "type": "keyword"
                }
              }
            },
            "nameIdentifier": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_contributor"
              ]
            },
            "contributorName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_contributor"
              ]
            },
            "familyName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_contributor"
              ]
            },
            "givenName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_contributor"
              ]
            },
            "contributorAlternative": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_contributor"
              ]
            },
            "affiliation": {
              "type": "object",
              "properties": {
                "nameIdentifier": {
                  "type": "keyword",
                  "index": true,
                  "copy_to": [
                    "search_identifier"
                  ]
                },
                "affiliationName": {
                  "type": "keyword",
                  "index": true,
                  "copy_to": [
                    "search_other"
                  ]
                }
              }
            }
          }
        },
        "accessRights": {
          "type": "keyword",
          "index": true,
          "copy_to": [
            "search_other"
          ]
        },
        "apc": {
          "type": "text",
          "index": true,
          "copy_to": [
            "search_other"
          ]
        },
        "rights": {
          "type": "text",
          "copy_to": [
            "search_other"
          ]
        },
        "rightsHolder": {
          "type": "object",
          "properties": {
            "nameIdentifier": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_identifier"
              ]
            },
            "rightsHolderName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            }
          }
        },
        "subject": {
          "type": "nested",
          "properties": {
            "value": {
              "type": "text",
              "copy_to": [
                "search_other"
              ]
            },
            "subjectScheme": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_attr"
              ]
            }
          }
        },
        "description": {
          "type": "object",
          "properties": {
            "value": {
              "type": "keyword",
              "copy_to": [
                "search_des"
              ]
            },
            "descriptionType": {
              "type": "keyword"
            }
          }
        },
        "publisher": {
          "type": "text",
          "copy_to": [
            "search_publisher"
          ]
        },
        "date": {
          "type": "nested",
          "properties": {
            "dateType": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_attr"
              ]
            },
            "value": {
              "type": "date",
              "format": "yyyy-MM-dd||yyyy-MM||yyyy"
            }
          }
        },
        "language": {
          "type": "keyword",
          "copy_to": [
            "search_other"
          ]
        },
        "version": {
          "type": "text",
          "index": true,
          "copy_to": [
            "search_other"
          ]
        },
        "versionType": {
          "type": "text",
          "copy_to": [
            "search_other"
          ]
        },
        "identifier": {
          "type": "nested",
          "properties": {
            "value": {
              "type": "text",
              "copy_to": [
                "search_other"
              ]
            },
            "identifierType": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_attr"
              ]
            }
          }
        },
        "identifierRegistration": {
          "type": "nested",
          "properties": {
            "value": {
              "type": "text",
              "copy_to": [
                "search_other"
              ]
            },
            "identifierType": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_attr"
              ]
            }
          }
        },
        "relation": {
          "type": "object",
          "properties": {
            "relatedIdentifier": {
              "type": "nested",
              "properties": {
                "value": {
                  "type": "text",
                  "copy_to": [
                    "search_other"
                  ]
                },
                "identifierType": {
                  "type": "keyword",
                  "index": true,
                  "copy_to": [
                    "search_attr"
                  ]
                }
              }
            },
            "relatedTitle": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            },
            "relationType": {
              "type": "nested",
              "properties": {
                "value": {
                  "type": "text",
                  "index": true
                },
                "item_links": {
                  "type": "keyword",
                  "index": true
                },
                "item_title": {
                  "type": "keyword",
                  "index": true
                }
              }
            }
          }
        },
        "temporal": {
          "type": "text",
          "copy_to": [
            "search_other"
          ]
        },
        "geoLocation": {
          "type": "object",
          "properties": {
            "geoLocationPoint": {
              "type": "object",
              "properties": {
                "pointLongitude": {
                  "type": "geo_point"
                },
                "pointLatitude": {
                  "type": "geo_point"
                }
              }
            },
            "geoLocationBox": {
              "type": "object",
              "properties": {
                "westBoundLongitude": {
                  "type": "geo_point"
                },
                "eastBoundLongitude": {
                  "type": "geo_point"
                },
                "southBoundLatitude": {
                  "type": "geo_point"
                },
                "northBoundLatitude": {
                  "type": "geo_point"
                }
              }
            },
            "geoLocationPlace": {
              "type": "text",
              "copy_to": [
                "search_other"
              ]
            }
          }
        },
        "fundingReference": {
          "type": "object",
          "properties": {
            "funderIdentifier": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_identifier"
              ]
            },
            "funderName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            },
            "awardNumber": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            },
            "awardTitle": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            }
          }
        },
        "sourceIdentifier": {
          "type": "nested",
          "properties": {
            "value": {
              "type": "text",
              "copy_to": [
                "search_other"
              ]
            },
            "identifierType": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_attr"
              ]
            }
          }
        },
        "sourceTitle": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          },
          "copy_to": [
            "search_other"
          ]
        },
        "volume": {
          "type": "text",
          "index": true,
          "copy_to": [
            "search_other"
          ]
        },
        "issue": {
          "type": "text",
          "index": true,
          "copy_to": [
            "search_other"
          ]
        },
        "numPages": {
          "type": "text"
        },
        "pageStart": {
          "type": "text"
        },
        "pageEnd": {
          "type": "text"
        },
        "dissertationNumber": {
          "type": "text",
          "copy_to": [
            "search_other"
          ]
        },
        "degreeName": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          },
          "copy_to": [
            "search_other"
          ]
        },
        "dateGranted": {
          "type": "date",
          "format": "yyyy-MM-dd||yyyy-MM||yyyy"
        },
        "degreeGrantor": {
          "type": "object",
          "properties": {
            "nameIdentifier": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_identifier"
              ]
            },
            "degreeGrantorName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other",
                "dgName"
              ]
            }
          }
        },
        "conference": {
          "type": "object",
          "properties": {
            "conferenceName": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            },
            "conferenceSequence": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            },
            "conferencePlace": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            },
            "conferenceCountry": {
              "type": "keyword",
              "index": true,
              "copy_to": [
                "search_other"
              ]
            }
          }
        },
        "file": {
          "type": "object",
          "properties": {
            "URI": {
              "type": "nested",
              "properties": {
                "value": {
                  "type": "text"
                },
                "objectType": {
                  "type": "keyword",
                  "index": true
                }
              }
            },
            "mimeType": {
              "type": "keyword",
              "index": true
            },
            "extent": {
              "type": "keyword",
              "index": true
            },
            "date": {
              "type": "nested",
              "properties": {
                "dateType": {
                  "type": "keyword",
                  "index": true
                },
                "value": {
                  "type": "date",
                  "format": "yyyy-MM-dd||yyyy-MM||yyyy"
                }
              }
            },
            "version": {
              "type": "text"
            }
          }
        },
        "content": {
          "type": "nested",
          "properties": {
            "file_id": {
              "type": "keyword",
              "index": true
            },
            "groups": {
              "type": "keyword",
              "index": true
            },
            "file_name": {
              "type": "text",
              "fields": {
                "ja": {
                  "type": "text"
                }
              }
            },
            "display_name": {
              "type": "text",
              "fields": {
                "ja": {
                  "type": "text"
                }
              }
            },
            "license_notation": {
              "type": "text"
            },
            "file": {
              "type": "text",
              "term_vector": "with_positions_offsets",
              "store": true,
              "fields": {
                "ja": {
                  "type": "text",
                  "term_vector": "with_positions_offsets",
                  "store": true
                }
              }
            },
            "attachment": {
              "properties": {
                "content": {
                  "type": "text",
                  "term_vector": "with_positions_offsets",
                  "store": true,
                  "fields": {
                    "ja": {
                      "type": "text",
                      "term_vector": "with_positions_offsets",
                      "store": true
                    }
                  }
                }
              }
            }
          }
        },
        "weko_creator_id": {
          "type": "text",
          "fielddata": true,
          "index": true
        },
        "weko_id": {
          "type": "text",
          "fielddata": true,
          "index": true
        },
        "search_title": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        },
        "search_creator": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        },
        "search_contributor": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        },
        "search_other": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        },
        "search_identifier": {
          "type": "text"
        },
        "search_attr": {
          "type": "text"
        },
        "search_string": {
          "type": "text"
        },
        "search_publisher": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        },
        "search_des": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        },
        "dgName": {
          "type": "text",
          "fields": {
            "ja": {
              "type": "text"
            }
          }
        }
      },
      "dynamic_templates": [
        {
          "other_text": {
            "match_mapping_type": "string",
            "match_pattern": "regex",
            "match": ".*?",
            "unmatch": "^((subitem|item)_\\d+)|weko_id|attribute_value$$",
            "mapping": {
              "type": "text",
              "index": false
            }
          }
        },
        {
          "weko_id": {
            "match_mapping_type": "string",
            "match_pattern": "regex",
            "match": "^weko_id$",
            "mapping": {
              "type": "text",
              "fielddata": true,
              "index": false,
              "copy_to": "weko_id"
            }
          }
        },
        {
          "string": {
            "match_mapping_type": "string",
            "match_pattern": "regex",
            "match": "^((subitem|item)_\\d+)|attribute_value$",
            "mapping": {
              "type": "text",
              "index": false,
              "copy_to": "search_string"
            }
          }
        },
        {
          "date": {
            "match_mapping_type": "date",
            "match_pattern": "regex",
            "match": "^(subitem|item)_\\d+$",
            "mapping": {
              "type": "date",
              "index": false,
              "copy_to": "date_search"
            }
          }
        },
        {
          "boolean": {
            "match_mapping_type": "boolean",
            "mapping": {
              "type": "boolean",
              "index": true
            }
          }
        },
        {
          "object": {
            "match_mapping_type": "object",
            "mapping": {
              "type": "object",
              "index": false
            }
          }
        }
      ]
    }
  }
}
'



curl -XPOST 'http://elasticsearch:9200/_reindex' -H 'Content-Type: application/json' -d '
{
  "source": {
    "index": "tenant1-weko-item-v1.0.0"
  },
  "dest": {
    "index": "tenant2-weko-item-v1.0.0"
  }
}
'

curl -XPOST 'http://elasticsearch:9200/_aliases' -H 'Content-Type: application/json' -d '
{
    "actions": [
        {"remove": {
            "alias": "tenant1-weko",
            "index": "tenant1-weko-item-v1.0.0"
        }},
        {"add": {
            "alias": "tenant1-weko",
            "index": "tenant2-weko-item-v1.0.0"
        }}
    ]
}
'

curl -XDELETE 'http://elasticsearch:9200/tenant1-weko-item-v1.0.0' -H


}