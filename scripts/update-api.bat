@echo off
for /f %%i in ('powershell -Command "[DateTimeOffset]::Now.ToUnixTimeSeconds()"') do set TIMESTAMP=%%i
set TAG=api-%TIMESTAMP%

echo Updating API...
echo Building image: %TAG%
docker build -t %TAG% .

echo Cleaning old image from Minikube...
minikube ssh "docker rmi %TAG% 2>/dev/null || true"

echo Loading image into Minikube...
minikube image load %TAG%

echo Updating deployment...
kubectl set image deployment/api api=%TAG% -n app

echo Waiting for new pod to be ready...
kubectl rollout status deployment/api -n app --timeout=60s

echo API updated successfully!