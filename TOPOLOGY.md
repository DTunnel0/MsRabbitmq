# Topologia de eventos

Todos os eventos de domínio usam o exchange tópico durável `dtunnel.events`.
Cada consumidor possui fila principal, `.retry` e `.dlq`; a fila de retry retorna
ao destino pela exchange `dtunnel.requeue`.

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

## Ciclo de retry

Cada fila principal usa o mesmo nome como routing key nas exchanges auxiliares:

1. falha transitória publica em `dtunnel.retry` com TTL;
2. o dead-letter da fila `.retry` publica em `dtunnel.requeue`;
3. `dtunnel.requeue` devolve à fila principal;
4. ao esgotar tentativas, a mensagem segue para `.dlq` via `dtunnel.dlq`.

O arquivo [definitions.json](./definitions.json) é a fonte executável da
topologia. Execute `python3 update_commerce_topology.py` após ajustes no conjunto
de filas do comércio.
