#!/bin/sh
set -eu

user="${RABBITMQ_DEFAULT_USER:-guest}"
password="${RABBITMQ_DEFAULT_PASS:-guest}"

cleanup() {
  if [ -z "${rabbit_pid:-}" ]; then
    return
  fi

  if ! kill -0 "$rabbit_pid" 2>/dev/null; then
    return
  fi

  kill "$rabbit_pid"
  wait "$rabbit_pid" || true
}

trap cleanup INT TERM

rabbitmq-server &
rabbit_pid=$!

until rabbitmq-diagnostics -q ping >/dev/null 2>&1; do
  sleep 2
done

rabbitmqctl await_startup
rabbitmqctl import_definitions /etc/rabbitmq/definitions.json

while IFS= read -r queue; do
  if [ -z "$queue" ]; then
    continue
  fi
  if rabbitmqctl -q list_queues -p / name | grep -Fqx "$queue"; then
    rabbitmqctl delete_queue -p / "$queue"
  fi
done </etc/rabbitmq/obsolete-queues.txt

if ! rabbitmqctl change_password "$user" "$password" >/dev/null 2>&1; then
  rabbitmqctl add_user "$user" "$password"
fi

rabbitmqctl set_user_tags "$user" administrator
rabbitmqctl set_permissions -p / "$user" ".*" ".*" ".*"

wait "$rabbit_pid"
