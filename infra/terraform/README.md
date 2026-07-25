# Huawei Cloud Infrastructure

This Terraform configuration provisions the portfolio project's core Huawei Cloud
resources:

- VPC and subnet
- CCE cluster and autoscaling node pool
- private SWR repositories for the two services

## Safety

The configuration intentionally does not embed credentials or create a key pair.
Use an existing KPS key pair and authenticate the Huawei Cloud provider through
approved environment variables or a protected CI credential store.

Review region-specific CCE versions, flavors, operating systems, EVS volume
types, quotas, and prices before running `terraform apply`.

## Commands

```bash
cp terraform.tfvars.example terraform.tfvars
terraform fmt -check
terraform init
terraform validate
terraform plan
```

Do not commit `terraform.tfvars`, state files, credentials, or plan files.

