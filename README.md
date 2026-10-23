# MindScope landing site

The public site at **https://mindscopecares.com** (`www` redirects to it).
It's a React + Vite single-page app in `website/`, served by nginx on Google
Cloud Run (service `mindscope-landing`, project `mindscope-prod`).

## Develop

```bash
cd website
npm ci
npm run dev        # http://localhost:5173
```

Node 22+ is required (Vite 8).

The AI features (IEP analyzer, research-to-slides) call an Azure Function set
in `website/src/lib/siteConfig.ts` (`PROCESS_URL`).

## Ship a change

1. Branch from `main`, commit, push, open a PR.
2. CI runs (typecheck, build, container check) and the PR gets a **preview URL**.
3. **@AJEgwu approves** (`approval-gate` check). Teammates can review and LGTM too.
4. Squash-merge. `Deploy` builds, smoke-tests the new revision, then moves
   mindscopecares.com to it, usually within about 4 minutes.

Roll back: Actions → Deploy → re-run an earlier successful run, or
`gcloud run services update-traffic mindscope-landing --to-revisions <revision>=100 --region us-central1 --project mindscope-prod`.

## Layout

```text
website/          the app (src/, public/, vite.config.ts)
deploy/nginx.conf static serving, SPA fallback, www → apex redirect, /health
Dockerfile        build + nginx image
.github/          CI, deploy, previews, approval gate
```
