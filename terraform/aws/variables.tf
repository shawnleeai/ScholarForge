# AWS Terraform变量

variable "region" {
  description = "AWS区域"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "项目名称"
  type        = string
  default     = "scholarforge"
}

# 数据库配置
variable "db_instance_class" {
  description = "RDS实例规格"
  type        = string
  default     = "db.t3.medium"  # 2核4G
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
  default     = "postgres"
}

variable "db_password" {
  description = "数据库密码"
  type        = string
  sensitive   = true
}

# Redis配置
variable "redis_node_type" {
  description = "Redis节点规格"
  type        = string
  default     = "cache.t3.micro"
}

# S3配置
variable "s3_bucket_name" {
  description = "S3 Bucket名称"
  type        = string
  default     = "scholarforge-data-us-east-1"
}
