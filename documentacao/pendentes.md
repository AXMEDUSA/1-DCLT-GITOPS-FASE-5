# Pendências — Entrega Fase 5 SolidaryTech

Atualizado em: 2026-06-15

---

## CRÍTICO — sem isso a entrega está incompleta

### 1. Datadog Agent
**Status:** não instalado  
**O que falta:**
- Obter a API key do grupo (variável `DD_API_KEY`)
- Criar manifest `infra/datadog/datadog-agent.yaml` (DaemonSet ou Helm values via ArgoCD)
- Injetar variáveis de APM nos 3 deployments: `DD_SERVICE`, `DD_ENV`, `DD_VERSION`, `DD_AGENT_HOST`
- Validar no Datadog SaaS: APM → Services mostrando `ngo-service`, `donation-service`, `volunteer-service`
- Adicionar prints de evidência na seção 13 do README

**Comando rápido depois de ter a API key:**
```bash
kubectl create secret generic datadog-secret \
  --from-literal=api-key=<DD_API_KEY> \
  -n monitoring
```

---

## IMPORTANTE — entrega mais fraca sem isso

### 2. Vídeo de demonstração
**Status:** roteiro pronto em `documentacao/roteiro-video.md`  
**O que falta:**
- Gravar seguindo o roteiro (duração sugerida: 3–5 min)
- Cobrir: UI funcionando, fluxo E2E, Grafana dashboard, Velero restore, ArgoCD selfHeal
- Fazer upload e adicionar link no README

### 3. PCN como documento separado
**Status:** conteúdo já está na seção 11 do README  
**O que falta (opcional):**
- Extrair para `documentacao/PCN.md` se o professor exigir documento formal separado
- O conteúdo atual no README já cobre RTO/RPO, cenários e procedimentos

---

## CONCLUÍDO — não mexer

| Item | Status |
|---|---|
| CORS em todos os 3 microsserviços | ✅ |
| nginx porta 8080 (non-root) | ✅ |
| ArgoCD selfHeal + GitOps | ✅ |
| Grafana dashboard com métricas reais | ✅ |
| Velero backup/restore demonstrado | ✅ |
| Evidências UI (12 screenshots seção 12) | ✅ |
| Evidências Velero DR (8 screenshots seção 11) | ✅ |
| Prometheus + Loki + Grafana no cluster | ✅ |
| HPA configurado nos 3 serviços | ✅ |
| Terraform IaC documentado | ✅ |
| Script run-ui.sh com port-forward automático | ✅ |
| README completo com todas as seções | ✅ |
