module "service_bus_subscription" {
  for_each = local.service_bus_subscriptions_map

  source = "../../../../../dtos-devops-templates/infrastructure/modules/service-bus-subscription"

  subscription_name    = each.value.service_bus_subscription_key
  resource_group_name  = azurerm_resource_group.core[each.value.region].name
  topic_name
  namespace_name
  function_app_principal_id         = module.functionapp["${each.value.subscriber_functionName}-${each.value.region}"].function_app_sami_id

  tags = var.tags
}

locals {

  service_bus_subscriptions_object_list = flatten([
    for region in keys(var.regions) : [
      for service_bus_subscription_key, service_bus_subscription_details in var.service_bus_subscriptions.subscriber_config : merge(
        {
          region                       = region                       # 1st iterator
          service_bus_subscription_key = service_bus_subscription_key # 2nd iterator
        },
        service_bus_subscription_details # the rest of the key/value pairs for a specific service_bus
      )
    ]
  ])

  # ...then project the list of objects into a map with unique keys (combining the iterators), for consumption by a for_each meta argument
  service_bus_subscriptions_map = {
    for object in local.service_bus_subscriptions_object_list : "${object.service_bus_subscription_key}-${object.region}" => object
  }
}
