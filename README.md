# MsRabbitmq

## Topologia

O broker sobe com a topologia carregada automaticamente por:

- [rabbitmq.conf](/home/dutra/DTunnel/MsRabbitmq/rabbitmq.conf)
- [definitions.json](/home/dutra/DTunnel/MsRabbitmq/definitions.json)

Isso cria:

- exchanges `dtunnel.events`, `dtunnel.retry`, `dtunnel.dlq`, `dtunnel.commands`
- filas principais, `.retry` e `.dlq` dos micros Python
- binding do fluxo atual do `MsDevice` em `amq.direct` para `ms_device_update_last_seen`

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
