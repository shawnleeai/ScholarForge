# 阿里云基础设施即代码
# Terraform配置

terraform {
  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.220"
    }
  }
  required_version = ">= 1.0"
}

# 配置阿里云Provider
provider "alicloud" {
  region = var.region
}

# 获取可用区
 data "alicloud_zones" "default" {
  available_disk_category     = "cloud_efficiency"
  available_resource_creation = "VSwitch"
}

# VPC网络
resource "alicloud_vpc" "main" {
  vpc_name   = "${var.project_name}-vpc"
  cidr_block = "10.0.0.0/16"
}

# 交换机
resource "alicloud_vswitch" "main" {
  count        = length(var.zone_ids)
  vpc_id       = alicloud_vpc.main.id
  cidr_block   = "10.0.${count.index + 1}.0/24"
  zone_id      = var.zone_ids[count.index]
  vswitch_name = "${var.project_name}-vswitch-${count.index + 1}"
}

# 安全组
resource "alicloud_security_group" "main" {
  name   = "${var.project_name}-sg"
  vpc_id = alicloud_vpc.main.id
}

# RDS PostgreSQL
resource "alicloud_db_instance" "main" {
  engine               = "PostgreSQL"
  engine_version       = "16.0"
  instance_type        = var.db_instance_class
  instance_storage     = var.db_storage
  instance_name        = "${var.project_name}-db"
  vswitch_id           = alicloud_vswitch.main[0].id
  security_group_ids   = [alicloud_security_group.main.id]
  instance_charge_type = "Postpaid"

  parameters {
    name  = "max_connections"
    value = "500"
  }
}

# 创建数据库账号
resource "alicloud_db_account" "main" {
  db_instance_id   = alicloud_db_instance.main.id
  account_name     = var.db_username
  account_password = var.db_password
  account_type     = "Super"
}

# 创建数据库
resource "alicloud_db_database" "main" {
  instance_id = alicloud_db_instance.main.id
  name        = var.db_name
}

# Redis 企业版
resource "alicloud_kvstore_instance" "main" {
  instance_name  = "${var.project_name}-redis"
  instance_type  = "Redis"
  engine_version = "7.0"
  instance_class = var.redis_instance_class
  vswitch_id     = alicloud_vswitch.main[0].id
  security_group_id = alicloud_security_group.main.id
  payment_type   = "PostPaid"
}

# OSS Bucket
resource "alicloud_oss_bucket" "main" {
  bucket = var.oss_bucket_name
  acl    = "private"

  versioning {
    status = "Enabled"
  }

  lifecycle_rule {
    id      = "log-expiration"
    prefix  = "logs/"
    enabled = true

    expiration {
      days = 30
    }
  }
}

# ECS 实例
resource "alicloud_instance" "main" {
  count             = var.ecs_instance_count
  instance_name     = "${var.project_name}-ecs-${count.index + 1}"
  instance_type     = var.ecs_instance_type
  image_id          = "ubuntu_22_04_x64_20G_alibase_20230630.vhd"
  vswitch_id        = alicloud_vswitch.main[count.index % length(alicloud_vswitch.main)].id
  security_groups   = [alicloud_security_group.main.id]
  system_disk_category = "cloud_efficiency"
  system_disk_size  = 40
  internet_max_bandwidth_out = 10

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose
              systemctl enable docker
              systemctl start docker
              EOF
}

# SLB负载均衡
resource "alicloud_slb_load_balancer" "main" {
  load_balancer_name = "${var.project_name}-slb"
  address_type       = "internet"
  load_balancer_spec = var.slb_spec
  vswitch_id         = alicloud_vswitch.main[0].id
}

# 输出
output "rds_endpoint" {
  value = alicloud_db_instance.main.connection_string
}

output "redis_endpoint" {
  value = alicloud_kvstore_instance.main.connection_domain
}

output "oss_bucket_endpoint" {
  value = alicloud_oss_bucket.main.extranet_endpoint
}

output "slb_ip" {
  value = alicloud_slb_load_balancer.main.address
}
