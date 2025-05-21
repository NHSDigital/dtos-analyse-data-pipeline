application           = "andppl"
application_full_name = "analyse-data-pipeline"
environment           = "DEV"

features = {
  acr_enabled                          = false
  api_management_enabled               = false
  event_grid_enabled                   = true
  private_endpoints_enabled            = true
  private_service_connection_is_manual = false
  public_network_access_enabled        = false
  smoke_test_managed_identity_created  = false
}

tags = {
  Project = "analyse-data-pipeline"
}

regions = {
  uksouth = {
    is_primary_region = true
    address_space     = "10.113.0.0/16"
    connect_peering   = true
    subnets = {
      apps = {
        cidr_newbits               = 8
        cidr_offset                = 2
        delegation_name            = "Microsoft.Web/serverFarms"
        service_delegation_name    = "Microsoft.Web/serverFarms"
        service_delegation_actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
      }
      pep = {
        cidr_newbits = 8
        cidr_offset  = 1
      }
      sql = {
        cidr_newbits = 8
        cidr_offset  = 3
      }
    }
  }
}

routes = {
  uksouth = {
    firewall_policy_priority = 100
    application_rules        = []
    nat_rules                = []
    network_rules = [
      {
        name                  = "AllowandpplToAudit"
        priority              = 800
        action                = "Allow"
        rule_name             = "andpplToAudit"
        source_addresses      = ["10.113.0.0/16"] # will be populated with the andppl manager subnet address space
        destination_addresses = ["10.114.0.0/16"] # will be populated with the audit subnet address space
        protocols             = ["TCP", "UDP"]
        destination_ports     = ["443"]
      },
      {
        name                  = "AllowAuditToandppl"
        priority              = 810
        action                = "Allow"
        rule_name             = "AuditToandppl"
        source_addresses      = ["10.114.0.0/16"]
        destination_addresses = ["10.113.0.0/16"]
        protocols             = ["TCP", "UDP"]
        destination_ports     = ["443"]
      }
    ]
    route_table_routes_to_audit = [
      {
        name                   = "andpplToAudit"
        address_prefix         = "10.114.0.0/16"
        next_hop_type          = "VirtualAppliance"
        next_hop_in_ip_address = "" # will be populated with the Firewall Private IP address
      }
    ]
    route_table_routes_from_audit = [
      {
        name                   = "AuditToandppl"
        address_prefix         = "10.113.0.0/16"
        next_hop_type          = "VirtualAppliance"
        next_hop_in_ip_address = "" # will be populated with the Firewall Private IP address
      }
    ]
  }
}

app_service_plan = {
  os_type                  = "Linux"
  sku_name                 = "P2v3"
  vnet_integration_enabled = true

  autoscale = {
    memory_percentage = {
      metric = "MemoryPercentage"

      capacity_min = "1"
      capacity_max = "5"
      capacity_def = "1"

      time_grain       = "PT1M"
      statistic        = "Average"
      time_window      = "PT10M"
      time_aggregation = "Average"

      inc_operator        = "GreaterThan"
      inc_threshold       = 70
      inc_scale_direction = "Increase"
      inc_scale_type      = "ChangeCount"
      inc_scale_value     = 1
      inc_scale_cooldown  = "PT5M"

      dec_operator        = "LessThan"
      dec_threshold       = 25
      dec_scale_direction = "Decrease"
      dec_scale_type      = "ChangeCount"
      dec_scale_value     = 1
      dec_scale_cooldown  = "PT5M"
    }
  }

  instances = {
    DefaultServicePlan = {}
    # BIAnalyticsDataService       = {}
    # BIAnalyticsService           = {}
    # DemographicsService          = {}
    # EpisodeDataService           = {}
    # EpisodeIntegrationService    = {}
    # EpisodeManagementService     = {}
    # MeshIntegrationService       = {}
    # ParticipantManagementService = {}
    # ReferenceDataService         = {}
  }
}

diagnostic_settings = {
  metric_enabled = true
}



function_apps = {
  acr_mi_name = "dtos-analyse-data-pipeline-acr-push"
  acr_name    = "acrukshubdevandppl"
  acr_rg_name = "rg-hub-dev-uks-andppl"

  app_insights_name                      = "appi-dev-uks-andppl"
  app_insights_rg_name                   = "rg-andppl-dev-uks-audit"
  app_service_logs_disk_quota_mb         = 35
  app_service_logs_retention_period_days = 7

  always_on = true

  cont_registry_use_mi = true

  docker_CI_enable  = "true"
  docker_env_tag    = "development"
  docker_img_prefix = "analyse-data-pipeline"

  enable_appsrv_storage         = "false"
  ftps_state                    = "Disabled"
  https_only                    = true
  remote_debugging_enabled      = false
  storage_uses_managed_identity = null
  worker_32bit                  = false
  ip_restriction_default_action = "Deny"

  fa_config = {

    serviceLayer = {
      name_suffix            = "service-layer"
      function_endpoint_name = "service-layer"
      app_service_plan_key   = "DefaultServicePlan"
      env_vars_static = {
        QUEUE_NAME               = "queue.1"
        FUNCTIONS_WORKER_RUNTIME = "python"
        ASPNETCORE_URLS          = "http://0.0.0.0:7072"
      }
      env_vars_from_key_vault = [
        {
          env_var_name          = "SERVICE_BUS_CONNECTION_STR"
          key_vault_secret_name = "SERVICE-BUS-CONNECTION-STR"
        }
      ]
    }
  }
}

function_app_slots = []

key_vault = {
  disk_encryption   = true
  soft_del_ret_days = 7
  purge_prot        = false
  sku_name          = "standard"
}

storage_accounts = {
  fnapp = {
    name_suffix                   = "fnappstor"
    account_tier                  = "Standard"
    replication_type              = "LRS"
    public_network_access_enabled = false
    containers = {
      config = {
        container_name = "config"
      }
      inbound = {
        container_name = "inbound"
      }
      inbound-poison = {
        container_name = "inbound-poison"
      }
    }
  }
}
