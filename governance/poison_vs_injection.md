# Poisoning vs adversarial input

## Poisoning
Someone changes the knowledge the model retrieves or trains on, so answers drift without any user being clever.

## Adversarial input
Someone types text that tries to override our instructions or extract secrets.

## Lab evidence
`governance/knowledge/pin.json` catches silent FAQ swaps.
`access_control/injection_guard.py` returns 400 on override language.

## We will not claim
We do not claim the model cannot be jailbroken. We claim the API fails closed on known override phrasing and that pinned files cannot change without a pull request.
