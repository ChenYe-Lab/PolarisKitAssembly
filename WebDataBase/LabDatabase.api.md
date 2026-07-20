# Lab DNA Data page API

## Base URL
- http://10.30.76.2:8000/LabDatabase

## Overview
- Title: Lab DNA Data page
- Version: 1.0.0
- Description: This is a API module for database search page.

## Endpoints
### Untagged

#### [GET] /index
Summary: show main web page

#### [GET] /getdata
Summary: List one page value of type with page value ( use webdatabase api Part/Backbone/Plasmid )
OperationId: getData
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| type | query | true | data type (part\backbone\plasmid) |
| page | query | true | page number (default 1) |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get data list |
| 400 | search error |

#### [POST] /filterdata
Summary: search data by filter info (use webdatabase api PartFilter)
OperationId: DataFilter
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartSimple'
- Schema: '#/components/schemas/BackboneSimple'
- Schema: '#/components/schemas/PlasmidSimple'
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Part Data list |
| 200/1 | Get Backbone Data list |
| 200/2 | Get Backbone Data list |
| 400 | search error |

#### [GET] /UploadPartMap

#### [GET] /UploadBackboneMap

#### [GET] /UploadPlasmidMap

#### [GET] /UploadFile
Summary: get upload excel file and analysis file
OperationId: UploadFile
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| file | - | true | - |
Responses:
| Code | Description |
| --- | --- |
| 200 | upload data successfully |
| 400 | upload data failly |

#### [GET] /part/<int:partid>
Summary: show part detail information page (use webdatabase api PartByID)
OperationId: part_detail_show
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| partid | head | true | part id |

#### [GET] /backbone/<int:backboneid>
Summary: show backbone detail information page (use webdatabase api BackboneByID)
OperationId: backbone_detail_show
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| backboneid | head | true | backbone id |

#### [GET] /plasmid/<int:plasmidid>
Summary: show backbone detail information page (use webdatabase api PlasmidByID,GetPartParent,GetBackboneParent,GetPlasmidParent,GetPlasmidSon)
OperationId: plasmid_detail_show
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| partid | head | true | part id |

#### [GET] /download/<str:type>
Summary: download the data template file
OperationId: download_template

