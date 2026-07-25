variable "region" {
  description = "Huawei Cloud region code. Verify CCE and SWR availability before applying."
  type        = string
}

variable "environment" {
  description = "Environment name used in resource tags."
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "environment must be development, staging, or production."
  }
}

variable "name_prefix" {
  description = "Prefix applied to Huawei Cloud resources."
  type        = string
  default     = "commerce-devsecops"
}

variable "availability_zone" {
  description = "Optional availability zone. The first available zone is used when null."
  type        = string
  default     = null
}

variable "vpc_cidr" {
  description = "CIDR range for the platform VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR range for the CCE subnet."
  type        = string
  default     = "10.20.1.0/24"
}

variable "cluster_flavor_id" {
  description = "CCE cluster flavor available in the selected region."
  type        = string
}

variable "cluster_version" {
  description = "CCE Kubernetes version available in the selected region."
  type        = string
}

variable "container_network_type" {
  description = "CCE container network type."
  type        = string
  default     = "overlay_l2"
}

variable "node_flavor_id" {
  description = "Compute flavor ID for CCE worker nodes."
  type        = string
}

variable "node_os" {
  description = "Operating system supported by the selected CCE version."
  type        = string
}

variable "key_pair_name" {
  description = "Existing Huawei Cloud KPS key pair name. Private keys must not enter Terraform state."
  type        = string
}

variable "volume_type" {
  description = "EVS volume type available in the selected region."
  type        = string
  default     = "SSD"
}

variable "initial_node_count" {
  description = "Initial number of worker nodes."
  type        = number
  default     = 1
}

variable "enable_node_autoscaling" {
  description = "Enable CCE node-pool autoscaling."
  type        = bool
  default     = true
}

variable "min_node_count" {
  description = "Minimum worker-node count."
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum worker-node count."
  type        = number
  default     = 3
}

variable "swr_organization" {
  description = "Globally unique SWR organization name."
  type        = string
}

variable "tags" {
  description = "Additional resource tags."
  type        = map(string)
  default     = {}
}

