# Makefile

.PHONY: build-image minikube vault vault-root-token vault-init vault-cleanup db api worker start-api logs-api setup setup-continue deploy-services remove-all update-api update-api-bat

build-image:
	@echo "Building api:latest..."
	docker build -t api:latest .

minikube:
	@echo "Start Minikube..."
	minikube start --driver=docker
	minikube image load api:latest
	kubectl apply -f k8s/namespace.yaml

vault:
	@echo "Deploy Vault..."
	kubectl apply -f k8s/vault/

vault-root-token:
	@echo ""
	@echo "Init Vault..."
	@echo "!!! Manual steps required !!!"
	@echo "1. Check Vault pod is running"
	@echo " kubectl get pods -n app "
	@echo " Wait a little if not"
	@echo "2. Copy & execute to initialize: "
	@echo "   kubectl exec -it -n app deploy/vault -- sh -c 'export VAULT_ADDR=http://127.0.0.1:8200 && vault operator init' "
	@echo "!!! SAVE root token and unseal keys securely !!!"
	@echo "3. Unseal Vault (!!! run 3 times with different keys !!!):"
	@echo "   kubectl exec -it -n app deploy/vault -- sh -c 'export VAULT_ADDR=http://127.0.0.1:8200 && vault operator unseal' "
	@echo "4. Create Kubernetes secret:"
	@echo "   kubectl create secret generic vault-root-token -n app --from-literal=token=<YOUR_ROOT_TOKEN> "
	@echo ""
	@echo "!! After completing these steps, run: make setup-continue !!!"
	@echo ""

vault-init:
	@echo "Configure Vault..."
	kubectl apply -f k8s/vault-init/
	@echo "Waiting for job completion (max 60s)..."
	kubectl wait --for=condition=complete job/vault-init -n app --timeout=60s
	@echo ""
	@echo "!!! NEXT: Store your application secrets in Vault !!!"
	@echo "Example (replace <ROOT_TOKEN> with your actual token):"
	@echo "  kubectl exec -it -n app deploy/vault -- sh -c 'VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=<ROOT_TOKEN> vault kv put secret/db/creds password=your_strong_password' "
	@echo "  kubectl exec -it -n app deploy/vault -- sh -c 'VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=<ROOT_TOKEN> vault kv put secret/redis/creds password=your_redis_password' "
	@echo "  kubectl exec -it -n app deploy/vault -- sh -c 'VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=<ROOT_TOKEN> vault kv put secret/auth/jwt secret_key=jwt_secret_key' "
	@echo ""
	@echo "!!! After completing these steps, run: make deploy-services !!!"
	@echo ""

vault-cleanup:
	@echo "Delete root-token from Kubernetes..."
	kubectl delete secret vault-root-token -n app --ignore-not-found

db:
	@echo "Deploy PostgreSQL and Redis..."
	kubectl apply -f k8s/postgres/
	kubectl apply -f k8s/redis/

api:
	@echo "Deploy API..."
	kubectl apply -f k8s/api/

worker:
	@echo "Deploy email-worker..."
	kubectl apply -f k8s/email-worker/

start-api:
	@echo "Launch port-forward..."
	kubectl port-forward svc/api 8000:8000 -n app

update-api:
	@TAG=$$(date +'%d%m%Y-%H%M%S'); \
	echo "Updating API..." && \
	echo "Building image: api-$$TAG" && \
	docker build -t "api-$$TAG" . && \
	echo "Cleaning old image from Minikube..." && \
	minikube ssh "docker rmi api-$$TAG 2>/dev/null || true" && \
	echo "Loading image into Minikube..." && \
	minikube image load "api-$$TAG" && \
	echo "Updating deployment..." && \
	kubectl set image deployment/api api="api-$$TAG" -n app && \
	echo "Waiting for new pod to be ready..." && \
	kubectl rollout status deployment/api -n app --timeout=60s && \
	echo "API updated successfully!"

update-api-bat:
	cmd /c ".\\scripts\\update-api.bat"

logs-api:
	@echo "API Logs:"
	kubectl logs -l app=api -n app -f

remove-all:
	minikube delete

setup: build-image minikube vault vault-root-token

setup-continue: vault-init

deploy-services: vault-cleanup db api worker
	@echo "Setup done!"