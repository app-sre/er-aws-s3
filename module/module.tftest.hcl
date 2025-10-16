variables {
  s3_bucket = {
    bucket = "test-bucket"
  }

  server_side_encryption_configuration = {
    apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
    }
  }
  lifecycle_rules = []
  tags = {
    managed_by_integration = "external_resources"
    cluster                = "test-cluster"
    namespace              = "test-namespace"
    environment            = "stage"
    app                    = "test-app"
  }

  region = "us-east-1"
  # provision = {
  #   provision_provider = "aws"
  #   provisioner        = "test-account"
  #   provider           = "rds"
  #   identifier         = "test-instance"
  #   target_cluster     = "test-cluster"
  #   target_namespace   = "test-namespace"
  #   target_secret_name = "test-db-creds"
  #   module_provision_data = {
  #     tf_state_bucket         = "external-resources-state"
  #     tf_state_region         = "us-east-1"
  #     tf_state_dynamodb_table = "external-resources-terraform-lock"
  #     tf_state_key            = "aws/test-account/rds/test-instance/terraform.tfstate"
  #   }
  # }
}

run "s3_bucket" {
  command = plan

  assert {
    condition     = aws_s3_bucket.this.bucket != null
    error_message = "A bucket is expected to be created."
  }

  assert {
    condition = aws_s3_bucket_acl.this.acl == "private"
    error_message = "The ACL should be set to private."
  }

  assert {
    condition = aws_s3_bucket_ownership_controls.this.rule[0].object_ownership == "BucketOwnerPreferred"
    error_message = "The object ownership should be set to BucketOwnerPreferred."
  }

  assert {
    condition = [for r in aws_s3_bucket_server_side_encryption_configuration.this.rule : r.apply_server_side_encryption_by_default[0].sse_algorithm][0] == "AES256"
    error_message = "The server-side encryption algorithm should be set to AES256."
  }

}

run "server_side_encryption" {
  command = plan
  variables {
    server_side_encryption_configuration = {
      bucket_key_enabled = true
      apply_server_side_encryption_by_default = {
          sse_algorithm = "AES256"
        }
    }
  }
  assert {
    condition = [for r in aws_s3_bucket_server_side_encryption_configuration.this.rule : r.apply_server_side_encryption_by_default[0].sse_algorithm][0] == "AES256"
    error_message = "The server-side encryption algorithm should be set to AES256."
  }
  assert {
    condition = [for r in aws_s3_bucket_server_side_encryption_configuration.this.rule: r.bucket_key_enabled][0] == true
    error_message = "The bucket key should be enabled."
  }
}



run "lifecycle_policies" {
  command = plan
  variables {
    lifecycle_rules = [
      {"id": "test-lifecycle-rule-1", "status": "Enabled", "filter": {"prefix": "test-prefix/"}, "expiration": {"days": 30}},
      {"id": "test-lifecycle-rule-2", "status": "Enabled", "filter": {"prefix": "another-prefix/"}, "expiration": {"days": 60}}
    ]
  }
  assert {
    condition = aws_s3_bucket_lifecycle_configuration.this.rule[0].id == "test-lifecycle-rule-1"
    error_message = "The first lifecycle rule should be test-lifecycle-rule-1."
  }
}
