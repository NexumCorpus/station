# Context sutures — exact memory without re-narration

A context suture is a passive, immutable packet of declared byte intervals.
Each interval carries its source path, offsets, whole-source hash, slice hash,
destination label, and base64 exact bytes. The packet therefore does not ask a
successor to trust a summary or reconstitute intent from prose: it carries the
selected bytes themselves.

`station suture seal` accepts a small manifest from standard input and permits
sources only inside a registered estate repository. The id is immutable; a
changed reading needs a new id. `station suture verify` checks stored payload
integrity first, then compares the donor's current whole file and byte interval.
`SUTURE-ROT` means preserved bytes are corrupt; `SUTURE-SOURCE-DRIFT` means the
historical payload is intact but must not be presented as current context.

This is deliberately weaker than a graft. A graft is an executable capability
claim tested in an empty body. A suture carries no command and grants no
execution authority; it is a lossless context opening. Nor is it whole-estate
preservation: the declared slices are useful because they are narrow, while Git,
the Continuity mirror, and Reed–Solomon shards retain the wider body.

The falsifier is simple: if a payload byte changes undetected, source roots can
escape the registered estate, an existing id can be silently rewritten, or donor
drift is rendered as current, then the suture is an unmarked summary wearing an
alien name and must be removed.

## Economics are selection, not magic

`station suture measure <id>` reports raw bytes, explicitly not model tokens.
The first `organism-receipt-schema` pack selects all 3,393 bytes of its donor
and stores 5,080 bytes because base64 plus metadata costs space: it is a
portable exact cache, not a saving. The narrower `organism-receipt-contract`
pack carries two exact intervals (constants plus report/render) totaling 2,157
of the 3,393 donor bytes: 1,236 bytes are avoided only for the declared task of
interpreting an existing receipt. Its 3,748-byte stored form still has transport
overhead. The honest efficiency appears when a successor loads the raw decoded
2,157 bytes instead of the full donor or wider estate, and reuses the verified
pointer; no tokenizer or reasoning-quality gain is claimed from a byte count.
