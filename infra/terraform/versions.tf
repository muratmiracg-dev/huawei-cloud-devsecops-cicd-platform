terraform {
  required_version = ">= 1.7.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = ">= 1.77.0, < 2.0.0"
    }
  }
}

