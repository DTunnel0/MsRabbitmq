# MsRabbitmq

## Topologia

O broker sobe com bootstrap explícito:

- [bootstrap.sh](/home/dutra/DTunnel/MsRabbitmq/bootstrap.sh)
- [rabbitmq.conf](/home/dutra/DTunnel/MsRabbitmq/rabbitmq.conf)
- [definitions.json](/home/dutra/DTunnel/MsRabbitmq/definitions.json)

No boot ele:

- inicia o broker
- importa `definitions.json`
- reaplica o usuário admin definido por `RABBITMQ_DEFAULT_USER` e `RABBITMQ_DEFAULT_PASS`
- reaplica as permissões do admin em `/`

Isso evita o caso de volume antigo com senha divergente e também cria:

- exchanges `dtunnel.events`, `dtunnel.retry`, `dtunnel.requeue`, `dtunnel.dlq`
- filas principais, `.retry` e `.dlq` dos micros Python

O `MsDevice` nao usa mais RabbitMQ para `update_last_seen`; esse fluxo foi movido para Redis.

## Deploy

Docker Compose:

```bash
docker compose up -d
```

Docker Swarm:

```bash
docker stack deploy -c docker-stack.yml ms_rabbitmq
```

## Validação

Depois de subir, confira:

```bash
docker exec rabbitmq rabbitmqctl list_exchanges name type
docker exec rabbitmq rabbitmqctl list_queues name
docker exec rabbitmq rabbitmqctl list_bindings
```
