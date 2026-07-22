# NIFTY Guardian — Release Checklist

Run through this before every deployment to staging or production.

## Code quality

- [ ] `ruff check .` passes (backend)
- [ ] `mypy app tests` passes (backend, strict mode)
- [ ] `pytest tests/ -v` passes (backend)
- [ ] `npm run typecheck` passes (frontend, TypeScript strict)
- [ ] `npm run lint` passes (frontend, oxlint)
- [ ] `npm run format:check` passes (frontend, prettier)
- [ ] `npm run test` passes (frontend, vitest)
- [ ] `npm run build` succeeds (frontend production bundle)

## Docker

- [ ] `docker build -f deploy/docker/backend.Dockerfile --target production .` succeeds
- [ ] `docker build -f deploy/docker/frontend.Dockerfile --target production .` succeeds
- [ ] `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml config` validates without error
- [ ] `.github/workflows/full-platform.yml` is green on the commit being released

## Configuration

- [ ] `config/<environment>.env` has every `CHANGE ME` value filled in - see `docs/CONFIGURATION_REFERENCE.md`
- [ ] `SECRET_KEY` is freshly generated for this environment, never reused from another
- [ ] `CORS_ORIGINS` points at the real frontend origin, not `localhost`
- [ ] `LOG_LEVEL` is `INFO` or higher (not `DEBUG`)
- [ ] `LOG_FORMAT=json` for staging/production
- [ ] `GET /health/ready` on the target environment reports every check `ok: true` before cutting traffic over

## Security

- [ ] No secrets committed anywhere in the diff being released (`git diff` reviewed, not just `git status`)
- [ ] `docs/SECURITY.md` reviewed if anything about credential loading or secret management changed

## Live Trading Mode (only if `LIVE_MODE=true` for this release)

**Do not check this section's boxes casually - see
`docs/LIVE_TRADING_GUIDE.md`'s own Operational Checklist for full
detail.**

- [ ] `MAX_DAILY_LOSS`/`MAX_OPEN_POSITIONS`/`MAX_ORDERS_PER_DAY` reviewed and deliberately set, not left at defaults
- [ ] `TRADING_START`/`TRADING_END` match the intended trading session
- [ ] `ZERODHA_API_KEY`/`ZERODHA_API_SECRET`/`ZERODHA_ACCESS_TOKEN` are set and current (today's access token)
- [ ] Kill switch reachable and exercised at least once outside a test, this deployment
- [ ] A human is actively monitoring logs/`SafetyManager` decisions for the first live session after this release

## Rollback plan

- [ ] Previous image tag/commit identified and available to redeploy
- [ ] Database migration (if any) has a documented rollback path, or the release makes no schema changes
- [ ] `docs/INCIDENT_RESPONSE.md` reviewed by whoever is on call for this release

## Post-release verification

- [ ] `GET /health/live` returns 200
- [ ] `GET /health/ready` returns 200 with every check `ok: true`
- [ ] `GET /health/metadata` reports the expected `version`/`git_commit`
- [ ] Frontend loads and connects to the backend (`VITE_DASHBOARD_SERVICE=rest` path exercised, not just the mock)
- [ ] No unexpected ERROR/CRITICAL log lines in the first few minutes after cutover
