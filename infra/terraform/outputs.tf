output "vpc_id" {
  description = "Created VPC ID."
  value       = huaweicloud_vpc.platform.id
}

output "subnet_id" {
  description = "Created subnet ID."
  value       = huaweicloud_vpc_subnet.platform.id
}

output "cce_cluster_id" {
  description = "Created CCE cluster ID."
  value       = huaweicloud_cce_cluster.platform.id
}

output "cce_node_pool_id" {
  description = "Created CCE node-pool ID."
  value       = huaweicloud_cce_node_pool.platform.id
}

output "swr_repositories" {
  description = "Created private SWR repositories."
  value       = { for name, repository in huaweicloud_swr_repository.services : name => repository.name }
}

