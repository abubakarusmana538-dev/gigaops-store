# GigaOps Store

Project by Usman Abubakar.

Microservices demo shop (frontend, product API, order API, MySQL) built to run on a
kubeadm / containerd / Calico Kubernetes cluster, with Docker image builds via GitHub Actions
and three ways to deploy: plain manifests, Helm, and Kustomize.

```
Browser -> frontend (nginx :80, NodePort)
              |-- /api/products/ -> product-service :5001
              |-- /api/orders/   -> order-service   :5002 -> product-service, MySQL :3306
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `services/` | Source + Dockerfiles for frontend, product-service, order-service |
| `k8s/base/` | Plain manifests (single `gigaops-store` namespace, PVC-backed MySQL) |
| `k8s/extras/` | HPA, PodDisruptionBudgets, quota/limits, NetworkPolicies, Ingress |
| `helm/gigaops-store/` | Helm chart + `values-dev/test/prod.yaml` |
| `kustomize/` | Base + dev/test/prod overlays |
| `docs/` | Cluster install guide and operations runbook |
| `.github/workflows/ci.yml` | Lint/render checks, then build and push images on `main` |
| `docker-compose.yml` | Run everything locally without Kubernetes |

## Quick start

### 1. Run locally
```bash
docker compose up --build      # http://localhost:8080
```

### 2. Build and push images
```bash
make build push REGISTRY=<your-dockerhub-user> TAG=v1
```
The manifests default to `gigaops/...` images. Either push to that namespace or change the
image names (Helm: `images.*` in values; Kustomize: `images:` in the overlay; plain: edit `k8s/base`).

### 3. Deploy (pick ONE method per namespace)

**Plain manifests**
```bash
kubectl get storageclass            # set the right one in k8s/base/02-mysql.yaml
kubectl apply -f k8s/base/
kubectl apply -f k8s/extras/        # optional hardening (needs metrics-server / Calico / ingress)
```
**Helm**
```bash
helm upgrade --install gigaops-dev helm/gigaops-store -n gigaops-dev --create-namespace \
  -f helm/gigaops-store/values-dev.yaml
```
**Kustomize**
```bash
kubectl create namespace gigaops-dev
kubectl apply -k kustomize/overlays/dev
```

| Env | Namespace | Images | Replicas | NodePort |
| --- | --- | --- | --- | --- |
| dev | gigaops-dev | v1 | 1 | 30080 |
| test | gigaops-test | v2 | 2 | 30081 |
| prod | gigaops-prod | v3 | 3 | 30082 |

Open `http://<node-ip>:<nodePort>`.

## Production notes (read before going live)

- **Secrets**: passwords in `secret.yaml` / `values.yaml` are lab defaults. Use Sealed Secrets,
  External Secrets or Vault, or override at install time: `--set database.password=...`.
- **Database**: MySQL is a single-replica Deployment. Helm prod enables a PVC
  (`persistence.enabled: true`); dev/test are ephemeral. For real production data use a managed
  database (e.g. AWS RDS) or an operator-managed StatefulSet.
- **Kustomize** overlays are ephemeral-DB only (matching the lab); add a PVC patch if needed.
- **NodePort** is for labs. Use the Ingress in `k8s/extras/ingress.yaml` plus TLS for real traffic.
- Pin images by tag/digest, never `latest`, in prod.

## Changes vs. the original lab files

- Order service: wrapped the product call in error handling (502 instead of a crash), and runs
  under gunicorn with DB init once at startup (the lab ran Flask's dev server).
- Containers run as a non-root user; Python services use gunicorn.
- Helm: uses `.Release.Namespace` instead of a `namespace` value (so `-n` and values can't disagree);
  NodePort only rendered for `type: NodePort`; optional MySQL PVC.
- Plain manifests: added startup probe for the order service, resource limits, MySQL readiness probe
  and `Recreate` strategy for the RWO volume.

## CI/CD

`ci.yml` runs on every push/PR (Python syntax, `helm lint`/`template`, `kustomize build`). On `main` it
builds and pushes the three images tagged with the commit SHA and `latest`.
Add repo secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.
