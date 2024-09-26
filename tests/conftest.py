from cdktf import Testing

from er_aws_s3.input import AppInterfaceInput

Testing.__test__ = False


def input_data() -> dict:
    """Returns a JSON input data"""
    return {
        "data": {
            "identifier": "test-s3",
            "acl": "private",
            "versioning": "false",
            "server_side_encryption_configuration": {
                "rule": {
                    "apply_server_side_encryption_by_default": {
                        "sse_algorithm": "AES256",
                    }
                },
            },
            "lifecycle_rules": [
                {
                    "id": "cleanup_noncurrent_versions",
                    "enabled": "true",
                    "status": "Enabled",
                    "noncurrent_version_expiration": {
                        "days": 1,
                    },
                    "expiration": {"expired_object_delete_marker": "true"},
                }
            ],
            "default_tags": [{"tags": {"app": "app-sre-infra"}}],
            "output_prefix": "output_prefix_s3_bucket",
            "tags": {
                "app": "external-resources-poc",
                "cluster": "appint-ex-01",
                "environment": "stage",
                "managed_by_integration": "external_resources",
                "namespace": "external-resources-poc",
            },
        },
        "provision": {
            "provision_provider": "aws",
            "provisioner": "app-int-example-01",
            "provider": "s3",
            "identifier": "test-23",
            "target_cluster": "appint-ex-01",
            "target_namespace": "external-resources-poc",
            "target_secret_name": "test-s3",
            "module_provision_data": {
                "tf_state_bucket": "external-resources-terraform-state-dev",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "external-resources-terraform-lock",
                "tf_state_key": "aws/app-int-example-01/s3/test-rds/terraform.tfstate",
            },
        },
    }


def input_object() -> AppInterfaceInput:
    """Returns an AppInterfaceInput object"""
    return AppInterfaceInput.model_validate(input_data())
