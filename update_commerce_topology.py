#!/usr/bin/env python3
"""Replace obsolete plan/payment consumer queues with Commerce v2 queues."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFINITIONS = ROOT / 'definitions.json'
OBSOLETE_PREFIXES = ('ms_user.payment.', 'ms_plan.plan.purchase.')
QUEUES = {
    'ms_commerce.payment.approved': ['payment.approved'],
    'ms_commerce.payment.cancelled': ['payment.cancelled'],
    'ms_commerce.payment.refunded': ['payment.refund.succeeded'],
    'ms_user.entitlement.granted': ['entitlement.granted'],
    'ms_user.entitlement.revoked': ['entitlement.revoked'],
    'ms_protocol_token.entitlement.events': [
        'entitlement.granted',
        'entitlement.revoked',
    ],
}


def queue(name: str, arguments: dict | None = None) -> dict:
    return {
        'name': name,
        'vhost': '/',
        'durable': True,
        'auto_delete': False,
        'arguments': arguments or {},
    }


def binding(source: str, destination: str, routing_key: str) -> dict:
    return {
        'source': source,
        'vhost': '/',
        'destination': destination,
        'destination_type': 'queue',
        'routing_key': routing_key,
        'arguments': {},
    }


def main() -> None:
    data = json.loads(DEFINITIONS.read_text())
    managed_names = {
        suffix
        for name in QUEUES
        for suffix in (name, f'{name}.retry', f'{name}.dlq')
    }
    data['queues'] = [
        item
        for item in data['queues']
        if not item['name'].startswith(OBSOLETE_PREFIXES)
        and item['name'] not in managed_names
    ]
    data['bindings'] = [
        item
        for item in data['bindings']
        if not item['destination'].startswith(OBSOLETE_PREFIXES)
        and item['destination'] not in managed_names
    ]
    for name, events in QUEUES.items():
        data['queues'].extend(
            [
                queue(name),
                queue(
                    f'{name}.retry',
                    {
                        'x-dead-letter-exchange': 'dtunnel.requeue',
                        'x-dead-letter-routing-key': name,
                    },
                ),
                queue(f'{name}.dlq'),
            ]
        )
        data['bindings'].extend(
            binding('dtunnel.events', name, event) for event in events
        )
        data['bindings'].extend(
            [
                binding('dtunnel.retry', f'{name}.retry', name),
                binding('dtunnel.dlq', f'{name}.dlq', name),
                binding('dtunnel.requeue', name, name),
            ]
        )
    DEFINITIONS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
