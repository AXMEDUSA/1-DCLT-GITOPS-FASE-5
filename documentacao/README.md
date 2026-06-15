# SolidaryTech — Documentação Técnica Completa

> Hackathon FIAP — Fase 5 | Equipe DCLT

---

## Sumário

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura](#2-arquitetura)
3. [Microsserviços](#3-microsserviços)
4. [Infraestrutura como Código (Terraform)](#4-infraestrutura-como-código-terraform)
5. [Containers e CI/CD](#5-containers-e-cicd)
6. [GitOps com ArgoCD](#6-gitops-com-argocd)
7. [Observabilidade](#7-observabilidade)
8. [SRE — Confiabilidade e Golden Metrics](#8-sre--confiabilidade-e-golden-metrics)
9. [FinOps — Otimização Financeira](#9-finops--otimização-financeira)
10. [AIOps e ITSM — Gestão Preditiva de Incidentes](#10-aiops-e-itsm--gestão-preditiva-de-incidentes)
11. [Disaster Recovery e Continuidade de Negócios](#11-disaster-recovery-e-continuidade-de-negócios)

---

## 1. Visão Geral do Projeto

A **SolidaryTech** é uma plataforma sem fins lucrativos que conecta ONGs a doadores e voluntários em todo o Brasil. Após ganhar destaque em rede nacional, a plataforma passou a enfrentar picos de acesso imprevisíveis, exigindo uma arquitetura de microsserviços resiliente, observável e financeiramente sustentável.

### Repositórios

| Repositório | Finalidade |
|---|---|
| `1-DCLT-TERRAFORM-FASE-5` | IaC — provisionamento de toda a infraestrutura Azure |
| `1-DCLT-APPLICATIONS-FASE-5` | Dockerfiles, código-fonte e pipelines CI/CD |
| `1-DCLT-GITOPS-FASE-5` | Manifestos Kubernetes e configuração do ArgoCD |

### Princípios da Regra de Ouro

- **Sem deploy manual via `kubectl`** — todo deploy passa pelo ArgoCD
- **Sem infraestrutura "clicada" no console** — tudo provisionado via Terraform
- **Sem voo cego** — observabilidade completa com Prometheus, Grafana, Loki e Datadog APM

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Azure — eastus2                            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   AKS — centralus                            │  │
│  │                                                              │  │
│  │  namespace: solidarytech          namespace: monitoring      │  │
│  │  ┌─────────────────────┐         ┌──────────────────────┐   │  │
│  │  │  ngo-service        │         │  Prometheus           │   │  │
│  │  │  Python / Flask     │         │  Grafana (3 dashboards│   │  │
│  │  │  PostgreSQL         │         │  Loki + Promtail      │   │  │
│  │  ├─────────────────────┤         │  Datadog Agent        │   │  │
│  │  │  donation-service   │         └──────────────────────┘   │  │
│  │  │  Go / HTTP          │                                     │  │
│  │  │  PostgreSQL + Queue │         namespace: argocd           │  │
│  │  │  HPA: 2–10 réplicas │         ┌──────────────────────┐   │  │
│  │  ├─────────────────────┤         │  ArgoCD              │   │  │
│  │  │  volunteer-service  │         │  GitOps Controller   │   │  │
│  │  │  Python / Flask     │         └──────────────────────┘   │  │
│  │  │  CosmosDB (Table)   │                                     │  │
│  │  └─────────────────────┘         namespace: velero           │  │
│  │                                  ┌──────────────────────┐   │  │
│  │                                  │  Velero              │   │  │
│  │                                  │  Backup → brazilsouth│   │  │
│  │                                  └──────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │  ACR          │  │  PostgreSQL   │  │  Azure Storage       │    │
│  │  acrsolidary  │  │  3x Flexible  │  │  Queue: fila-solid.  │    │
│  │  techf5       │  │  Server       │  │  Blob: tfstate       │    │
│  └──────────────┘  └───────────────┘  └──────────────────────┘    │
│                                                                     │
│  ┌──────────────┐  ┌───────────────┐                               │
│  │  Redis       │  │  CosmosDB     │                               │
│  │  Balanced_B0 │  │  Table API    │                               │
│  │  (hot path)  │  │  Serverless   │                               │
│  └──────────────┘  └───────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘

GitHub Actions ──► ACR ──► ArgoCD ──► AKS
     (CI/CD)              (GitOps)   (cluster)
```

---

## 3. Microsserviços

### 3.1 ngo-service

**Linguagem:** Python 3 / Flask  
**Porta:** 8081  
**Banco:** PostgreSQL Flexible Server (centralus)  
**Função:** Cadastro e gestão das ONGs parceiras da plataforma.

**Endpoints:**

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Health check — retorna `{"status":"ok"}` |
| `POST` | `/ngos` | Cadastra nova ONG (campos: `name`, `email`, `cause`, `city`) |
| `GET` | `/ngos` | Lista todas as ONGs ordenadas por ID decrescente |

**Recursos no cluster:**
- Deployment: 1 réplica, `requests: 100m CPU / 128Mi`, `limits: 250m / 256Mi`
- HPA: min 1, max 5, CPU 70%
- Prometheus annotations para scrape automático (`/metrics`, porta 8081)
- Datadog APM: variáveis `DD_SERVICE`, `DD_ENV`, `DD_VERSION` injetadas

---

### 3.2 donation-service ⚡ Hot Path

**Linguagem:** Go 1.24  
**Porta:** 8082  
**Banco:** PostgreSQL Flexible Server (centralus)  
**Fila:** Azure Storage Queue (`fila-solidarytech`)  
**Cache:** Redis Managed (Balanced_B0)  
**Função:** Processamento das doações — caminho crítico da plataforma. Toda doação é processada aqui, persistida no PostgreSQL e um evento é despachado para a fila de notificações.

**Endpoints:**

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Health check — retorna `{"status":"ok"}` |
| `POST` | `/donations` | Processa nova doação (campos: `ngo_id`, `amount`, `donor_name`) |
| `GET` | `/donations` | Lista todas as doações ordenadas por data |

**Fluxo de uma doação:**
```
POST /donations → valida payload → INSERT PostgreSQL → status "APPROVED" → evento async Azure Storage Queue
```

**Recursos no cluster:**
- Deployment: **2 réplicas mínimas** (alta disponibilidade)
- HPA: **min 2, max 10**, CPU 70% / Memória 75%
- Scale up: +2 pods por minuto (janela 30s)
- Scale down: -1 pod a cada 2 minutos (janela 300s — conservador)
- `topologySpreadConstraints`: pods distribuídos entre nós distintos
- `requests: 250m CPU / 256Mi`, `limits: 500m / 512Mi`
- Datadog APM completo com Distributed Tracing

**SLOs definidos:**

| SLI | Expressão | SLO |
|---|---|---|
| Taxa de Sucesso | `rate(http_requests_total{service="donation-service",status!~"5.."}[5m])` | ≥ 99,9% |
| Latência P99 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | ≤ 500ms |

---

### 3.3 volunteer-service

**Linguagem:** Python 3 / Flask  
**Porta:** 8083  
**Banco:** Azure CosmosDB (Table API, Serverless)  
**Função:** Match entre voluntários e campanhas das ONGs. Cada voluntário é registrado com um UUID único e associado a uma ONG pelo `ngo_id`.

**Endpoints:**

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Health check — retorna `{"status":"ok"}` |
| `POST` | `/volunteers` | Registra novo voluntário (campos: `name`, `email`, `ngo_id`) |
| `GET` | `/volunteers/<ngo_id>` | Lista voluntários de uma ONG específica |

**Recursos no cluster:**
- Deployment: 1 réplica, `requests: 100m CPU / 128Mi`, `limits: 250m / 256Mi`
- HPA: min 1, max 5, CPU 70%
- Datadog APM: variáveis `DD_SERVICE`, `DD_ENV`, `DD_VERSION` injetadas

---

## 4. Infraestrutura como Código (Terraform)

**Repositório:** `1-DCLT-TERRAFORM-FASE-5/`  
**Provider:** `azurerm` 4.x  
**Backend:** Azure Blob Storage (remote state)  
**Região principal:** `eastus2` (Resource Group) / `centralus` (AKS, PostgreSQL)

### Recursos provisionados

| Arquivo `.tf` | Recurso | Detalhes |
|---|---|---|
| `resourcegroup.tf` | Resource Group | `rg-solidarytech-fase5` — eastus2 |
| `aks.tf` | AKS Cluster | `aks-solidarytech` — centralus, Standard_D2s_v3, 2 nós, CNI Azure |
| `acr.tf` | Container Registry | `acrsolidarytechf5` — SKU Basic |
| `postgresql.tf` | PostgreSQL × 3 | Flexible Server — ngo, donation, volunteer |
| `redis.tf` | Redis Cache | `Balanced_B0` — hot path donation-service |
| `cosmo_db.tf` | CosmosDB | Table API, Serverless — volunteer-service |
| `storage_queue.tf` | Storage Queue | `fila-solidarytech` — eventos de doação |
| `storage_account_tfstate.tf` | Storage Account | tfstate remoto + blobs Velero DR |
| `vnet.tf` | VNet + Subnets + Peering | VNet principal + VNet AKS (isolada) |
| `private_endpoint.tf` | Private Endpoints | PostgreSQL e Redis sem IP público |
| `route_table.tf` | Route Table | Roteamento interno AKS |

### Política de Tags FinOps

Todos os recursos recebem as tags obrigatórias via `local.common_tags`:

```hcl
locals {
  finops_tags = {
    Project     = "SolidaryTech"
    Environment = "Production"
    Owner       = "FIAP-Team"
    CostCenter  = "NGO-Core"
    CreatedBy   = "Terraform"
    ManagedBy   = "Terraform"
  }
}
```

Aplicado em: AKS, ACR, PostgreSQL × 3, Redis, CosmosDB, Storage Account, VNet.

### Módulo Warm Standby (DR — Opção B)

O Terraform está estruturado para levantar um ambiente espelho em `brazilsouth` via:

```bash
terraform apply -var="location=brazilsouth" -var="aks_location=brazilsouth" -var="pg_location=brazilsouth"
```

---

## 5. Containers e CI/CD

### Dockerfiles

Todos os serviços usam **build multi-stage** seguindo práticas DevSecOps:

**donation-service (Go):**
```
Stage 1 — builder: golang:1.24-alpine
  → go mod download → go build -ldflags="-s -w" (binário otimizado)

Stage 2 — runtime: gcr.io/distroless/static:nonroot
  → copia apenas o binário → usuário nonroot:nonroot → EXPOSE 8082
```

**ngo-service e volunteer-service (Python):**
```
Stage 1 — builder: python:3.12-alpine
  → pip install → sem cache

Stage 2 — runtime: python:3.12-alpine (mínimo)
  → copia dependências → usuário não-root → EXPOSE 808x
```

### Pipelines CI/CD (GitHub Actions)

**Repositório:** `1-DCLT-APPLICATIONS-FASE-5/.github/workflows/`

Fluxo de cada pipeline:

```
push na branch main
       ↓
checkout do código
       ↓
build da imagem Docker (multi-stage)
       ↓
Trivy scan — filesystem (SAST/SCA)
       ↓
Trivy scan — imagem final
       ↓
push para ACR (acrsolidarytechf5.azurecr.io)
       ↓
commit automático da nova tag no repo GitOps
       ↓
ArgoCD detecta mudança → sync automático → deploy no AKS
```

**Secrets necessários no GitHub:**

| Secret | Uso |
|---|---|
| `AZURE_CLIENT_ID` | Autenticação no ACR via OIDC |
| `AZURE_CLIENT_SECRET` | Credencial Azure |
| `AZURE_TENANT_ID` | Tenant Azure |
| `AZURE_SUBSCRIPTION_ID` | Subscription Azure |
| `GITOPS_TOKEN` | Commit automático no repo GitOps |

---

## 6. GitOps com ArgoCD

**Repositório:** `1-DCLT-GITOPS-FASE-5/`

O ArgoCD monitora este repositório e aplica qualquer mudança automaticamente no cluster, sem intervenção manual.

### AppProject `solidarytech`

Define as permissões do ArgoCD para o projeto:
- **Source repos permitidos:** GitHub GitOps, Helm charts (prometheus-community, grafana, vmware-tanzu)
- **Namespaces permitidos:** `solidarytech`, `monitoring`, `velero`, `kube-system`, `default`
- **Sync policy:** automated + selfHeal + prune

### Applications registradas

| Application | Chart / Source | Namespace | Sync | Health |
|---|---|---|---|---|
| `ngo-service` | repo GitOps | solidarytech | Synced | Healthy |
| `donation-service` | repo GitOps | solidarytech | Synced | Healthy |
| `volunteer-service` | repo GitOps | solidarytech | Synced | Healthy |
| `monitoring-stack` | kube-prometheus-stack 65.x | monitoring | Synced | Healthy |
| `loki-stack` | loki 6.x + promtail 6.x | monitoring | Synced | Healthy |
| `grafana-dashboards` | repo GitOps (ConfigMap) | monitoring | Synced | Healthy |
| `velero` | velero 6.7.0 | velero | Synced | Healthy |

### Estrutura de diretórios

```
1-DCLT-GITOPS-FASE-5/
├── apps/
│   ├── donation-service/
│   │   ├── deployment.yaml     # 2 réplicas, HPA, Datadog, probes
│   │   ├── service.yaml        # ClusterIP porta 8082
│   │   └── hpa.yaml            # min 2 / max 10 / CPU 70%
│   ├── ngo-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   └── volunteer-service/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── hpa.yaml
├── argocd-apps/
│   ├── app-donation.yaml
│   ├── app-ngo.yaml
│   ├── app-volunteer.yaml
│   ├── app-monitoring.yaml     # kube-prometheus-stack
│   ├── app-loki.yaml           # Loki + Promtail
│   ├── app-grafana.yaml        # Grafana standalone (ref)
│   ├── app-grafana-dashboards.yaml
│   └── app-velero.yaml
├── infra/
│   ├── argocd/
│   │   └── argocd-install.yaml # AppProject solidarytech
│   ├── monitoring/
│   │   ├── prometheus-values.yaml
│   │   ├── grafana-values.yaml
│   │   ├── grafana-dashboards-configmap.yaml
│   │   ├── grafana-secret.yaml
│   │   ├── loki-values.yaml
│   │   └── promtail-values.yaml
│   ├── namespace/
│   │   └── namespace.yaml
│   └── velero/
│       └── velero-install.yaml
└── documentacao/
    ├── README.md               # este arquivo
    └── roteiro-video.md
```

---

## 7. Observabilidade

### Stack completa rodando no namespace `monitoring`

| Componente | Versão/Chart | Função |
|---|---|---|
| **Prometheus** | kube-prometheus-stack 65.x | Coleta de métricas do cluster e dos serviços |
| **Grafana** | embutido no kube-prometheus-stack | Visualização — 3 dashboards customizados |
| **Loki** | loki 6.x (SingleBinary) | Agregação de logs dos pods |
| **Promtail** | promtail 6.x | Coleta de logs e envio ao Loki |
| **Datadog Agent** | (a instalar) | APM com Distributed Tracing e Watchdog |

### Coleta de métricas (Prometheus)

O Prometheus scrape os serviços automaticamente via annotations nos pods:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8082"
  prometheus.io/path: "/metrics"
```

O `additionalScrapeConfig` no `prometheus-values.yaml` garante que todos os pods do namespace `solidarytech` sejam descobertos e que o label `app` do pod seja mapeado para `service` nas métricas.

### Dashboards Grafana

**1. SRE — donation-service** (`uid: sre-donation`)
- Gauge: Taxa de Sucesso vs SLO 99,9%
- Stat: Error Budget restante (30 dias)
- Time series: Latência P50 / P95 / P99 com linha de threshold em 500ms
- Time series: RPS por status HTTP (2xx / 4xx / 5xx)
- Time series: CPU e Memória dos pods
- Stat: Pods disponíveis
- Time series: Reinicializações (CrashLoop detector)
- Time series: HPA réplicas desejadas vs atuais

**2. SolidaryTech — Overview** (`uid: solidarytech-overview`)
- RPS dos 3 serviços lado a lado
- Latência P99 dos 3 serviços em um único gráfico
- Taxa de erro dos 3 serviços
- CPU e Memória do namespace completo
- Tabela de status de pods

**3. FinOps — Consumo de Recursos** (`uid: finops-costs`)
- Bargauge: CPU Request vs Usage (rightsizing visual)
- Bargauge: Memória Request vs Usage
- Histórico 24h de CPU (baseline para rightsizing)
- Gauge: % CPU alocada vs capacidade dos nós
- Gauge: % Memória alocada vs capacidade dos nós

### Alertas (PrometheusRules)

| Alerta | Condição | Severidade |
|---|---|---|
| `DonationServiceErrorBudgetBurning` | Taxa de erro > 0,1% por 5min | critical |
| `DonationServiceHighLatency` | P99 > 500ms por 5min | warning |
| `DonationServiceDown` | `up == 0` por 1min | critical |
| `PodCrashLooping` | Restarts > 0 em 15min | warning |

Alertas são roteados via Alertmanager → Slack `#incidentes`.

### Coleta de logs (Loki + Promtail)

O Promtail roda como DaemonSet e coleta logs de todos os pods do namespace `solidarytech`, enriquecendo com labels:
- `app` — nome do serviço
- `namespace` — solidarytech
- `pod` — nome do pod
- `container` — nome do container

---

## 8. SRE — Confiabilidade e Golden Metrics

### SLIs e SLOs do donation-service

O donation-service é o **Caminho Crítico (Hot Path)** da plataforma. Uma falha aqui impede doações — impacto direto nas ONGs parceiras.

#### SLI 1 — Taxa de Sucesso

```promql
rate(http_requests_total{service="donation-service",status!~"5.."}[5m])
/ rate(http_requests_total{service="donation-service"}[5m]) * 100
```

**SLO:** ≥ 99,9% das requisições bem-sucedidas em janela de 30 dias  
**Error Budget:** 0,1% = ~43 minutos de downtime por mês

#### SLI 2 — Latência P99

```promql
histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket{service="donation-service"}[5m])
)
```

**SLO:** P99 ≤ 500ms  
**Justificativa:** Uma doação deve ser processada em menos de meio segundo para garantir boa experiência ao doador.

### Error Budget

O Error Budget é calculado em tempo real no dashboard Grafana:

```promql
(1 - (
  sum(increase(http_requests_total{service="donation-service",status=~"5.."}[30d]))
  / sum(increase(http_requests_total{service="donation-service"}[30d]))
)) / (1 - 0.999) * 100
```

Quando o Error Budget cai abaixo de 10%, o alerta `DonationServiceErrorBudgetBurning` dispara com severidade `critical`.

### MTTR (Mean Time To Recovery)

A stack de observabilidade reduz o MTTR da seguinte forma:

| Etapa | Ferramenta | Tempo estimado |
|---|---|---|
| Detecção | Prometheus → Alertmanager (alerta em 1-5min) | 1–5 min |
| Notificação | Slack `#incidentes` + Datadog Watchdog | < 1 min |
| Diagnóstico | Grafana APM + Loki logs + Datadog traces | 3–8 min |
| Mitigação | HPA auto-escala / ArgoCD selfHeal | automático |
| Resolução | Rollback via GitOps (commit no repo) | 2–5 min |
| **MTTR total** | | **~15 min** |

---

## 9. FinOps — Otimização Financeira

### Rightsizing dos Pods

Os recursos foram dimensionados com base nas Golden Metrics dos serviços:

| Serviço | CPU Request | CPU Limit | Mem Request | Mem Limit | Justificativa |
|---|---|---|---|---|---|
| `donation-service` | 250m | 500m | 256Mi | 512Mi | Hot path — Go compilado, alta concorrência |
| `ngo-service` | 100m | 250m | 128Mi | 256Mi | Carga baixa — CRUD simples |
| `volunteer-service` | 100m | 250m | 128Mi | 256Mi | Carga baixa — CosmosDB serverless |

### Forecast de Custos Mensais (Azure — centralus/eastus2)

| Recurso | Configuração | Custo estimado/mês |
|---|---|---|
| AKS — 2 nós Standard_D2s_v3 | centralus | ~$140 |
| PostgreSQL Flexible × 3 | B1ms, centralus | ~$45 |
| Redis Cache | Balanced_B0 | ~$15 |
| CosmosDB | Table API, Serverless | ~$5–20 |
| ACR | Basic | ~$5 |
| Storage Account | LRS, hot tier | ~$5 |
| **Total estimado** | | **~$215–230/mês** |

### Recomendações de Economia

1. **Spot Nodes para ngo-service e volunteer-service:** migrar os serviços de menor criticidade para node pool spot — economia de ~60% no custo de VM (~$84/mês)
2. **CosmosDB Serverless:** já está em uso — ideal para cargas imprevisíveis sem custo fixo
3. **ACR Basic:** suficiente para o volume atual; evitar upgrade para Standard desnecessariamente
4. **HPA conservador no scale-down:** janela de 300s evita thrashing, mas garante escalar para baixo após picos

---

## 10. AIOps e ITSM — Gestão Preditiva de Incidentes

### Funcionalidades de AIOps (Datadog)

- **Watchdog:** detecção automática de anomalias comportamentais sem configuração manual — identifica desvios em latência, taxa de erro e throughput
- **APM Anomaly Detection:** modelo de baseline automático para o donation-service — alerta quando o comportamento sai do padrão histórico
- **Distributed Tracing:** rastreamento de uma requisição do início ao fim, cruzando todos os serviços

### Fluxo de Vida de um Incidente (ITSM)

```
1. DETECÇÃO
   └─ Prometheus detecta violação de SLO
      └─ Datadog Watchdog detecta anomalia comportamental

2. ALERTA
   └─ Alertmanager → Slack #incidentes (< 1 min)
      └─ Datadog Monitor → Datadog Incident criado automaticamente

3. TRIAGEM (on-call acionado)
   └─ Grafana: dashboard SRE mostra Error Budget consumido
   └─ Datadog APM: trace da requisição com falha identificado
   └─ Loki: logs do pod no momento do erro

4. MITIGAÇÃO AUTOMÁTICA
   └─ HPA escala donation-service (se causa for carga)
   └─ ArgoCD selfHeal corrige drift de configuração
   └─ Kubernetes liveness probe reinicia pod travado

5. RESOLUÇÃO
   └─ Correção via commit no repo GitOps
   └─ ArgoCD detecta e aplica em < 2 min
   └─ Alerta resolvido automaticamente (resolve_timeout: 5min)

6. POST-MORTEM
   └─ Documento no Datadog Incident (causa raiz + timeline + ações)
   └─ PrometheusRule ajustada se necessário

7. COMUNICAÇÃO
   └─ Status page atualizado
   └─ Comunicado às ONGs parceiras via e-mail
```

---

## 11. Disaster Recovery e Continuidade de Negócios

### Plano de Continuidade de Negócios (PCN)

#### Valores críticos do donation-service

| Métrica | Valor | Justificativa |
|---|---|---|
| **RTO** (Recovery Time Objective) | **15 minutos** | Tempo máximo tolerável sem processar doações |
| **RPO** (Recovery Point Objective) | **1 hora** | Máximo de dados de doações que podem ser perdidos |

#### Cenários cobertos

| Cenário | Estratégia | RTO esperado |
|---|---|---|
| Pod crashando | Liveness probe + restart automático | < 1 min |
| Nó do AKS com falha | topologySpreadConstraints + novo nó via VMSS | 3–5 min |
| Região Azure indisponível | Velero restore em nova região | ~15 min |
| Corrupção de dados no PostgreSQL | Backup automático (geo-redundant) + restore | ~30–60 min |

### Estratégia DR — Velero (Opção A: Cross-Region Backup)

**Velero** está instalado no cluster via ArgoCD e configurado para:

- **Backup diário:** todos os dias às 02:00 UTC
- **Escopo:** namespace `solidarytech` completo (manifestos + volumes)
- **Destino:** Azure Blob Storage (`stsolidarytechvelero`) — região `brazilsouth`
- **Retenção:** 30 dias (720h)

**Schedule configurado:**
```yaml
schedule: "0 2 * * *"
includedNamespaces: [solidarytech]
ttl: 720h0m0s
```

**Procedimento de restore:**
```bash
# 1. Listar backups disponíveis
velero backup get

# 2. Restaurar o backup mais recente
velero restore create --from-backup <nome-do-backup>

# 3. Acompanhar status
velero restore describe <nome-do-restore>
```

### Estratégia DR — Warm Standby via Terraform (Opção B)

O Terraform está parametrizado para levantar um ambiente espelho em outra região com um único comando:

```bash
# Levantar ambiente espelho em brazilsouth
terraform apply \
  -var="location=brazilsouth" \
  -var="aks_location=brazilsouth" \
  -var="pg_location=brazilsouth"
```

O PostgreSQL do donation-service está configurado com `geo_redundant_backup_enabled = true`, garantindo replicação automática dos dados para a região secundária.
