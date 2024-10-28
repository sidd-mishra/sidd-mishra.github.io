# summariz.py

import json
from typing import List, Dict, Any

def summarize(inputJson: str) -> str:
    data = json.loads(inputJson)    
    credit_limit = data.get("creditLimit", 0)
    events = data.get("events", [])

    available_credit = credit_limit
    payable_balance = 0

    pending_transactions: Dict[str, Dict[str, Any]] = {}
    settled_transactions: Dict[str, Dict[str, Any]] = {}

    for event in events:
        event_type = event.get("eventType")
        event_time = event.get("eventTime")
        txn_id = event.get("txnId")
        amount = event.get("amount", 0)

        if event_type == "TXN_AUTHED":
            pending_transactions[txn_id] = {
                "txnId": txn_id,
                "amount": amount,
                "initial_time": event_time,
                "final_time": None,
                "type": "transaction"
            }
            available_credit -= amount

        elif event_type == "TXN_SETTLED":
            if txn_id in pending_transactions:
                txn = pending_transactions.pop(txn_id)
                old_amount = txn["amount"]
                new_amount = amount
                available_credit += old_amount  # Release old hold
                available_credit -= new_amount  # Apply new settled amount
                payable_balance += new_amount
                txn.update({
                    "amount": new_amount,
                    "final_time": event_time
                })
                settled_transactions[txn_id] = txn

        elif event_type == "TXN_AUTH_CLEARED":
            if txn_id in pending_transactions:
                txn = pending_transactions.pop(txn_id)
                available_credit += txn["amount"]

        elif event_type == "PAYMENT_INITIATED":
            pending_transactions[txn_id] = {
                "txnId": txn_id,
                "amount": amount,
                "initial_time": event_time,
                "final_time": None,
                "type": "payment"
            }
            payable_balance += amount  # Since amount is negative

        elif event_type == "PAYMENT_POSTED":
            if txn_id in pending_transactions:
                payment = pending_transactions.pop(txn_id)
                amount = payment["amount"]
                payable_balance -= amount  # Remove the payment from payable balance
                available_credit -= amount  # Increase available credit
                payment.update({
                    "final_time": event_time
                })
                settled_transactions[txn_id] = payment

        elif event_type == "PAYMENT_CANCELED":
            if txn_id in pending_transactions:
                payment = pending_transactions.pop(txn_id)
                payable_balance -= payment["amount"]  # Revert the initiated payment

    # Prepare Pending Transactions List
    pending_list = sorted(
        [txn for txn in pending_transactions.values()],
        key=lambda x: x["initial_time"],
        reverse=True
    )

    # Prepare Settled Transactions List
    settled_list = sorted(
        [txn for txn in settled_transactions.values()],
        key=lambda x: x["initial_time"],
        reverse=True
    )[:3]  # Only the three most recent

    # Format amounts
    def format_amount(a):
        return f"${a}" if a >= 0 else f"-${-a}"

    # Build the output string
    output_lines = [
        f"Available credit: {format_amount(available_credit)}",
        f"Payable balance: {format_amount(payable_balance)}",
        "",
        "Pending transactions:"
    ]

    for txn in pending_list:
        output_lines.append(f"{txn['txnId']}: {format_amount(txn['amount'])} @ time {txn['initial_time']}")

    output_lines.append("")
    output_lines.append("Settled transactions:")

    for txn in settled_list:
        if txn["final_time"] is not None:
            output_lines.append(f"{txn['txnId']}: {format_amount(txn['amount'])} @ time {txn['initial_time']} (finalized @ time {txn['final_time']})")
        else:
            output_lines.append(f"{txn['txnId']}: {format_amount(txn['amount'])} @ time {txn['initial_time']}")

    return "\n".join(output_lines).strip()
