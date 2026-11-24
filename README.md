# MindScope landing site

The public site at **https://mindscopecares.com**. `www.mindscopecares.com`
redirects there. It's a React + Vite single-page app in `website/`, hosted on
**Firebase Hosting** in the Google Cloud project `mindscope-prod` (site
`mindscope-prod`, also reachable at https://mindscope-prod.web.app).

## Develop

```bash
cd website
npm ci
npm run dev        # http://localhost:5173
```

Node 22+ is required (Vite 8).

The AI features (IEP analyzer, research-to-slides) call the service set in
`website/src/lib/siteConfig.ts` (`PROCESS_URL`).

## Ship a change

1. Branch from `main`, commit, push, open a PR.
2. CI runs (typecheck, tests, build, security-header check), and Firebase posts a
   **preview URL** on the PR.
3. **@AJEgwu approves** (`approval-gate` check). Teammates can review and LGTM too.
4. Squash-merge. "Deploy to Firebase Hosting on merge" builds and publishes it
   to mindscopecares.com, usually within about 2 minutes.

Deploys authenticate with GitHub's OIDC token through Workload Identity
Federation (repo variables `GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`); there is no
service-account key anywhere.

**Roll back:** Firebase console → Hosting → *mindscope-prod* → Release history →
pick an earlier release → **Roll back**. Or re-run an earlier successful
"Deploy to Firebase Hosting on merge" run.

## Security headers

`website/firebase.json` sets HSTS, X-Frame-Options, a frame-ancestors CSP,
nosniff, Referrer-Policy and Permissions-Policy on every page. CI fails if any
of them is removed (`scripts/check_hosting_headers.py`).

## Layout

```text
website/               the app (src/, public/, vite.config.ts, firebase.json)
scripts/               CI checks
.github/               CI, Firebase deploys and previews, approval gate
```
