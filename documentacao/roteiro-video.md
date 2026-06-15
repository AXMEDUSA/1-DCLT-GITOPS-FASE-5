# Roteiro — Vídeo de Demonstração
## SolidaryTech | Hackathon FIAP Fase 5 | Equipe DCLT

> Duração total: 15 a 20 minutos  
> Formato: Pitch Executivo + Demo Técnica

---

## PARTE 1 — PITCH EXECUTIVO (5–7 min)

### [0:00 – 1:30] Abertura e Contexto de Negócio

**Fala sugerida:**
> "A SolidaryTech conecta ONGs a doadores e voluntários em todo o Brasil. Depois de ganhar destaque em rede nacional, a plataforma passou a enfrentar picos de acesso imprevisíveis. Nossa missão foi construir uma infraestrutura que garanta que **nenhuma doação seja perdida**, com custos controlados e resposta a incidentes em minutos — não em horas."

**Mostrar na tela:**
- Diagrama de arquitetura geral (slide ou imagem do README)
- Os 3 microsserviços e suas responsabilidades

---

### [1:30 – 3:00] Arquitetura e Decisões Técnicas

**Fala sugerida:**
> "Escolhemos Azure como cloud principal, com AKS como orquestrador Kubernetes. Toda a infraestrutura é provisionada via Terraform — nenhum recurso foi criado manualmente no console. O deploy é feito exclusivamente via ArgoCD, garantindo rastreabilidade e rollback em segundos."

**Mostrar na tela:**
- Tabela de decisões técnicas (cloud, GitOps, APM, DR)
- Print do portal Azure mostrando os recursos criados com as tags FinOps

---

### [3:00 – 4:30] SLOs e Garantias às ONGs

**Fala sugerida:**
> "Para as ONGs parceiras, estabelecemos acordos claros de nível de serviço. O donation-service — nosso caminho crítico — tem SLO de 99,9% de disponibilidade e latência P99 abaixo de 500ms. Isso representa menos de 43 minutos de downtime por mês. E temos um Error Budget monitorado em tempo real."

**Mostrar na tela:**
- Dashboard SRE no Grafana aberto (gauge de Taxa de Sucesso e Error Budget)
- Tabela de SLIs e SLOs

---

### [4:30 – 5:30] FinOps — Custo Justificado

**Fala sugerida:**
> "O orçamento da ONG é limitado. Por isso, cada recurso foi dimensionado e tagueado. O custo estimado é de R$ 1.100/mês, e já identificamos uma otimização imediata: migrar os serviços de menor criticidade para Spot Nodes, reduzindo o custo de VM em 60%."

**Mostrar na tela:**
- Dashboard FinOps no Grafana (rightsizing — request vs usage)
- Print do Terraform mostrando as tags FinOps

---

### [5:30 – 7:00] Disaster Recovery e Continuidade

**Fala sugerida:**
> "Se a nuvem cair, as doações não param. Temos RTO de 15 minutos e RPO de 1 hora para o donation-service. O Velero realiza backup diário de todo o cluster para a região Brazil South. E com um único comando Terraform, subimos um ambiente espelho em outra região."

**Mostrar na tela:**
- Schedule do Velero configurado
- Comando `terraform apply -var="location=brazilsouth"` (pode ser um slide)

---

## PARTE 2 — DEMO TÉCNICA (8–13 min)

### [7:00 – 8:30] CI/CD — Pipeline rodando no GitHub Actions

**O que mostrar:**
1. Abrir o GitHub → `1-DCLT-APPLICATIONS-FASE-5` → aba **Actions**
2. Mostrar um pipeline em execução ou o histórico de execuções
3. Clicar em uma run e mostrar os steps:
   - Build da imagem Docker
   - Trivy scan (filesystem + imagem) — mostrar o relatório de vulnerabilidades
   - Push para o ACR
   - Commit automático no repo GitOps com a nova tag da imagem

**Fala sugerida:**
> "Qualquer push na main dispara o pipeline. O Trivy escaneia vulnerabilidades antes do push. Se passar, a imagem vai para o ACR e o ArgoCD detecta a mudança automaticamente."

---

### [8:30 – 10:00] ArgoCD — GitOps em ação

**O que mostrar:**
1. Abrir a UI do ArgoCD (`kubectl port-forward svc/argocd-server -n argocd 8080:443`)
2. Mostrar a lista de Applications com status Synced/Healthy
3. Clicar em `donation-service` e mostrar:
   - Árvore de recursos (Deployment, Service, HPA)
   - Histórico de syncs
   - Self-heal: fazer uma mudança manual no cluster e mostrar o ArgoCD revertendo

**Fala sugerida:**
> "O ArgoCD monitora o repositório Git como fonte da verdade. Qualquer drift é corrigido automaticamente. Aqui vemos os 7 applications todos Synced e Healthy."

---

### [10:00 – 11:30] Terraform — Infraestrutura como Código

**O que mostrar:**
1. Mostrar o terminal com `terraform state list` — listar os recursos criados
2. Mostrar o arquivo `tags.tf` — política de tags FinOps
3. Mostrar o portal Azure com um recurso aberto e as tags visíveis:
   - `Project: SolidaryTech`
   - `Environment: Production`
   - `CostCenter: NGO-Core`
   - `ManagedBy: Terraform`

**Fala sugerida:**
> "Todo o ambiente foi criado com Terraform. Nenhum clique no console. E todos os recursos têm tags obrigatórias para rastreabilidade de custo."

---

### [11:30 – 13:30] Observabilidade — Prometheus, Grafana e Loki

**O que mostrar:**
1. Abrir o Grafana (`kubectl port-forward svc/monitoring-stack-grafana -n monitoring 3000:80`)
2. **Dashboard SRE — donation-service:**
   - Apontar o gauge de Taxa de Sucesso e explicar o SLO de 99,9%
   - Mostrar o Error Budget restante
   - Mostrar o gráfico de latência P99 com a linha de threshold em 500ms
   - Mostrar o RPS com separação por status HTTP
3. **Dashboard Overview:**
   - Mostrar os 3 serviços lado a lado
4. **Dashboard FinOps:**
   - Mostrar CPU/Memória request vs usage (rightsizing)
5. Abrir o **Loki** (Explore no Grafana) e fazer uma query de logs do donation-service:
   ```
   {namespace="solidarytech", app="donation-service"}
   ```

**Fala sugerida:**
> "Aqui está nosso painel SRE. O Error Budget está em X%, a latência P99 está abaixo de 500ms. No painel FinOps, vemos que estamos usando apenas Y% do CPU alocado — o que indica oportunidade de rightsizing."

---

### [13:30 – 15:00] Datadog APM — Distributed Tracing e Watchdog

**O que mostrar:**
1. Abrir o Datadog → APM → Services
2. Mostrar os 3 serviços instrumentados (donation-service, ngo-service, volunteer-service)
3. Clicar em um trace do donation-service e mostrar o distributed trace
4. Mostrar o **Watchdog** → alertas de anomalia detectados automaticamente
5. Mostrar um Monitor de latência configurado

**Fala sugerida:**
> "O Datadog APM nos dá visibilidade de ponta a ponta em cada requisição. O Watchdog detectou automaticamente esta anomalia sem nenhuma configuração manual — isso é AIOps na prática."

---

### [15:00 – 16:30] Disaster Recovery — Velero em ação

**O que mostrar:**
1. Mostrar o schedule do Velero:
   ```bash
   kubectl get schedules -n velero
   velero backup get
   ```
2. Mostrar o último backup criado e seu status (`Completed`)
3. Mostrar o Storage Account no Azure com os arquivos de backup
4. Demonstrar o comando de restore (pode ser em ambiente de teste):
   ```bash
   velero restore create --from-backup <nome-do-backup>
   velero restore describe <nome-do-restore>
   ```

**Fala sugerida:**
> "O Velero faz backup diário do cluster para o Brazil South. Se precisarmos restaurar, executamos um único comando e em menos de 15 minutos o ambiente está de volta — dentro do nosso RTO."

---

### [16:30 – 18:00] Encerramento

**Fala sugerida:**
> "Em resumo: entregamos uma plataforma que não apenas funciona, mas que **comprova** o que faz. Terraform garante que a infra é reproduzível. ArgoCD garante que o deploy é auditável. Prometheus e Grafana garantem que sabemos o que está acontecendo antes do usuário perceber. E o Velero garante que, se tudo der errado, voltamos em 15 minutos."

**Mostrar na tela (quadro final):**
- Checklist de entrega preenchido
- Diagrama de arquitetura completo

---

## Checklist antes de gravar

### Ambiente
- [ ] `kubectl get pods -n solidarytech` — todos Running
- [ ] `kubectl get pods -n monitoring` — todos Running
- [ ] `kubectl get applications -n argocd` — todos Synced/Healthy
- [ ] Grafana acessível via port-forward (porta 3000)
- [ ] ArgoCD UI acessível via port-forward (porta 8080)
- [ ] Datadog APM mostrando os 3 serviços

### Demonstrações prontas
- [ ] GitHub Actions — ter uma run recente com todos os steps visíveis
- [ ] Velero — ter pelo menos 1 backup com status `Completed`
- [ ] Grafana — dashboards com dados reais (não zerados)
- [ ] Datadog — pelo menos 1 trace de ponta a ponta visível
- [ ] Azure Portal — print dos recursos com tags FinOps visíveis

### Slides de apoio (sugeridos)
- [ ] Diagrama de arquitetura
- [ ] Tabela de SLOs
- [ ] Forecast de custos
- [ ] Fluxo ITSM de incidente
- [ ] PCN com RTO/RPO

---

## Dicas de gravação

- Resolução mínima: 1920×1080
- Fonte do terminal: aumentar para pelo menos 18pt
- Fechar notificações do sistema antes de gravar
- Ter os port-forwards já abertos antes de começar
- Deixar as abas do browser já abertas na ordem do roteiro
- Terminal: usar `tmux` ou ter múltiplos terminais já posicionados
