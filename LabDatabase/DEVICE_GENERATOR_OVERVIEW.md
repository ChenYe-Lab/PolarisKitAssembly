# Device Generator Overview

This document describes the files related to the `Device Generator` feature in `LabDatabase`, and explains how they work together.

## Feature Purpose

`Device Generator` provides a frontend tool for:

- selecting a chassis
- searching a CDS/gene
- providing expression-strength inputs
- recommending a promoter/RBS/terminator/backbone combination
- creating a temporary repository
- launching the downstream Golden Gate assembly workflow

## Main Request Flow

1. User opens `/LabDatabase/design-builder`
2. Django renders the design tool page
3. Frontend calls gene search and submit APIs
4. Backend computes a design recommendation
5. Backend creates a temporary repository
6. Backend starts an async assembly task
7. Frontend polls task status and displays the result

## Related Files

### 1. [WebDataWorld/LabDatabase/urls.py](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/urls.py:1)

Role:
- Defines the HTTP routes for the Device Generator feature

Key routes:
- `path("design-builder", views.design_builder, ...)`
- `path("design-builder/gene-search", views.design_gene_search, ...)`
- `path("design-builder/submit", views.submit_design_assembly, ...)`
- `path("task_status/<str:task_id>", views.task_status, ...)`
- `path("ShowRepository/<str:repositoryName>", views.showRepository, ...)`

Relationship:
- This file is the public entry point that connects browser requests to backend view functions.

### 2. [WebDataWorld/LabDatabase/views.py](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/views.py:252)

Role:
- Acts as the controller layer for Device Generator
- Receives requests from the frontend
- Calls the design engine
- Starts assembly tasks
- Collects repository data and generates assembly input files

Key functions:
- `design_builder`
  - Renders the Device Generator page
- `design_gene_search`
  - Returns CDS search candidates as JSON
- `submit_design_assembly`
  - Accepts design input, computes a recommendation, creates a repository, and starts async assembly
- `process_assembly_repo`
  - Reads repository contents and prepares sequence files for assembly
- `process_assembly_without_repo`
  - Similar assembly logic for direct lists instead of repository-based assembly

Important responsibilities:
- normalizes generated assembly file names
- builds `file_address_list` and `file_name_list`
- passes assembly input into the Golden Gate execution layer

Relationship:
- `views.py` is the central coordinator between frontend, recommendation logic, repository creation, file generation, and assembly execution.

### 3. [WebDataWorld/LabDatabase/design_engine.py](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/design_engine.py:1)

Role:
- Contains the recommendation logic for Device Generator

Key functions:
- `get_design_form_context`
  - Provides chassis options and preset values for page rendering
- `search_gene_candidates`
  - Searches `Parttable` for CDS candidates
- `recommend_design`
  - Builds the recommended design from chassis, gene, and strength inputs
- `create_design_repository`
  - Creates the temporary repository used for downstream assembly

Important behavior:
- selects promoter/RBS/terminator candidates from `Parttable`
- selects the backbone according to chassis rules
- computes or resolves expression-strength values
- creates a temporary repository record with selected parts/backbone

Relationship:
- `views.py` delegates all design recommendation logic to this file.

### 4. [WebDataWorld/LabDatabase/templates/design_builder.html](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/templates/design_builder.html:1)

Role:
- HTML template for the Device Generator page

Contains:
- top navigation
- sidebar tabs
- expression design form
- result summary panel
- repository visualization panel
- logic-gate placeholder panel

Relationship:
- Rendered by `views.design_builder`
- Uses data returned by `design_engine.get_design_form_context`
- Loads the page behavior from `design_builder.js`

### 5. [WebDataWorld/LabDatabase/static/LabDatabase/js/design_builder.js](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/static/LabDatabase/js/design_builder.js:1)

Role:
- Frontend behavior for the Device Generator page

Main responsibilities:
- handle tab switching
- search CDS/gene candidates
- preview formula/strength calculations
- submit the design form
- render selected parts and backbone
- poll assembly task status
- show repository visualization

Key API calls:
- `GET /LabDatabase/design-builder/gene-search`
- `POST /LabDatabase/design-builder/submit`
- `GET /LabDatabase/task_status/<task_id>`

Relationship:
- This file is the browser-side companion to `views.py`.

### 6. [WebDataWorld/LabDatabase/GGModule/SupportGG.py](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/GGModule/SupportGG.py:1)

Role:
- Wraps the `dnacauldron` Golden Gate assembly workflow

Key methods:
- `assemblyPart`
  - Imports sequence records into a `SequenceRepository`
  - Builds a `Type2sRestrictionAssembly`
  - Simulates the assembly
- `show`
  - Writes the assembly report

Important behavior:
- imports generated `.gbk` files
- uses the file names as record IDs for assembly matching

Relationship:
- Called from assembly execution logic in `views.py`
- This is the execution layer after all design inputs have already been prepared

### 7. [WebDataWorld/LabDatabase/CaculateModule/FileGenerator.py](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/CaculateModule/FileGenerator.py:1)

Role:
- Generates GenBank (`.gbk`) files for parts, backbones, and plasmids

Key methods used in the Device Generator/assembly chain:
- `SequenceAnnotator.GeneratorPartNoSa`
- `SequenceAnnotator.GeneratorBackboneNoSa`
- `SequenceAnnotator.GenerateGBKFile`

Relationship:
- Called by `views.py` when assembly input files need to be created
- Produces the actual files later imported by `SupportGG.py`

### 8. [WebDataWorld/LabDatabase/templates/index.html](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/templates/index.html:170)

Role:
- Contains the navigation links that expose Device Generator to users

Relevant links:
- `/LabDatabase/design-builder`

Relationship:
- This page is not part of the execution chain, but it is one of the UI entry points to the feature.

### 9. [WebDataWorld/LabDatabase/CaculateModule/DNADiagram.py](/c:/Users/admin/Desktop/WebDatabase/WebDataWorld/LabDatabase/CaculateModule/DNADiagram.py:733)

Role:
- Generates repository plasmid/construct visualization for repository-level output

Relationship:
- Not part of the core recommendation step
- Related to the repository result visualization layer after assembly/repository creation

## Data/Control Relationship Summary

### Frontend Layer

- `templates/design_builder.html`
- `static/LabDatabase/js/design_builder.js`

Purpose:
- collect user input
- call backend APIs
- display design and assembly results

### Backend Controller Layer

- `views.py`
- `urls.py`

Purpose:
- expose APIs
- route requests
- coordinate recommendation and assembly

### Design Logic Layer

- `design_engine.py`

Purpose:
- choose parts/backbone
- compute strength values
- create the temporary design repository

### File Generation Layer

- `CaculateModule/FileGenerator.py`

Purpose:
- turn selected repository items into `.gbk` files

### Assembly Execution Layer

- `GGModule/SupportGG.py`

Purpose:
- import generated records
- simulate Golden Gate assembly
- produce reports

## Simplified Dependency Graph

```text
index.html
   -> /LabDatabase/design-builder

urls.py
   -> views.design_builder
   -> views.design_gene_search
   -> views.submit_design_assembly

views.design_builder
   -> design_engine.get_design_form_context
   -> render design_builder.html

design_builder.js
   -> design_gene_search
   -> submit_design_assembly
   -> task_status

views.submit_design_assembly
   -> design_engine.recommend_design
   -> design_engine.create_design_repository
   -> process_assembly_repo

process_assembly_repo
   -> FileGenerator / SequenceAnnotator
   -> SupportGG.SupportGG

SupportGG
   -> dnacauldron assembly simulation
```

## Maintenance Notes

- If the design form changes, update both:
  - `design_builder.html`
  - `design_builder.js`

- If recommendation rules change, update:
  - `design_engine.py`

- If generated file names or assembly inputs change, check:
  - `views.py`
  - `FileGenerator.py`
  - `SupportGG.py`

- If task execution or assembly matching fails, the most relevant files are:
  - `views.py`
  - `SupportGG.py`
  - `FileGenerator.py`
