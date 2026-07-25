data "huaweicloud_availability_zones" "available" {}

locals {
  availability_zone = coalesce(
    var.availability_zone,
    try(data.huaweicloud_availability_zones.available.names[0], null)
  )
  common_tags = merge(
    {
      project     = "huawei-cloud-devsecops-cicd-platform"
      environment = var.environment
      managed_by  = "terraform"
    },
    var.tags
  )
}

resource "huaweicloud_vpc" "platform" {
  name = "${var.name_prefix}-vpc"
  cidr = var.vpc_cidr
  tags = local.common_tags
}

resource "huaweicloud_vpc_subnet" "platform" {
  vpc_id            = huaweicloud_vpc.platform.id
  name              = "${var.name_prefix}-subnet"
  cidr              = var.subnet_cidr
  gateway_ip        = cidrhost(var.subnet_cidr, 1)
  availability_zone = local.availability_zone
}

resource "huaweicloud_cce_cluster" "platform" {
  name                   = "${var.name_prefix}-cce"
  flavor_id              = var.cluster_flavor_id
  cluster_version        = var.cluster_version
  cluster_type           = "VirtualMachine"
  container_network_type = var.container_network_type
  vpc_id                 = huaweicloud_vpc.platform.id
  subnet_id              = huaweicloud_vpc_subnet.platform.id
  description            = "CCE cluster for the DevSecOps portfolio platform"
  tags                   = local.common_tags
}

resource "huaweicloud_cce_node_pool" "platform" {
  cluster_id               = huaweicloud_cce_cluster.platform.id
  name                     = "${var.name_prefix}-pool"
  type                     = "vm"
  os                       = var.node_os
  flavor_id                = var.node_flavor_id
  availability_zone        = local.availability_zone
  key_pair                 = var.key_pair_name
  initial_node_count       = var.initial_node_count
  scall_enable             = var.enable_node_autoscaling
  min_node_count           = var.min_node_count
  max_node_count           = var.max_node_count
  scale_down_cooldown_time = 10
  priority                 = 1
  tags                     = local.common_tags

  root_volume {
    size       = 40
    volumetype = var.volume_type
  }

  data_volumes {
    size       = 100
    volumetype = var.volume_type
  }
}

resource "huaweicloud_swr_organization" "platform" {
  name = var.swr_organization
}

resource "huaweicloud_swr_repository" "services" {
  for_each = toset(["catalog-service", "orders-service"])

  organization = huaweicloud_swr_organization.platform.name
  name         = each.value
  category     = "app_server"
  is_public    = false
  description  = "Private image repository for ${each.value}"
}
