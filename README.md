# 1-DCLT-GITOPS-FASE-5 — SolidaryTech GitOps

Manifestos Kubernetes + configurações ArgoCD para o ecossistema SolidaryTech.

## Estrutura

```
.
├── bootstrap.sh                    # Script de instalação do ArgoCD + registro das apps
├── apps/
│   ├── ngo-service/                # Deployment, Service, HPA (porta 8081)
│   ├── donation-service/           # Deployment, Service, HPA (porta 8082, hot path)
│   └── volunteer-service/          # Deployment, Service, HPA (porta 8083)
├── argocd-apps/
│   ├── app-ngo.yaml                # ArgoCD Application — ngo-service
│   ├── app-donation.yaml           # ArgoCD Application — donation-service
│   ├── app-volunteer.yaml          # ArgoCD Application — volunteer-service
│   ├── app-monitoring.yaml         # ArgoCD Application — kube-prometheus-stack
│   ├── app-loki.yaml               # ArgoCD Application — Loki + Promtail
│   └── app-velero.yaml             # ArgoCD Application — Velero (DR)
└── infra/
    ├── namespace/namespace.yaml    # Namespace solidarytech
    ├── argocd/argocd-install.yaml  # ArgoCD AppProject solidarytech
    ├── monitoring/
    │   ├── prometheus-values.yaml  # kube-prometheus-stack + alertas SLO
    │   ├── grafana-values.yaml     # Dashboards SRE (donation-service)
    │   ├── loki-values.yaml        # Agregação de logs
    │   └── otel-collector-values.yaml # OpenTelemetry → Datadog
    └── velero/
        └── velero-install.yaml     # Backup diário às 02:00 + Schedule
```

## Como usar

### 1. Bootstrap (primeira vez)

```bash
az login
az aks get-credentials --resource-group rg-solidarytech-fase5 --name aks-solidarytech
./bootstrap.sh
```

### 2. Criar Secrets antes do primeiro sync

```bash
# ngo-service
kubectl create secret generic ngo-service-secrets \
  --from-literal=database-url="postgresql://adminuser:<senha>@pg-ngo-solidarytech-f5.postgres.database.azure.com:5432/ngodb?sslmode=require" \
  -n solidarytech

# donation-service
kubectl create secret generic donation-service-secrets \
  --from-literal=database-url="postgresql://adminuser:<senha>@pg-donation-solidarytech-f5.postgres.database.azure.com:5432/donationdb?sslmode=require" \
  --from-literal=storage-connection-string="<connection-string-do-storage-account>" \
  -n solidarytech

# volunteer-service (CosmosDB via API Table compatível com DynamoDB)
kubectl create secret generic volunteer-service-secrets \
  --from-literal=cosmos-region="eastus2" \
  --from-literal=cosmos-access-key="<cosmos-account-name>" \
  --from-literal=cosmos-secret-key="<cosmos-primary-key>" \
  --from-literal=cosmos-endpoint="https://<cosmos-account>.table.cosmos.azure.com:443/" \
  -n solidarytech
```

### 3. Verificar sincronização

```bash
kubectl get applications -n argocd
kubectl get pods -n solidarytech
kubectl get pods -n monitoring
```

## SLOs — donation-service

| SLI | Métrica | SLO |
|---|---|---|
| Taxa de Sucesso | `rate(http_requests_total{service="donation-service",status!~"5.."}[5m])` | ≥ 99.9% |
| Latência P99 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | ≤ 500ms |

Alertas configurados em `infra/monitoring/prometheus-values.yaml`.

## HPA — donation-service (hot path)

- **min:** 2 réplicas / **max:** 10 réplicas
- **CPU trigger:** 70%
- **Scale up:** +2 pods/min, janela 30s
- **Scale down:** -1 pod/2min, janela 5min

## DR — Velero

Backup diário às **02:00 UTC**, namespace `solidarytech`, retenção **30 dias**.

```bash
velero restore create --from-schedule daily-backup-solidarytech
velero backup get
```