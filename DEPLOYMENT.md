# Deployment

This document describes the three supported deployment scenarios for Mosaic.

---

## 1. Local (Development)

The recommended setup for running the full interactive application.

**Requirements:** Python 3.11+, Node 18+

```bash
# Backend
python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Access at `http://localhost:5173`. The frontend proxies API calls to `http://localhost:8000`.

---

## 2. EC2 Production (Primary — Automated via GitHub Actions)

The live public deployment runs on a single AWS EC2 t3.micro instance (Ubuntu 22.04, ap-south-1).

**Architecture:**

```
Internet → EC2 (13.205.223.250)
  └── nginx (port 80)
        ├── /        → serves frontend/dist/ (React static build)
        └── /api/*   → proxies to uvicorn on 127.0.0.1:8000
```

nginx and uvicorn share the same origin, so no CORS configuration is needed.

### First-time setup (already done)

The EC2 instance was provisioned using:

```bash
aws ec2 run-instances --image-id ami-0a9723306502e2558 \
  --instance-type t3.micro --key-name mosaic-key \
  --security-group-ids sg-0f2fa6547f53f7a49 \
  --user-data file://deploy/userdata.sh
```

The `deploy/userdata.sh` bootstrap script ran automatically on first boot and:
- Installed nginx, Python 3.11, Node, npm
- Cloned the repository
- Created a Python virtualenv with CPU-only PyTorch
- Built the React frontend
- Configured nginx and the systemd service
- Started both services

### Continuous deployment

Every push to `main` that passes CI automatically deploys via `.github/workflows/deploy.yml`:

1. GitHub Actions SSHes into the instance as the `mosaic` user
2. Runs `deploy/deploy.sh` which:
   - `git pull origin main`
   - `pip install -r requirements.txt` (installs only changed packages)
   - `npm install && npm run build` (rebuilds frontend)
   - `sudo systemctl restart mosaic-api`

**Deploy time:** ~45 seconds on a warm instance (packages cached, no full reinstall).

### Instance details

| Resource | Value |
|---|---|
| Instance ID | `i-03c19cf337c0447d2` |
| Public IP (permanent) | `13.205.223.250` |
| Region | `ap-south-1` (Mumbai) |
| Instance type | `t3.micro` (1 GB RAM, 2 vCPU) |
| OS | Ubuntu 22.04 LTS |
| Key pair | `mosaic-key` (stored at `~/.ssh/mosaic-key.pem`) |
| Security group | `sg-0f2fa6547f53f7a49` (ports 22, 80, 443) |

### SSH access

```bash
ssh -i ~/.ssh/mosaic-key.pem mosaic@13.205.223.250
```

### Checking service status

```bash
sudo systemctl status mosaic-api
sudo systemctl status nginx
sudo journalctl -u mosaic-api -n 50
```

### Notes

- **Persistent filesystem:** The EBS volume (20 GB gp3) persists across reboots and redeployments. Completed `runs/` directories survive.
- **Memory:** t3.micro has 1 GB RAM. Default simulations (N=200) use ~50 MB. UMAP uses ~150 MB. Large runs (N≥1000) may hit the memory limit and should be run locally.
- **Workers:** uvicorn runs with 2 workers. Simultaneous simulations from two users are supported; more than two concurrent large runs may cause OOM.

---

## 3. GitHub Pages Static Showcase (Secondary)

A read-only, non-interactive version of the site is automatically deployed to GitHub Pages on every push to `main` via `.github/workflows/pages.yml`.

**URL:** `https://adityawagh19.github.io/Mosaic/`

**What works without the backend:**
- Landing page
- Method guide
- Experiments page layout (figures do not load without the backend)

**What requires the local backend:**
- Running simulations
- Viewing completed run results
- Comparison page
- ML analysis page

API-dependent pages show their graceful empty or error states when the backend is unavailable. There is no broken state — every page degrades cleanly.

### Activation (one-time)

After the first `pages.yml` workflow run, go to:

> Repository Settings → Pages → Source: **Deploy from a branch** → Branch: **gh-pages**, Folder: **/ (root)**

### SPA routing

GitHub Pages does not support server-side routing. The `frontend/public/404.html` file encodes unrecognised paths into a query string and redirects to `index.html`, which restores the URL before React Router hydrates. This allows deep links (e.g., `/experiments`) to work correctly.

---

## Environment Variables

| Variable | Used in | Default | Purpose |
|---|---|---|---|
| `VITE_API_BASE_URL` | Frontend build | `http://localhost:8000` | Base URL for API requests |
| `VITE_BASE_PATH` | Frontend build | `/` | Base path for Vite asset URLs (set to `/Mosaic/` for GitHub Pages) |

Local development uses `frontend/.env.local` (gitignored):

```
VITE_API_BASE_URL=http://localhost:8000
```

EC2 production build sets `VITE_API_BASE_URL=/api` so nginx proxies all requests on the same origin.

GitHub Pages build sets both `VITE_BASE_PATH=/Mosaic/` and `VITE_API_BASE_URL=http://localhost:8000`.
