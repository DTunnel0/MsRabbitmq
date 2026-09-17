#!/usr/bin/env python3
"""Synchronize definitions.json with the queues used by DTunnel services."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFINITIONS = ROOT / "definitions.json"

STANDARD_QUEUES = {
    "ms_app_config.user.created": ["user.created"],
    "ms_app_config.user.updated": ["user.updated"],
    "ms_app_config.user.deleted": ["user.deleted"],
    "ms_app_config.user.synchronized.v1": ["user.synchronized.v1"],
    "ms_app_config.member.resources.changed.v1": ["member.resources.changed.v1"],
    "ms_commerce.payment.approved": ["payment.approved"],
    "ms_commerce.payment.cancelled": ["payment.cancelled"],
    "ms_commerce.payment.refunded": ["payment.refund.succeeded"],
    "ms_config.user.created": ["user.created"],
    "ms_config.user.updated": ["user.updated"],
    "ms_config.user.deleted": ["user.deleted"],
    "ms_config.user.synchronized.v1": ["user.synchronized.v1"],
    "ms_config.member.resources.changed.v1": ["member.resources.changed.v1"],
    "ms_config.vps.server.snapshot.v1": ["vps.server.snapshot.v1"],
    "ms_payment.user.created": ["user.created"],
    "ms_payment.user.updated": ["user.updated"],
    "ms_payment.user.deleted": ["user.deleted"],
    "ms_payment.user.synchronized.v1": ["user.synchronized.v1"],
    "ms_protocol_token.entitlement.events": [
        "entitlement.granted",
        "entitlement.revoked",
    ],
    "ms_text.user.created": ["user.created"],
    "ms_text.user.updated": ["user.updated"],
    "ms_text.user.deleted": ["user.deleted"],
    "ms_text.user.synchronized.v1": ["user.synchronized.v1"],
    "ms_text.member.resources.changed.v1": ["member.resources.changed.v1"],
    "ms_user.entitlement.granted": ["entitlement.granted"],
    "ms_user.entitlement.revoked": ["entitlement.revoked"],
}

VPS_QUEUES = {
    "ms_vps.action.requested.v1": "vps.action.requested.v1",
    "ms_vps.action.completed.v1": "vps.action.completed.v1",
    "ms_vps.state.changed.v1": "vps.state.changed.v1",
}
VPS_RETRY_DELAYS_MS = (5_000, 10_000, 20_000, 40_000, 60_000)


def queue(name: str, arguments: dict | None = None) -> dict:
    return {
        "name": name,
        "vhost": "/",
        "durable": True,
        "auto_delete": False,
        "arguments": arguments or {},
    }


def binding(source: str, destination: str, routing_key: str) -> dict:
    return {
        "source": source,
        "vhost": "/",
        "destination": destination,
        "destination_type": "queue",
        "routing_key": routing_key,
        "arguments": {},
    }


def standard_topology(name: str, events: list[str]) -> tuple[list[dict], list[dict]]:
    queues = [
        queue(name),
        queue(
            f"{name}.retry",
            {
                "x-dead-letter-exchange": "dtunnel.requeue",
                "x-dead-letter-routing-key": name,
            },
        ),
        queue(f"{name}.dlq"),
    ]
    bindings = [binding("dtunnel.events", name, event) for event in events]
    bindings.extend(
        [
            binding("dtunnel.retry", f"{name}.retry", name),
            binding("dtunnel.dlq", f"{name}.dlq", name),
            binding("dtunnel.requeue", name, name),
        ]
    )
    return queues, bindings


def vps_topology(name: str, event: str) -> tuple[list[dict], list[dict]]:
    queues = [queue(name), queue(f"{name}.dlq")]
    bindings = [
        binding("dtunnel.events", name, event),
        binding("dtunnel.requeue", name, name),
        binding("dtunnel.dlq", f"{name}.dlq", name),
    ]
    for delay in VPS_RETRY_DELAYS_MS:
        retry_name = f"{name}.retry.{delay}"
        queues.append(
            queue(
                retry_name,
                {
                    "x-message-ttl": delay,
                    "x-dead-letter-exchange": "dtunnel.requeue",
                    "x-dead-letter-routing-key": name,
                },
            )
        )
        bindings.append(binding("dtunnel.retry", retry_name, f"{name}.{delay}"))
    return queues, bindings


def main() -> None:
    data = json.loads(DEFINITIONS.read_text())
    data["queues"] = [
        item for item in data.get("queues", []) if not item["name"].startswith("ms_")
    ]
    data["bindings"] = [
        item
        for item in data.get("bindings", [])
        if not (
            item.get("destination_type") == "queue"
            and item["destination"].startswith("ms_")
        )
    ]

    for name, events in STANDARD_QUEUES.items():
        queues, bindings = standard_topology(name, events)
        data["queues"].extend(queues)
        data["bindings"].extend(bindings)
    for name, event in VPS_QUEUES.items():
        queues, bindings = vps_topology(name, event)
        data["queues"].extend(queues)
        data["bindings"].extend(bindings)

    data["queues"].sort(key=lambda item: item["name"])
    data["bindings"].sort(
        key=lambda item: (
            item["source"],
            item["destination"],
            item.get("routing_key", ""),
        )
    )
    DEFINITIONS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
