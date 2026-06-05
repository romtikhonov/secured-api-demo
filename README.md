# 🚀 Secured API

Local development environment with Minikube, HashiCorp Vault, PostgreSQL, Redis, and background workers.  
All secrets are securely managed via Vault.

---

## 🧰 Requirements

- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (v1.30+)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Docker
- Terminal with `make` support

---

## 🚦 Quick Start

```bash
# 1. Deploy the full stack
make setup
# → Make Vault manual steps
make setup-continue
# → Write secrets
make deploy-services

# 2. Start port-forward (keep window minimized)
make start-api

# 3. Test the API
curl http://localhost:8000/health


💡 On first run, follow terminal instructions to initialize Vault.

💡 Tips
- To update code run:
make update-api
- To get API logs run:
make logs-api
- To remove all run:
make remove-all