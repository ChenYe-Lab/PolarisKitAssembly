# Lab DNA Database API

## Base URL
- http://10.30.76.2:8000/WebDatabase

## Overview
- Title: Lab DNA Database
- Version: 1.0.0
- Description: This is a API module for use LabDnaData Database. Module includes Part, Backbone, Plasmid,

## Endpoints
### Strain

#### [GET] /StrainName
Summary: Search Strain By Name.
Description: List strain information by name provided by user.
OperationId: StrainName
Tags: Strain
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | The Name to Search |
Responses:
| Code | Description |
| --- | --- |
| 200 | The Strain Information with query name |
| 400 | No Name Search |
| 404 | No such strain |

### Part

#### [GET] /Part
Summary: List all parts
Description: List all parts.
OperationId: part
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| page | query | false | if page is null, return all data, else return offset:offset+pagesize data |
| page_size | query | false | size of page when page is not null |
Responses:
| Code | Description |
| --- | --- |
| 200 | List All Parts (no page data) |
| 200/1 | Get one page parts (with page data) |
| 404 | No part data |

#### [GET] /PartByID
Summary: List parts data by ID
Description: List parts by provided ID
OperationId: PartByID
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| ID | query | true | The ID used to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Part Data list |
| 400 | parameter is empty |
| 404 | No such part |

#### [GET] /PartName
Summary: List parts data by name
Description: List parts by provided name
OperationId: PartName
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | The Name used to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Part Data list |
| 400 | parameter is empty |
| 404 | No such part |

#### [GET] /PartAlias
Summary: List parts data by alias
Description: List parts by provided alias
OperationId: PartAlias
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| AlterName | query | true | The Alter Name used to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get part data list |
| 400 | parameter is empty |
| 404 | No Such part |

#### [GET] /PartType
Summary: List parts data by type
Description: List parts data by provided type
OperationId: PartType
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| 'type' | query | true | The type used to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get part data list |
| 400 | parameter is empty |
| 404 | No Such part |

#### [GET] /TypeByName
Summary: Search Part Type by name
Description: Search Part Type by provided name, return Promoter\CDS\Terminator\RBS\Carb
OperationId: TypeByName
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | The name used to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return Part's type |
| 400 | parameter is empty |
| 404 | No such part of name |

#### [GET] /PartRPU
Summary: List part data which rpu like provided value
Description: search part which rpu in range [floor(RPU), ceil(RPU)]
OperationId: PartRPU
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| rpu | query | true | rpu value |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return Part Data |
| 400 | RPU value is empty |
| 404 | No such part |

#### [GET] /PartSeq
Summary: List part data by sequence
Description: Search part which sequence like provided sequence
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| seq | query | true | DNA Sequence |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return Part Data |
| 400 | Provided sequence value is empty |
| 404 | No such part |

#### [GET] /PartFile
Summary: Search part sequence map file address by name
Description: Search file address
OperationId: PartFile
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | part name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return Part sequence file address |
| 400 | parameter name is empty |
| 404 | No such part or User don't have part file address |

#### [GET] /PartID
Summary: Get Part ID by name
OperationId: PartID
Tags: Part

#### [POST] /AddPartRPU
Summary: Append part rpu data in database
Description: Add part rpu data
OperationId: AddPartRPU
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartRPU'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added part rpu |
| 400 | parameter name is empty |
| 404 | No such part |

#### [POST] /AddPartData
Summary: Add Part Data
Description: insert part data into database
OperationId: AddPartData
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/partWithoutID'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added part data |
| 400 | Required parameter |

#### [POST] /AddPartFile
Summary: Add Part sequence file address
Description: Add Part sequence file address into database
OperationId: AddPartFile
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartFile'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added Part File address |
| 404 | No such part |

#### [POST] /UpdatePart
Summary: update part data
Description: update part data by information provided
OperationId: UpdatePart
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartWithOriginName'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated part data |
| 404 | No such part |

#### [POST] /UpdatePartRPU
Summary: Update part rpu data
Description: Update part rpu data by value provided
OperationId: UpdatePartRPU
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartRPU'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated part rpu |
| 400 | Parameter Name, test strain, rpu cannot be empty |
| 404 | No such part rpu |

#### [POST] /UpdatePartFile
Summary: Update part file address information
Description: Update part file address of name provided
OperationId: UpdatePartFile
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartFile'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated part file address |
| 400 | Name, Address cannot be empty |
| 404 | No such part |

#### [GET] /deletePart
Summary: delete part from database
Description: delete part of name provided
OperationId: deletePart
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | name of part which to be delete |
Responses:
| Code | Description |
| --- | --- |
| 200 | deleted part |
| 400 | Name cannot be empty |
| 404 | No such part |

#### [GET] /deletePartFile
Summary: delete part file address
Description: delete part file address of name provided
OperationId: deletePartFile
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | name of part which address to be delete |
Responses:
| Code | Description |
| --- | --- |
| 200 | Delete Part File Address |
| 400 | Name cannot be empty |
| 404 | No such part |

#### [POST] /PartFilter
Summary: search part by multiple info
Description: search part by multiple info
OperationId: PartFilter
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PartSimple'
Responses:
| Code | Description |
| --- | --- |
| 200 | return part value |
| 400 | Name cannot be empty |

#### [GET] /PartNameFilter
Summary: get simple part information by part name
Description: get simple part information which name like provided name
OperationId: PartNameFilter
Tags: Part
Responses:
| Code | Description |
| --- | --- |
| 200 | Get part List |
| 400 | Parameter name is empty |
| 404 | catch exceptions |

#### [GET] /getPartValueList<str:column>
Summary: get each type value of provided part column name
Description: get each type value of provided part column name
OperationId: getPartValueList
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| column name | path | true | part column name |
Responses:
| Code | Description |
| --- | --- |
| 200 | return part column value |
| 400 | column value is empty |

#### [GET] /getPartScarList
Summary: get all part scar type
Description: get all part scar type
OperationId: getPartScarList
Tags: Part
Responses:
| Code | Description |
| --- | --- |
| 200 | return part scar type |

#### [GET] /getPartScar
Summary: get scar information of provided part
Description: get scar information of provided part
OperationId: getPartScar
Tags: Part
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | part name |
Responses:
| Code | Description |
| --- | --- |
| 200 | return part scar information |
| 400 | No such scar information |

#### [POST] /setPartScar
Summary: set part scar information
Description: set part scar information
OperationId: setPartScar
Tags: Part
Request Body:
- Content-Type: application/json
- Schema: inline
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully add part scar information |
| 400 | Parameters name cannot be empty |
| 404 | No such part |

### Untagged

#### [GET] /SearchRPU

#### [POST] /login
Summary: login UI

#### [POST] /logout
Summary: logout function

#### [POST] /register
Summary: show register ui

### Plasmid

#### [GET] /PlasmidName
Summary: List plasmid data by name
Description: search plasmid data by name provided
OperationId: PlasmidName
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | plasmid name to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | List plasmid data |
| 400 | Name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidByID
Summary: List plasmid data by ID
Description: search plasmid data by ID provided
OperationId: PlasmidByID
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| ID | query | true | plasmid ID to search |
Responses:
| Code | Description |
| --- | --- |
| 200 | List plasmid data |
| 400 | Name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidAlterName
Summary: List Plasmid data by alias
Description: Search Plasmid data by alias provided
OperationId: PlasmidAlterName
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| altername | query | true | Plasmid Alias |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of Alias |
| 400 | Alias cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidSeq
Summary: List Plasmid data by sequence
Description: Search plasmid data by sequence provided
OperationId: PlasmidSeq
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| seq | query | true | plasmid sequence |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of Alias |
| 400 | Alias cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidSeqByName
Summary: Get plasmid sequence by name
Description: Search Plasmid sequence by name provided
OperationId: PlasmidSeqByName
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return plasmid sequence |
| 400 | name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidOriClone
Summary: List plasmid data by origin (clone)
Description: Search plasmid data by plasmid origin(clone) name
OperationId: PlasmidOriClone
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| oriClone | query | true | origin name |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of origin(clone) name |
| 400 | Origin name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidOriHost
Summary: List plasmid data by origin (host)
Description: Search plasmid data by plasmid origin(host) name
OperationId: PlasmidOriHost
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| oriHost | query | true | origin name |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of origin(host) name |
| 400 | Origin name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidMarkerClone
Summary: List plasmid data by marker (clone)
Description: Search plasmid data by plasmid marker (clone) name
OperationId: PlasmidMarkerClone
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| MarkerClone | query | true | marker name |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of marker (clone) name |
| 400 | marker name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidMarkerHost
Summary: List plasmid data by marker (host)
Description: Search plasmid data by plasmid marker (host) name
OperationId: PlasmidMarkerHost
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| markerHost | query | true | marker name |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of marker (host) name |
| 400 | Marker name cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidLevel
Summary: List plasmid data by level
Description: Search plasmid data by level provided
OperationId: PlasmidLevel
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| level | query | true | plasmid level |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return plasmid data |
| 400 | Level cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidPlate
Summary: List plasmid data by plate information
Description: Search plasmid data by plate provided
OperationId: PlasmidPlate
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plate | query | true | plasmid plate |
Responses:
| Code | Description |
| --- | --- |
| 200 | List Plasmid Data of plate information |
| 400 | Plate cannot be empty |
| 404 | No such plasmid |

#### [GET] /PlasmidParent
Summary: List Parent plasmid name
Description: Search Parent plasmid name of plasmid name provided
OperationId: PlasmidParent
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidName | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return parent plasmid name of plasmid provided |
| 400 | PlasmidName cannot be empty |
| 404 | No such Plasmid/Parent plasmid |

#### [GET] /PlasmidParentByID
Summary: List Parent plasmid name by Plasmid ID
Description: Search Parent plasmid name of plasmid id provided
OperationId: PlasmidParentByID
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidID | query | true | plasmid id |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return parent plasmid name of plasmid provided |
| 400 | PlasmidID cannot be empty |
| 404 | No such Plasmid/Parent plasmid |

#### [GET] /GetParentID
Summary: List Parent plasmid IDs by Plasmid ID
Description: Search Parent plasmid IDs of plasmid id provided
OperationId: GetParentID
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidID | query | true | plasmid id |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return parent plasmid IDs of plasmid provided |
| 400 | PlasmidID cannot be empty |
| 404 | No such Plasmid/Parent plasmid |

#### [GET] /PlasmidID
Summary: Get Plasmid ID by name
OperationId: PlasmidID
Tags: Plasmid

#### [GET] /PlasmidFile
Summary: Get Plasmid file address
Description: Get Plasmid file address by name and user name
OperationId: PlasmidFile
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return plasmid file address |
| 400 | Name cannot be empty |
| 404 | No such plasmid/ No such file address |

#### [POST] /AddPlasmidFile
Summary: Add plasmid file address
Description: Add plasmid file address in database
OperationId: AddPlasmidFile
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PlasmidFile'
Responses:
| Code | Description |
| --- | --- |
| 200 | Add Plasmid Address |
| 400 | Name cannot be empty |
| 404 | No such Plasmid |

#### [POST] /AdddPlasmidData
Summary: Add plasmid data
Description: Add plasmid data in database
OperationId: AddPlasmidData
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PlasmidWithoutID'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added Plasmid Data |
| 400 | Name, Level, sequence, origin, marker cannot be empty |

#### [POST] /AddPlasmidParent
Summary: Add plasmid parent information
Description: Add plasmid parent information into database
OperationId: AddPlasmidParent
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PlasmidParent'
Responses:
| Code | Description |
| --- | --- |
| 200 | Parent plasmid Added |
| 400 | Son Plasmid Name/ Parent Plasmid Name cannot be empty |
| 404 | No such son plasmid/ parent plasmid |

#### [POST] /UpdatePlasmid
Summary: update plasmid data
Description: update plasmid data by origin plasmid name
OperationId: UpdatePlasmid
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/plasmidWithOriginName'
Responses:
| Code | Description |
| --- | --- |
| 200 | Plasmid data updated |
| 400 | Required Parameter is empty |
| 404 | No such origin plasmid |

#### [POST] /UpdatePlasmidFile
Summary: update plasmid file address
Description: update plasmid file address of name and user name
OperationId: UpdatePlasmidFile
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/PlasmidFile'
Responses:
| Code | Description |
| --- | --- |
| 200 | Plasmid file address updated |
| 400 | Parametes cannot be empty |
| 404 | Np such plasmid |

#### [GET] /deletePlasmid
Summary: delete plasmid data
Description: delete plasmid data by name
OperationId: deletePlasmid
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | plasmid data deleted |
| 400 | Name cannot be empty |
| 404 | No such Plasmid |

#### [GET] /deletePlasmidFile
Summary: delete plasmid file address
Description: delete plasmid file address of name
OperationId: deletePlasmidFile
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| PlasmidName | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Plasmid file address deleted |
| 400 | Parameter cannot be empty |
| 404 | No such plasmid |

#### [GET] /deletePlasmidParent
Summary: delete parent plasmid data
Description: delete parent plasmid of plasmid name provided
OperationId: deletePlasmidParent
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidName | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Parent plasmid deleted |
| 400 | Parent Plasmid name cannot be empty |
| 404 | No such parent plasmid |

#### [GET] /PlasmidNameFilter
Summary: get simple Plasmid information by plasmid name
Description: get simple plasmid information which name like provided name
OperationId: PlasmidNameFilter
Tags: Plasmid
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Plasmid List |
| 400 | Parameter name is empty |
| 404 | catch exceptions |

#### [POST] /AddPartParent
Summary: Add Plasmid parent part information
Description: Add Plasmid parent part information
OperationId: AddPartParent
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully add parent part information |
| 400 | Parameters name cannot be empty |
| 404 | No such plasmid or parent part |

#### [POST] /AddBackboneParent
Summary: Add Plasmid parent part information
Description: Add Plasmid parent part information
OperationId: AddPartParent
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully add parent part information |
| 400 | Parameters name cannot be empty |
| 404 | No such plasmid or parent part |

#### [GET] /GetPartParent
Summary: get plasmid part information
Description: get plasmid's part information
OperationId: GetParentPart
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidid | query | true | plasmid id |
Responses:
| Code | Description |
| --- | --- |
| 200 | return parent part list |

#### [GET] /GetBackboneParent
Summary: get plasmid backbone information
Description: get plasmid's backbone information
OperationId: GetParentBackbone
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidid | query | true | plasmid id |
Responses:
| Code | Description |
| --- | --- |
| 200 | return parent backbone list |

#### [GET] /GetPlasmidParent
Summary: get plasmid's plasmid information
Description: get plasmid's parent plasmid information
OperationId: GetParentParent
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidid | query | true | plasmid id |
Responses:
| Code | Description |
| --- | --- |
| 200 | return parent plasmid list |

#### [GET] /GetPlasmidSon
Summary: get plasmid's son plasmid information
Description: get plasmid's son plasmid information
OperationId: GetSonPlasmid
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| plasmidid | query | true | plasmid id |
Responses:
| Code | Description |
| --- | --- |
| 200 | return son plasmid list |

#### [GET] /getPlasmidValueList/<str:column>
Summary: get each type value of provided plasmid column name
Description: get each type value of provided plasmid column name
OperationId: getPlasmidValueList
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| column name | path | true | plasmid column name |
Responses:
| Code | Description |
| --- | --- |
| 200 | return plasmid column value |
| 400 | column value is empty |

#### [GET] /getPlasmidScarList
Summary: get all plasmid scar type
Description: get all plasmid scar type
OperationId: getPlasmidScarList
Tags: Plasmid
Responses:
| Code | Description |
| --- | --- |
| 200 | return plasmid scar type |

#### [GET] /getPlasmidScar
Summary: get plasmid scar information
Description: get plasmid scar information
OperationId: getPlasmidScar
Tags: Plasmid
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | plasmid name |
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully get plasmid scar information |
| 400 | Parameters name cannot be empty\ No such scar information |

#### [POST] /setPlasmidScar
Summary: set plasmid scar information
Description: set plasmid scar information
OperationId: setPlasmidScar
Tags: Plasmid
Request Body:
- Content-Type: application/json
- Schema: inline
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully add plasmid scar information |
| 400 | Parameters name cannot be empty\just post request |
| 404 | No such plasmid |

### Backbone

#### [GET] /BackboneName
Summary: List backbone data
Description: Search backbone data by name provided
OperationId: BackboneName
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | Backbone Name |
Responses:
| Code | Description |
| --- | --- |
| 200 | return backbone data of name provided |
| 400 | Parameter name cannot be empty |
| 404 | No such name |

#### [GET] /BackboneByID
Summary: List backbone data
Description: Search backbone data by ID provided
OperationId: BackboneByID
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| ID | query | true | Backbone ID |
Responses:
| Code | Description |
| --- | --- |
| 200 | return backbone data of ID provided |
| 400 | Parameter name cannot be empty |
| 404 | No such name |

#### [GET] /BackboneSeq
Summary: List backbone data by sequence
Description: search backbone data by sequence provided
OperationId: BackboneSeq
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| seq | query | true | backbone sequence |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Backbone data by sequence |
| 400 | Parameter sequence cannot be empty |
| 404 | No such backbone |

#### [GET] /BackboneSpecies
Summary: List backbone data by species
Description: Search backbone data by species provided
OperationId: BackboneSpecies
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| species | query | true | Backbone species |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get backbone data by species |
| 400 | Parameter species cannot be empty |
| 404 | No such backbone |

#### [GET] /BackboneMarker
Summary: List Backbone data by marker
Description: Search backbone by marker name provided
OperationId: BackboneMarker
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| marker | query | true | marker name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Backbone data by marker |
| 400 | Parameter marker cannot be empty |
| 404 | No such backbone |

#### [GET] /BackboneOri
Summary: List Backbone data by Origin
Description: Search Backbone data by origin name provided
OperationId: BackboneOri
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| ori | query | true | Backbone origin |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Backbone data by origin |
| 400 | Parameter origin cannot be empty |
| 404 | No such backbone |

#### [GET] /BackboneCopyNumber
Summary: List Backbone data by copy number
Description: Search backbone by copy number provided
OperationId: BackboneCopyNumber
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| copynumber | query | true | Backbone Copy Number |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get backbone data list by copy number |
| 400 | Parameter copy number cannot be empty |
| 404 | No such backbone |

#### [GET] /BackboneFile
Summary: List Backbone file address by name and user
Description: Search Backbone file by backbone name provided
OperationId: BackboneFile
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | backbone name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get backbone file address of name provided and current user |
| 400 | Parameter name cannot be empty |
| 404 | No such Backbone |

#### [GET] /BackboneID
Summary: Get Backbone ID by name
OperationId: BackboneID
Tags: Backbone

#### [POST] /AddBackbone
Summary: Add backbone data
Description: Add backbone data into database
OperationId: AddBackbone
Tags: Backbone
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/BackboneWithoutId'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added backbone data |
| 400 | Parameter name, sequence cannot be empty |

#### [POST] /AddBackboneFile
Summary: Add backbone file address
Description: Add backbone file address to database
OperationId: AddBackboneFile
Tags: Backbone
Request Body:
- Schema: inline
- Schema: '#/components/schemas/BackboneFile'
- Content-Type: application/json
Responses:
| Code | Description |
| --- | --- |
| 200 | Added backbone file data |
| 400 | Parameter name and address cannot be empty |
| 404 | No such backbone |

#### [POST] /UpdateBackbone
Summary: Update backbone data
Description: update backbone data in database by original name provided
OperationId: UpdateBackbone
Tags: Backbone
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/BackboneWithOriName'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated backbone data |
| 400 | Parameters original name, new name, new sequence cannot be empty |
| 404 | No such backbone of original name |

#### [POST] /UpdateBackboneFile
Summary: Update backbone file address
Description: Update backbone file address of name provided and current user
OperationId: UpdateBackboneFile
Tags: Backbone
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/BackboneFile'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated Backbone file address |
| 400 | Parameters name, address cannot be empty |
| 404 | No such backbone of name |

#### [GET] /deleteBackbone
Summary: delete backbone data
Description: delete backbone data from database by name
OperationId: deleteBackbone
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | Backbone name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Deleted Backbone data |
| 400 | Parameter name cannot be empty |
| 404 | No such backbone |

#### [GET] /deleteBackboneFile
Summary: delete backbone file address
Description: delete backbone file address from database by name provided and current user
OperationId: deleteBackboneFile
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | Backbone name |
Responses:
| Code | Description |
| --- | --- |
| 200 | deleted backbone data |
| 400 | Parameter name cannot be empty |
| 404 | No such backbone |

#### [GET] /BackboneNameFilter
Summary: get simple backbone information by backbone name
Description: get simple Backbone information which name like provided name
OperationId: BackboneNameFilter
Tags: Backbone
Responses:
| Code | Description |
| --- | --- |
| 200 | Get Backbone List |
| 400 | Parameter name is empty |
| 404 | catch exceptions |

#### [GET] /getBackboneValueList/<str:column>
Summary: get each type value of provided backbone column name
Description: get each type value of provided backbone column name
OperationId: getBackboneValueList
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| column name | path | true | backbone column name |
Responses:
| Code | Description |
| --- | --- |
| 200 | return backbone column value |
| 400 | column value is empty |

#### [GET] /getBackboneScarList
Summary: get all backbone scar type
Description: get all backbone scar type
OperationId: getBackboneScarList
Tags: Backbone
Responses:
| Code | Description |
| --- | --- |
| 200 | return backbone scar type |

#### [GET] /getBackboneScar
Summary: get backbone scar information
Description: get backbone scar information
OperationId: getBackboneScar
Tags: Backbone
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | backbone name |
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully get backbone scar information |
| 400 | Parameters name cannot be empty\ No such scar information |
| 404 | No such part |

#### [POST] /setBackboneScar
Summary: set backbone scar information
Description: set backbone scar information
OperationId: setBackboneScar
Tags: Backbone
Request Body:
- Content-Type: application/json
- Schema: inline
Responses:
| Code | Description |
| --- | --- |
| 200 | successfully add backbone scar information |
| 400 | Parameters name cannot be empty\just post request |
| 404 | No such backbone |

### Test Data

#### [GET] /TestDataName
Summary: List test data
Description: Search test data information from database by name provided
OperationId: TestDataName
Tags: Test Data
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | test data name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Get test data |
| 400 | Parameters name cannot be empty |
| 404 | No such test data |

### DBD

#### [GET] /GetDBDList
Summary: List all DBD value
Description: List all DBD data
OperationId: GetDBDList
Tags: DBD
Responses:
| Code | Description |
| --- | --- |
| 200 | Return all DBD value |
| 404 | No DBD data |

#### [GET] /GetDBDNameList
Summary: return All DBD Name
Description: Get all DBD value
OperationId: GetDBDNameList
Tags: DBD
Responses:
| Code | Description |
| --- | --- |
| 200 | Return DBD name list |
| 404 | No DBD List |

#### [GET] /GetDBDKdList
Summary: List DBD Kd value
Description: Get all DBD kd value list
OperationId: GetDBDKdList
Tags: DBD
Responses:
| Code | Description |
| --- | --- |
| 200 | return kd value list |
| 404 | No DBD kd value |

#### [GET] /GetDBD
Summary: Get simple dbd value
Description: search dbd value by name provided
OperationId: GetDBD
Tags: DBD
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | DBD name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return DBD value list |
| 400 | Parameter name cannot be empty |
| 404 | No such DBD |

#### [GET] /GetDBDAllByName
Summary: Get complex dbd value
Description: search dbd all value by name provided
OperationId: GetDBDAllByName
Tags: DBD
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | DBD name |
Responses:
| Code | Description |
| --- | --- |
| 200 | Return DBD value list |
| 400 | Parameter name cannot be empty |
| 404 | No such DBD |

#### [GET] /GetDBDMenu
Summary: Get All DBD simple data
Description: return all dbd data
OperationId: GetDBDMenu
Tags: DBD
Responses:
| Code | Description |
| --- | --- |
| 200 | Get all DBD simple data |
| 404 | No DBD data |

#### [GET] /GetDBDKd
Summary: Return kd value of dbd
Description: Get kd value of dbd name provided
OperationId: GetDBDKd
Tags: DBD
Parameters:
| Name | In | Required | Description |
| --- | --- | --- | --- |
| name | query | true | DBD name |
Responses:
| Code | Description |
| --- | --- |
| 200 | return kd value of name |
| 400 | Parameter name cannot be empty |
| 404 | No such DBD |

#### [POST] /AddDBD
Summary: Add DBD value
Description: Add DBD value into database
OperationId: AddDBD
Tags: DBD
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/DBDSimpleWithoutId'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added DBD |
| 400 | Parameter Name,I0,Kd cannot be empty |

#### [POST] /UpdateDBD
Summary: Update DBD value
Description: Update DBD simple value
OperationId: UpdateDBD
Tags: DBD
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/DBDSimpleWithoutId'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated DBD |
| 400 | Parameter Name,I0,Kd cannot be empty |

### LBDDimer

#### [GET] /GetLBDDimer
Summary: Return LBD all data
Description: Get LBD all data
OperationId: GetLbdDimer
Tags: LBDDimer
Responses:
| Code | Description |
| --- | --- |
| 200 | Return Complex lbd dimer data |
| 404 | No LBD Dimer |

#### [GET] /GetLBDDimerMenu
Summary: Get Simple LBD Dimer value list
Description: List Simple LBD Dimer value
OperationId: GetLBDDimerMenu
Tags: LBDDimer
Responses:
| Code | Description |
| --- | --- |
| 200 | Return Simple LBD Dimer value list |
| 404 | No such LBD Dimer data |

#### [GET] /GetLBDDimerNameList
Summary: List all LBD Dimer name list
Description: Return all lbd dimer name
OperationId: GetLBDDimerNameList
Tags: LBDDimer
Responses:
| Code | Description |
| --- | --- |
| 200 | Get all lbd dimer name list |
| 404 | No such LBDDimer |

#### [GET] /GetLBDDimerAllByName
Summary: List LBD All value by name provided
Description: Return complex lbd dimer value
OperationId: GetLBDDimerAllByName
Tags: LBDDimer
Responses:
| Code | Description |
| --- | --- |
| 200 | Get all lbd dimer value by name |
| 400 | Parameter Name cannot be empty |
| 404 | No such LBDDimer |

#### [POST] /ADDLBDDimer
Summary: Add Simple LBD Dimer data
Description: Add simple lbd dimer data into database
OperationId: ADDLBDDimer
Tags: LBDDimer
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/LBDDimerSimple'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added LBDDimer |
| 400 | Parameter Name, K1,K2,K3,I cannot be empty |

#### [POST] /UpdateLbdDimer
Summary: Update Lbd Dimer data
Description: Update LBD Dimer data in database
OperationId: UpdateLbdDimer
Tags: LBDDimer
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/LBDDimerSimple'
Responses:
| Code | Description |
| --- | --- |
| 200 | Updated DBD |
| 400 | Parameter Name, k1,k2,k3,I cannot be empty |
| 404 | No such LBD Dimer |

### LBDNR

#### [GET] /GetLBDNr
Summary: List complex LBD NR data
Description: Return all LBD complex data
OperationId: GetLBDNr
Tags: LBDNR
Responses:
| Code | Description |
| --- | --- |
| 200 | Return LBD data list |
| 404 | No LBD NR Data |

#### [GET] /GetLBDNRMenu
Summary: List simple LBD NR data
Description: Get all simple LBD NR value list
OperationId: GetLBDNRMenu
Tags: LBDNR
Responses:
| Code | Description |
| --- | --- |
| 200 | Return LBD NR data |
| 404 | No LBD NR data |

#### [GET] /GetLBDNRAllByName
Summary: List complex LBD NR data by name provided
Description: Get complex LBD NR value by name
OperationId: GetLBDNRAllByName
Tags: LBDNR
Responses:
| Code | Description |
| --- | --- |
| 200 | Return LBD NR data |
| 400 | Parameter name cannot be empty |
| 404 | No LBD NR data |

#### [GET] /GetLBDNRNameList
Summary: Get all LBD NR Name
Description: Return all LBD NR Name List
OperationId: GetLBDNRNameList
Tags: LBDNR
Responses:
| Code | Description |
| --- | --- |
| 200 | Get All Name List |
| 404 | No LBD NR data |

#### [POST] /AddLbdnr
Summary: Add LBD NR data
Description: Add LBD NR data in database
OperationId: AddLbdnr
Tags: LBDNR
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/LBDNRSimple'
Responses:
| Code | Description |
| --- | --- |
| 200 | Added LBD NR |
| 400 | Parameters Name,k1,k2,k3,kx1,kx2 cannot be empty |

#### [POST] /UpdateLBDnr
Summary: Update LBD data
Description: Update LBD NR data
OperationId: UpdateLBDnr
Tags: LBDNR
Request Body:
- Content-Type: application/json
- Schema: inline
- Schema: '#/components/schemas/LBDNRSimple'
Responses:
| Code | Description |
| --- | --- |
| 200 | Update LBD NR |
| 400 | Parameters Name,k1,k2,k3,kx1,kx2 cannot be empty |

