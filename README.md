### Nested repositories (git subtree)

This repo vendors some other projects via `git subtree`:

- `fury_api/` ← mirrors branch `digital-me` of `andre-cavalheiro/fury_api`
- `halo_webapp/` ← mirrors branch `digital-me` of `andre-cavalheiro/halo_webapp`

Day-to-day you can edit these folders and commit to `digital_me` as usual.

To sync **from** the upstream repos into this project:

```bash
# fury_api
git fetch fury_api
git subtree pull --prefix=fury_api fury_api digital-me --squash

# halo_webapp
git fetch halo_webapp
git subtree pull --prefix=halo_webapp halo_webapp digital-me --squash