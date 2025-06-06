locals {
  instances = merge([
    for key, attrs in var.instances : {
      for i in range(attrs.count) : 
      "${key}${i}" => {
          ami           = attrs.ami
          instance_type = attrs.instance_type
          volume_size   = attrs.volume_size
          user_data     = attrs.user_data
          tags          = attrs.tags
      }
    }
  ]...)
}