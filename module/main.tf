resource "aws_s3_bucket" "this" {
  bucket              = var.s3_bucket.bucket
  bucket_prefix       = try(var.s3_bucket.bucket_prefix, null)
  force_destroy       = try(var.s3_bucket.force_destroy, null)
  object_lock_enabled = try(var.s3_bucket.object_lock_enabled, null)
  tags                = try(var.tags, null)
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "this" {
  bucket = aws_s3_bucket.this.id
  acl    = "private"
}

# resource "aws_s3_bucket_logging" "this" {
#     bucket        = aws_s3_bucket.this.id
#     target_bucket = aws_s3_bucket.this.id
#     target_prefix = "${aws_s3_bucket.this.id}/"
# }

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  dynamic "rule" {
    for_each = var.server_side_encryption_configuration  != null ? [var.server_side_encryption_configuration] : []
    content {
      bucket_key_enabled = try(rule.value.bucket_key_enabled, null) != null ? rule.value.bucket_key_enabled : false
      dynamic "apply_server_side_encryption_by_default" {
        for_each = try(rule.value.apply_server_side_encryption_by_default, null) != null ? [rule.value.apply_server_side_encryption_by_default] : []
        content {
          sse_algorithm = apply_server_side_encryption_by_default.value.sse_algorithm
          kms_master_key_id = lookup(apply_server_side_encryption_by_default.value, "kms_master_key_id", null)
        }
      }
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  dynamic "rule" {
    for_each = { for rule in try(var.lifecycle_rules, []) : rule.id => rule }
    content {
      id     = rule.value.id
      status = rule.value.status

      dynamic "filter" {
        for_each = rule.value.filter != null ? [rule.value.filter] : []
        content {
          dynamic "and" {
            for_each = lookup(filter.value, "and", null) != null ? [filter.value.and] : []
            content {
              prefix = lookup(and.value, "prefix", null)
              tags   = lookup(and.value, "tags", null)
              object_size_greater_than = lookup(and.value, "object_size_greater_than", null)
              object_size_less_than    = lookup(and.value, "object_size_less_than", null)
            }
          }

          prefix = lookup(filter.value, "prefix", null)
          dynamic "tag" {
            for_each = lookup(filter.value, "tag", null) != null ? [filter.value.tag] : []
            content {
              key   = tag.value.key
              value = tag.value.value
            }
          }
          object_size_greater_than  = lookup(filter.value, "object_size_greater_than", null)
          object_size_less_than     = lookup(filter.value, "object_size_less_than", null)
        }
      }

      dynamic "transition" {
        for_each = try(rule.value.transition,null) != null ? [rule.value.transition] : []
        content {
          storage_class = transition.value.storage_class
          days          = lookup(transition.value, "days", null)
          date          = lookup(transition.value, "date", null)
        }
      }

      dynamic "expiration" {
        for_each = try(rule.value.expiration,null) != null ? [rule.value.expiration] : []
        content {
          days                        = lookup(expiration.value, "days", null)
          date                        = lookup(expiration.value, "date", null)
          expired_object_delete_marker = lookup(expiration.value, "expired_object_delete_marker", null)
        }
      }

      dynamic "abort_incomplete_multipart_upload" {
        for_each = try(rule.value.abort_incomplete_multipart_upload, null) != null ? [rule.value.abort_incomplete_multipart_upload] : []
        content {
          days_after_initiation = lookup(abort_incomplete_multipart_upload.value, "days_after_initiation", null)
        }
      }

      dynamic "noncurrent_version_expiration" {
        for_each = try(rule.value.noncurrent_version_expiration, null) != null ? [rule.value.noncurrent_version_expiration] : []
        content {
          noncurrent_days = lookup(noncurrent_version_expiration.value, "noncurrent_days", null)
        }
      }

      dynamic "noncurrent_version_transition" {
        for_each = try(rule.value.noncurrent_version_transition, null) != null ? [rule.value.noncurrent_version_transition] : []
        content {
          noncurrent_days = lookup(noncurrent_version_transition.value, "noncurrent_days", null)
          storage_class  = lookup(noncurrent_version_transition.value, "storage_class", null)
        }
      }

    }
  }
}
