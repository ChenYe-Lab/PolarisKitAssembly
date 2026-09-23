# Assembly annotations and persistence

The assembly path follows the feature-record conversion used by
`Desktop/WebDatabase/WebDataWorld`: database rows become Biopython records,
annotated input files are generated for each task, DNA Cauldron assembles them,
and the resulting annotations are serialized back to the database.

## Annotation rules

- Plasmid inputs retain their internal features and receive a whole-input source
  annotation. In a result, the whole-input label covers the retained plasmid
  contribution, not the discarded restriction fragment.
- Backbone inputs retain biological features only. Engine-generated whole-backbone
  labels and explicit source-container annotations are removed. Real features
  spanning the backbone are retained.
- Part features are shifted by the actual sequence prefix added for assembly.
  If processing no longer contains the original sequence, assembly fails rather
  than silently assigning guessed coordinates.
- Each task writes fresh files under its own `inputs/` directory. Source names
  are not used to decide whether to reuse old annotations.
- Database positions are 1-based closed intervals. Biopython positions are
  0-based half-open intervals. Compound locations are stored as ordered segments
  with a shared `feature_group`; strand, qualifiers and colors are retained.
- Opposite-strand annotations and whole-plasmid containers are not collapsed
  into coextensive internal features.

`assembly_inputs.py` reads source records from the same WebDataBase Django
database used by the `WebDatabase` app. KitAssembly continues to access the
backend through its existing APIs.

## Saving the result

`WebDatabase.assembly_results.save_assembly_result()` commits the sequence,
feature rows, Level, immediate Part/Backbone/Plasmid parent edges, culture fields
and scar information in one transaction. A failure rolls back the complete
update. Task completion is published only after this operation succeeds.

LabDatabase calls this service directly. The authenticated POST endpoint
`/WebDatabase/SaveAssemblyResult` exposes the same operation to API clients.
The payload uses `name`, `sequence`, `assembly_features`, `parts`, `backbones`,
`plasmids`, and optional `level`, `alias`, `note`, `culture`, `scars`. Parent
collections contain database IDs. Feature rows follow `feature_rows()` in
`feature_records.py` and include `coordinate_system=one_based_closed`.

When Level is omitted, direct Part inputs produce Level 1; plasmid parents
produce `max(parent.level) + 1`. The supported result levels are 1–3. Explicit
levels must be higher than every plasmid parent's level. Self-parenting and
ancestry cycles are rejected. Existing immediate parent edges are replaced,
while ancestor records retain their own edges, preserving the full hierarchy.

Map download endpoints reconstruct records from stored rows rather than rerun
sequence matching. Subsequent assembly therefore reads the annotations saved
for the previous result.

## Database upgrade

Run from `WebDataBase` with its environment active, after backing up the database:

```powershell
python manage.py migrate WebDatabase
```

Migration `0004_assembly_feature_metadata` registers the three legacy feature
tables in migration state. It creates missing feature tables, or adds missing
metadata columns to existing tables without deleting their rows. It is
intentionally irreversible through Django: do not use a backwards migration
to remove annotation data. Use a database backup for deployment rollback.

The migration does not reconstruct historical strand information that was
never stored. Reimport an original annotated map if an old row lacks this
information. It also does not repair unrelated differences between the
repository's older migrations and an existing deployment's database schema.

Both the code and database metadata migration are required before assembling
or downloading maps with the new code. Restart the backend after deployment.
No migration against an existing user database was performed during this change.

## Verification

The focused test suite uses an isolated in-memory SQLite database and a real
DNA Cauldron simulation; it does not access the configured MySQL database.

```powershell
python -m unittest LabDatabase.tests.test_assembly_annotations -v
```

Coverage includes reverse-strand compound-location round trips, actual assembly
annotation rules, prefix offsets, refreshed inputs, Level 1/2/3 parent edges,
repeated saves, invalid coordinates, cycle rejection, transaction rollback and
adoption of an existing feature table. Existing MySQL deployment and browser
end-to-end validation remain separate deployment checks.
