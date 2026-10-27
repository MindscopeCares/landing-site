# Staging and production releases

Merging a PR runs CI, builds one SHA-tagged image, deploys it to the separate
`mindscope-landing-staging` service, and checks it before routing staging traffic.
It never routes production traffic. PR previews use staging, too.

Production is explicit: run **Release to production** with the reviewed main
commit SHA. The workflow refuses commits without successful staging, passing
PR CI, or required approval. Only `RELEASE_MANAGERS` may start it. It promotes
the existing image by immutable digest, probes it with zero user traffic, then
ramps 10% → 50% → 100%, watching health/version and Cloud Monitoring at each
stage. Failure rolls back to the captured stable revision. Monitoring failures
block promotion. `skip_canary` skips intermediate percentages, not probes.

## One-time setup before merging

Provision `mindscope-landing-staging` separately from production, then set repository
variable `STAGING_SERVICE=mindscope-landing-staging`. The workflow checks the service
exists; it never copies production configuration or secrets. Use a dedicated
staging runtime identity with only staging permissions. Set `RELEASE_MANAGERS`
to the intended GitHub logins (for example AJEgwu). For the first release set `RELEASE_BASELINE_SHA` to the full commit currently
serving production (confirm it from Cloud Run, not merely the latest main).
Later production revisions carry a full `commit` label, so the gate checks
all first-parent commits since the actual stable revision, even after failed
releases. The target must still be the image currently serving staging.
Existing project/region,
image registry, WIF and deployment identity variables remain in use.

The first staging deploy happens only after this PR is merged and setup is
complete. Existing production stays on its current revision. No release train
is enabled by this PR; releases require an explicit workflow run.

## Emergency rollback

If a rollout fails, its failure handler restores the previous stable revision.
For a later incident, inspect Cloud Run revision history and route 100% to a
known-good revision of the same production service. Keep its image and database
compatibility in mind. No database restore occurs automatically.
