#!/bin/bash
set -euo pipefail

ARGOCD_VERSION="v2.12.0"
GITOPS_REPO="https://github.com/DCLT/1-DCLT-GITOPS-FASE-5"
RESOURCE_GROUP="rg-solidarytech-fase5"
AKS_NAME="aks-solidarytech"

echo "==> Obtendo credenciais do AKS..."
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_NAME" --overwrite-existing

echo "==> Criando namespace argocd..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

echo "==> Instalando ArgoCD ${ARGOCD_VERSION}..."
kubectl apply -n argocd -f "https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"

echo "==> Aguardando ArgoCD ficar pronto..."
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=180s

echo "==> Aplicando namespace solidarytech..."
kubectl apply -f infra/namespace/namespace.yaml

echo "==> Aplicando ArgoCD Project..."
kubectl apply -f infra/argocd/argocd-install.yaml

echo "==> Registrando Applications dos serviços..."
kubectl apply -f argocd-apps/app-ngo.yaml
kubectl apply -f argocd-apps/app-donation.yaml
kubectl apply -f argocd-apps/app-volunteer.yaml

echo "==> Registrando Applications de infra..."
kubectl apply -f argocd-apps/app-monitoring.yaml
kubectl apply -f argocd-apps/app-loki.yaml
kubectl apply -f argocd-apps/app-velero.yaml

echo ""
echo "==> Senha inicial do ArgoCD admin:"
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d
echo ""

echo "==> Port-forward ArgoCD UI (acesse http://localhost:8080):"
echo "    kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
echo "Bootstrap concluído. ArgoCD sincronizará os apps automaticamente."
