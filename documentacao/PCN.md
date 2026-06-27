# Plano de Continuidade de Negócios (PCN)
## SolidaryTech — Hackathon FIAP Fase 5

**Versão:** 1.0  
**Data:** 2026-06-15  
**Classificação:** Executivo  

---

## 1. Objetivo

Este documento define as diretrizes, procedimentos e métricas de recuperação para garantir a continuidade operacional da plataforma SolidaryTech em cenários de falha parcial ou total da infraestrutura. O foco principal é o **donation-service**, classificado como Caminho Crítico (Hot Path) da operação.

---

## 2. Escopo

| Serviço | Criticidade | Banco de Dados |
|---|---|---|
| donation-service | **CRÍTICO** — Hot Path | PostgreSQL (Azure Database) |
| ngo-service | Alta | PostgreSQL (Azure Database) |
| volunteer-service | Média | Azure Cosmos DB |

---

## 3. Objetivos de Recuperação

### 3.1 Valores críticos — donation-service

| Métrica | Valor | Justificativa |
|---|---|---|
| **RTO** (Recovery Time Objective) | **15 minutos** | Tempo máximo tolerável sem processar doações |
| **RPO** (Recovery Point Objective) | **1 hora** | Máximo de dados de doações que podem ser perdidos |

### 3.2 Valores complementares

| Serviço | RTO | RPO |
|---|---|---|
| ngo-service | 30 min | 24h |
| volunteer-service | 60 min | 24h |

---

## 4. Cenários de Falha e Estratégias

| Cenário | Probabilidade | Estratégia de Resposta | RTO Esperado |
|---|---|---|---|
| Pod crashando | Alta | Liveness probe + restart automático (Kubernetes) | < 1 min |
| Nó do AKS com falha | Média | topologySpreadConstraints + novo nó via VMSS | 3–5 min |
| Falha de deployment (config errada) | Média | ArgoCD selfHeal reverte para último estado Git | < 2 min |
| Região Azure indisponível | Baixa | Velero restore em nova região | ~15 min |
| Corrupção de dados no PostgreSQL | Baixa | Backup geo-redundante + restore | ~30–60 min |

---

## 5. Estratégia de DR — Opção A: Cross-Region Backup com Velero

**Velero** está instalado no cluster AKS via ArgoCD e configurado para backup automático:

- **Frequência:** diária às 02:00 UTC (`0 2 * * *`)
- **Escopo:** namespace `solidarytech` completo (manifestos Kubernetes + volumes PVC)
- **Destino:** Azure Blob Storage (`stsolidarytechvelero`) — região `brazilsouth`
- **Retenção:** 30 dias (720h)

### Procedimento de Restore

```bash
# 1. Listar backups disponíveis
velero backup get

# 2. Criar restore a partir do backup desejado
velero restore create restore-$(date +%Y%m%d%H%M) --from-backup <nome-do-backup>

# 3. Acompanhar status
velero restore describe <nome-do-restore>

# 4. Verificar pods restaurados
kubectl get pods -n solidarytech
```

### Evidência de Restore em Produção

Restore executado em 2026-06-15 — **37 itens restaurados em 2 segundos** (12:19:36 → 12:19:38), 0 erros.

---

## 6. Estratégia de DR — Opção B: Warm Standby via Terraform

O Terraform está parametrizado para levantar um ambiente espelho em outra região com um único comando:

```bash
terraform apply \
  -var="location=brazilsouth" \
  -var="aks_location=brazilsouth" \
  -var="pg_location=brazilsouth"
```

O PostgreSQL do donation-service está configurado com `geo_redundant_backup_enabled = true`, garantindo replicação automática dos dados para a região secundária.

---

## 7. Camadas de Resiliência Implementadas

### 7.1 Alta Disponibilidade no Cluster

- **HPA (Horizontal Pod Autoscaler):** escala automática baseada em CPU/memória
- **topologySpreadConstraints:** pods distribuídos entre nós diferentes do AKS
- **Liveness e Readiness Probes:** detecção e reinício automático de pods com falha
- **Resource Limits:** requests e limits definidos para todos os containers (Rightsizing)

### 7.2 GitOps com Self-Healing

- **ArgoCD selfHeal:** qualquer desvio do estado desejado (Git) é corrigido automaticamente em < 2 minutos
- **Rollback automático:** basta reverter o commit no repositório GitOps

### 7.3 Banco de Dados

- PostgreSQL (Azure Database for PostgreSQL Flexible Server) com `geo_redundant_backup_enabled = true`
- Backups automáticos diários gerenciados pela Azure
- Azure Cosmos DB para volunteer-service com replicação nativa

---

## 8. Monitoramento e Alertas

| Camada | Ferramenta | O que monitora |
|---|---|---|
| Infraestrutura | Prometheus + Grafana | CPU, Memória, Rede, Pods, HPA |
| Logs | Loki + Promtail | Logs de todos os containers |
| APM / Tracing | Datadog | Traces distribuídos, anomalias (Watchdog) |
| Incidentes | Datadog Monitors | Alertas automáticos + criação de incidentes |

---

## 9. Comunicação em Incidentes

| Fase | Ação | Responsável |
|---|---|---|
| Detecção | Alerta automático via Datadog Watchdog | Sistema |
| Triagem (< 5 min) | Análise no Grafana + Loki + Datadog APM | On-call |
| Contenção (< 15 min) | Rollback via Git ou restore Velero | Engenharia |
| Comunicação | Notificação às ONGs parceiras afetadas | Produto |
| Post-Mortem | Documento com causa raiz, timeline e ações | Engenharia |

---

## 10. Responsáveis

| Papel | Responsabilidade |
|---|---|
| Engenharia de Plataforma | Manutenção do cluster, backups e pipelines |
| SRE | Monitoramento contínuo, SLOs e resposta a incidentes |
| Produto | Comunicação externa com ONGs e doadores |

---

*Documento gerado para o Hackathon FIAP Fase 5 — SolidaryTech.*
