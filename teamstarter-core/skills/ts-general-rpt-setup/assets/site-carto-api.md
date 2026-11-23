# The Carto V2 page on a ChatGPT Site: what the Site provides

Give this file to ChatGPT (`@Sites`) with the page `carto-v2.html` that Teamstarter sent. It says
how to publish the page and which interface the Site's server part implements, so that the
controls of the page that write an answer (« Juste », « Corriger », « Pas celle-ci », « Marquer
comme fait », the state of a decision) work. Without the interface the page shows none of these
controls: it is then a page to read.

## Publish the page

- Serve `carto-v2.html` as the home page of the Site, unchanged: do not rewrite, minify or split
  it. The file is a fragment. Put it after
  `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">`.
- The page loads its fonts from `fonts.googleapis.com` and `fonts.gstatic.com`, and two scripts
  from `cdnjs.cloudflare.com` and `cdn.jsdelivr.net`. Allow them.
- Restrict the Site to the workspace, or to named people. Never public: the page shows the work
  of named people.

## The interface

Same origin, JSON, under `/api/carto`. The reader is the signed-in visitor the platform forwards
to the server part (`oai-authenticated-user-email`, `oai-authenticated-user-full-name`). A
request without a signed-in visitor gets `401` on every route.

The page never receives an e-mail address. The `id` of a visitor is `u_` followed by the first
22 characters of base64url(SHA-256(salt + lower-cased e-mail)), the salt being a secret of the
Site. It is the same at every visit.

| Route | Answer |
|---|---|
| `GET /api/carto/me` | `200 {"id": "u_…", "name": "<full name, or empty>", "write": true}` |
| `GET /api/carto/docs?collection=<path>` | `200 {"docs": [{"id": "<last segment>", "data": {…}}]}`: the documents directly in the collection that this visitor may read |
| `GET /api/carto/doc?path=<path>` | `200 {"exists": true, "data": {…}}`, or `200 {"exists": false}` (also for a document this visitor may not read) |
| `PUT /api/carto/doc?path=<path>`, body `{"data": {…}, "merge": false}` | Replaces the document. `200 {"ok": true}` |
| the same, with `"merge": true` | Merges `data` into the existing document: nested objects recursively, any other value replaced. The merge never follows the keys `__proto__`, `constructor` and `prototype`. `400 {"code": "invalid_argument"}` when the document does not exist |
| `DELETE /api/carto/doc?path=<path>` | `200 {"ok": true}` |

A path is made of segments `[A-Za-z0-9_\-.~:@+]{1,200}` joined by `/`, at most 16. A collection
has an odd number of segments, a document an even number. A document is a JSON object of at most
256 KiB.

`write` is `true` for every signed-in visitor: a Site has no level between reading it and
editing it, so the people the Site admits are the people who may answer. A Site that wants some
of them to read only answers `"write": false` for them and refuses their writes: the page then
shows them no control.

The rules, enforced in the server part (a hidden button protects nothing):

- `data/users/<id>/…` is read and written by the visitor whose `id` it is, and by nobody else.
- `answers/<id>` is read by every visitor. It is written by the visitor whose `id` it is, and by
  the owners of the Site (a list of e-mail addresses kept in a secret). Anyone else gets
  `403 {"code": "invalid_argument"}`.
- Every other path is read and written by every signed-in visitor.

One table is enough:
`docs(path TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL, updated_by TEXT NOT NULL)`.

## Check

1. Signed in, open `<site>/api/carto/me`: a JSON object whose `id` starts with `u_`.
2. Open the page, space « Déploiement »: an access to open has the button « Marquer comme
   fait ». Click it, reload the page: the line still says « Fait le … ».
3. A second member opens the page: they see that line, without « Annuler ».

If one of the three fails and cannot be fixed, tell Teamstarter: it sends the page built
read-only, which shows no control that writes on any host.

Teamstarter has a reference implementation of this interface (Node, in memory) and the test
that runs the page against it; ask for them if ChatGPT needs a model.
