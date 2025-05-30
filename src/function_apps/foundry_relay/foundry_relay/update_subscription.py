# update_subscription.py
import json
import os

subscription_name = os.environ.get("SUBSCRIPTION_NAME", "default-subscription")

file_path = "/home/site/wwwroot/foundry_relay/function.json"

with open(file_path, "r") as f:
    config = json.load(f)

for binding in config.get("bindings", []):
    if binding.get("type") == "serviceBusTrigger":
        binding["subscriptionName"] = subscription_name

with open(file_path, "w") as f:
    json.dump(config, f, indent=2)