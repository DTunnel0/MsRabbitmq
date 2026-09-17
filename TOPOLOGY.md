# Topologia de eventos

Todos os eventos de domínio usam o exchange tópico durável `dtunnel.events`.
Cada consumidor possui fila principal, retry e DLQ. A fila de retry retorna ao
destino pela exchange `dtunnel.requeue`. Os consumidores do `MsVPS` usam cinco
filas de atraso; os demais usam `.retry` com expiração definida na mensagem.

## Comércio v2

```text
MsPayment
  payment.approved ───────────┐
  payment.cancelled ──────────┼─> MsPlan/Commerce
  payment.refund.succeeded ───┘
                                   │
                                   ├─ entitlement.granted
                                   └─ entitlement.revoked
                                         ├─> MsUser (account.*)
                                         └─> MsProtocolToken (protocol-token)
```

Filas financeiras consumidas exclusivamente pelo `MsPlan`:

- `ms_commerce.payment.approved`
- `ms_commerce.payment.cancelled`
- `ms_commerce.payment.refunded`

Filas de projeção de acesso:

- `ms_user.entitlement.granted`
- `ms_user.entitlement.revoked`
- `ms_protocol_token.entitlement.events`, ligada aos dois eventos e filtrada
  internamente por `product_code=protocol-token`.

Os eventos antigos `plan.purchase.*` e as filas `ms_user.payment.*` não existem
mais. Serviços consumidores nunca concedem acesso diretamente a partir de um
evento financeiro.

## Projeção de servidores para Edge

O `MsVPS` publica `vps.server.snapshot.v1` pelo outbox. O `MsConfig` mantém uma
projeção mínima e idempotente pela fila `ms_config.vps.server.snapshot.v1`, com
retry e DLQ próprios. O evento carrega apenas identidade, proprietário, nome,
host público, estado e data; credenciais e fingerprints SSH não fazem parte do
contrato.

## Projeções de usuário

`MsAppConfig`, `MsConfig` e `MsText` consomem criação, atualização, remoção,
sincronização e alteração dos recursos herdados por membros. `MsPayment` consome
criação, atualização, remoção e sincronização. Cada projeção possui fila isolada,
retry e DLQ.

## Operações VPS

O `MsVPS` usa três filas principais:

- `ms_vps.action.requested.v1` para execução das operações;
- `ms_vps.action.completed.v1` para persistência dos resultados;
- `ms_vps.state.changed.v1` para a projeção entregue ao SSE.

Cada uma possui DLQ e retries de 5, 10, 20, 40 e 60 segundos.

## Ciclo de retry

Cada fila principal usa o mesmo nome como routing key nas exchanges auxiliares:

1. falha transitória publica em `dtunnel.retry` com TTL;
2. o dead-letter da fila `.retry` publica em `dtunnel.requeue`;
3. `dtunnel.requeue` devolve à fila principal;
4. ao esgotar tentativas, a mensagem segue para `.dlq` via `dtunnel.dlq`.

O arquivo [definitions.json](./definitions.json) é a fonte executável da
topologia. Execute `python3 update_topology.py` após qualquer ajuste em
consumidores, filas ou routing keys. O bootstrap remove apenas as filas
explicitamente listadas em [obsolete-queues.txt](./obsolete-queues.txt).
