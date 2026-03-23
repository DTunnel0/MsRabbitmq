# RabbitMQ Topology

## Objetivo

Padronizar o uso do RabbitMQ entre os micros do DTunnel para evitar:

- perda silenciosa de mensagem
- retry misturado entre consumidores diferentes
- DLQ compartilhada de forma implícita
- acoplamento ao `amq.direct`

## Problemas Do Modelo Atual

- os micros publicam direto no `amq.direct`
- as filas e bindings só nascem quando o consumer sobe
- a mesma routing key pode atender vários consumidores, mas cada fila cria sua topologia localmente
- as mensagens publicadas não usam persistência

## Desenho Proposto

### Exchanges

- `dtunnel.events`
  - tipo: `topic`
  - uso: eventos de domínio

- `dtunnel.retry`
  - tipo: `topic`
  - uso: reentrega por consumidor

- `dtunnel.dlq`
  - tipo: `topic`
  - uso: dead-letter final por consumidor

- `dtunnel.commands`
  - tipo: `topic`
  - uso: filas internas de trabalho pontual

## Regras De Nome

### Routing Keys De Evento

Usar `dominio.acao` ou `dominio.subdominio.acao`.

Exemplos:

- `user.created`
- `user.updated`
- `user.deleted`
- `payment.approved`
- `payment.cancelled`
- `plan.purchase.approved`
- `plan.purchase.cancelled`

### Filas

Fila principal:

- `<service>.<event>`

Fila de retry:

- `<service>.<event>.retry`

Fila de DLQ:

- `<service>.<event>.dlq`

Exemplos:

- `ms_payment.user.created`
- `ms_payment.user.created.retry`
- `ms_payment.user.created.dlq`

- `ms_user.payment.approved`
- `ms_user.payment.approved.retry`
- `ms_user.payment.approved.dlq`

## Eventos Atuais Do Sistema

### Publicados Pelo MsUser

- `user.created`
- `user.updated`
- `user.deleted`
- `plan.purchase.approved`
- `plan.purchase.cancelled`

### Publicados Pelo MsPayment

- `payment.approved`
- `payment.cancelled`

### Uso Interno Do MsDevice

Isso hoje se comporta mais como comando do que evento:

- `device.last_seen.update`

Esse fluxo deve usar `dtunnel.commands`, não `dtunnel.events`.

## Consumidores Atuais

### Eventos `user.*`

Consumidos por:

- `MsPayment`
- `MsConfig`
- `MsAppConfig`
- `MsText`

Filas propostas:

- `ms_payment.user.created`
- `ms_payment.user.updated`
- `ms_payment.user.deleted`

- `ms_config.user.created`
- `ms_config.user.updated`
- `ms_config.user.deleted`

- `ms_app_config.user.created`
- `ms_app_config.user.updated`
- `ms_app_config.user.deleted`

- `ms_text.user.created`
- `ms_text.user.updated`
- `ms_text.user.deleted`

### Eventos `payment.*`

Consumidos por:

- `MsUser`

Filas propostas:

- `ms_user.payment.approved`
- `ms_user.payment.cancelled`

### Eventos `plan.purchase.*`

Consumidos por:

- `MsPlan`

Filas propostas:

- `ms_plan.plan.purchase.approved`
- `ms_plan.plan.purchase.cancelled`

## Binding Exato

### Exchange `dtunnel.events`

- `user.created` -> `ms_payment.user.created`
- `user.created` -> `ms_config.user.created`
- `user.created` -> `ms_app_config.user.created`
- `user.created` -> `ms_text.user.created`

- `user.updated` -> `ms_payment.user.updated`
- `user.updated` -> `ms_config.user.updated`
- `user.updated` -> `ms_app_config.user.updated`
- `user.updated` -> `ms_text.user.updated`

- `user.deleted` -> `ms_payment.user.deleted`
- `user.deleted` -> `ms_config.user.deleted`
- `user.deleted` -> `ms_app_config.user.deleted`
- `user.deleted` -> `ms_text.user.deleted`

- `payment.approved` -> `ms_user.payment.approved`
- `payment.cancelled` -> `ms_user.payment.cancelled`

- `plan.purchase.approved` -> `ms_plan.plan.purchase.approved`
- `plan.purchase.cancelled` -> `ms_plan.plan.purchase.cancelled`

### Exchange `dtunnel.retry`

Binding por fila consumidora:

- `ms_payment.user.created` -> `ms_payment.user.created.retry`
- `ms_payment.user.updated` -> `ms_payment.user.updated.retry`
- `ms_payment.user.deleted` -> `ms_payment.user.deleted.retry`

- `ms_config.user.created` -> `ms_config.user.created.retry`
- `ms_config.user.updated` -> `ms_config.user.updated.retry`
- `ms_config.user.deleted` -> `ms_config.user.deleted.retry`

- `ms_app_config.user.created` -> `ms_app_config.user.created.retry`
- `ms_app_config.user.updated` -> `ms_app_config.user.updated.retry`
- `ms_app_config.user.deleted` -> `ms_app_config.user.deleted.retry`

- `ms_text.user.created` -> `ms_text.user.created.retry`
- `ms_text.user.updated` -> `ms_text.user.updated.retry`
- `ms_text.user.deleted` -> `ms_text.user.deleted.retry`

- `ms_user.payment.approved` -> `ms_user.payment.approved.retry`
- `ms_user.payment.cancelled` -> `ms_user.payment.cancelled.retry`

- `ms_plan.plan.purchase.approved` -> `ms_plan.plan.purchase.approved.retry`
- `ms_plan.plan.purchase.cancelled` -> `ms_plan.plan.purchase.cancelled.retry`

### Exchange `dtunnel.dlq`

Binding por fila consumidora:

- `ms_payment.user.created` -> `ms_payment.user.created.dlq`
- `ms_payment.user.updated` -> `ms_payment.user.updated.dlq`
- `ms_payment.user.deleted` -> `ms_payment.user.deleted.dlq`

- `ms_config.user.created` -> `ms_config.user.created.dlq`
- `ms_config.user.updated` -> `ms_config.user.updated.dlq`
- `ms_config.user.deleted` -> `ms_config.user.deleted.dlq`

- `ms_app_config.user.created` -> `ms_app_config.user.created.dlq`
- `ms_app_config.user.updated` -> `ms_app_config.user.updated.dlq`
- `ms_app_config.user.deleted` -> `ms_app_config.user.deleted.dlq`

- `ms_text.user.created` -> `ms_text.user.created.dlq`
- `ms_text.user.updated` -> `ms_text.user.updated.dlq`
- `ms_text.user.deleted` -> `ms_text.user.deleted.dlq`

- `ms_user.payment.approved` -> `ms_user.payment.approved.dlq`
- `ms_user.payment.cancelled` -> `ms_user.payment.cancelled.dlq`

- `ms_plan.plan.purchase.approved` -> `ms_plan.plan.purchase.approved.dlq`
- `ms_plan.plan.purchase.cancelled` -> `ms_plan.plan.purchase.cancelled.dlq`

## Retry E DLQ

### Main Queue

- fila durável
- consume manual com `ack`
- `prefetch_count` por consumidor

### Retry Queue

- fila durável
- TTL por mensagem no publish
- `x-dead-letter-exchange=dtunnel.events`
- `x-dead-letter-routing-key=<evento original>`

Exemplo:

- fila: `ms_payment.user.created.retry`
- republish: `dtunnel.retry` com routing key `ms_payment.user.created`
- volta para `dtunnel.events` com routing key `user.created`

### DLQ

- fila durável
- publish final em `dtunnel.dlq`
- routing key da própria fila consumidora

Exemplo:

- exchange: `dtunnel.dlq`
- routing key: `ms_payment.user.created`
- fila: `ms_payment.user.created.dlq`

## Publicação

Todo publish deve usar:

- `delivery_mode=2`
- `content_type=application/json`
- `mandatory=True`
- `message_id`
- `correlation_id` quando existir

## Regras Operacionais

- fila pertence ao consumidor, não ao publisher
- evento pertence ao domínio, não ao micro
- retry e DLQ pertencem à fila consumidora
- topologia deve existir antes do primeiro publish
- `MsDevice` deve sair do modelo atual de discard após retry e entrar nesse padrão, ou ficar explicitamente em `dtunnel.commands`

## Migração Do Modelo Atual

### Atual

- exchange implícita: `amq.direct`
- routing keys:
  - `user_created`
  - `user_updated`
  - `user_deleted`
  - `payment_approved`
  - `payment_cancelled`
  - `plan_purchase_approved`
  - `plan_purchase_cancelled`

### Alvo

- exchange: `dtunnel.events`
- routing keys:
  - `user.created`
  - `user.updated`
  - `user.deleted`
  - `payment.approved`
  - `payment.cancelled`
  - `plan.purchase.approved`
  - `plan.purchase.cancelled`

## Ordem Recomendada

1. declarar exchanges e filas novas
2. publicar duplicado por um período curto
3. migrar consumers para as filas novas
4. validar backlog, retry e DLQ
5. desligar o modelo antigo
