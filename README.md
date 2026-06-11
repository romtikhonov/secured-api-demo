# 🚀 Secured API

Local development environment with Minikube, HashiCorp Vault, PostgreSQL, Redis, and background workers.  
All secrets are securely managed via Vault.

🔐 **Security Features**:  
- JWT access/refresh tokens with audience validation  
- Secrets from HashiCorp Vault (Kubernetes auth)  
- Distributed locks for race condition prevention  
- Parameterized SQL queries (SQL injection protection)

---

## 🧰 Requirements

- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (v1.30+)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Docker
- Terminal with `make` support

---

## 🏗️ Architecture Overview

**Key Patterns Implemented**:  
✅ Dependency Injection (FastAPI Depends)  
✅ Unit of Work + Repository Pattern  
✅ Write-Through Caching (User profiles)  
✅ Cache-Aside (Leaderboard scores)  
✅ Observer Pattern (Login notifications via Pub/Sub)  
✅ Adapter Pattern (SecretProvider abstraction)

---

## 🚦 Quick Start

```bash
# 1. Deploy the full stack
make setup
# → Follow terminal instructions to initialize Vault
make setup-continue
# → Write secrets to Vault
make deploy-services

# 2. Start port-forward (keep window minimized)
make api-port-forward

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
- To launch postgres port-forward run:
make db-port-forward
