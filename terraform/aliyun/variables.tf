# 阿里云Terraform变量

variable "region" {
  description = "阿里云区域"
  type        = string
  default     = "cn-hangzhou"
}

variable "project_name" {
  description = "项目名称"
  type        = string
  default     = "scholarforge"
}

variable "zone_ids" {
  description = "可用区列表"
  type        = list(string)
  default     = ["cn-hangzhou-g", "cn-hangzhou-h"]
}

# 数据库配置
variable "db_instance_class" {
  description = "RDS实例规格"
  type        = string
  default     = "rds.pg.s1.large"  # 2核4G
}

variable "db_storage" {
  description = "数据库存储空间(GB)"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "数据库名"
  type        = string
  default     = "scholarforge"
}

variable "db_username" {
  description = "数据库用户名"
  type        = string
  default     = "scholarforge"
}

variable "db_password" {
  description = "数据库密码"
  type        = string
  sensitive   = true
}

# Redis配置
variable "redis_instance_class" {
  description = "Redis实例规格"
  type        = string
  default     = "redis.shard.small.2.ce"  # 1GB
}

# OSS配置
variable "oss_bucket_name" {
  description = "OSS Bucket名称"
  type        = string
  default     = "scholarforge-data"
}

# ECS配置
variable "ecs_instance_count" {
  description = "ECS实例数量"
  type        = number
  default     = 2
}

variable "ecs_instance_type" {
  description = "ECS实例规格"
  type        = string
  default     = "ecs.c6.large"  # 2核4G
}

# SLB配置
variable "slb_spec" {
  description = "SLB规格"
  type        = string
  default     = "slb.s1.small"
}
