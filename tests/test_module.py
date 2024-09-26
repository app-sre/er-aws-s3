import json

from cdktf import Testing
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_bucket_lifecycle_configuration import (
    S3BucketLifecycleConfiguration,
)

from er_aws_s3.s3 import Stack

from .conftest import input_object


class TestMain:
    """Main test class"""

    json.loads("{}")
    input = input_object()
    stack = Stack(Testing.app(), "CDKTF", input)
    synthesized = Testing.synth(stack)

    def test_should_contain_s3_bucket(self) -> None:
        """Test should_contain_s3_bucket"""
        assert Testing.to_have_resource_with_properties(
            self.synthesized,
            S3Bucket.TF_RESOURCE_TYPE,
            {
                "bucket": "test-s3",
                "tags": {
                    "app": "external-resources-poc",
                    "cluster": "appint-ex-01",
                    "environment": "stage",
                    "managed_by_integration": "external_resources",
                    "namespace": "external-resources-poc",
                },
            },
        )

        assert Testing.to_have_resource_with_properties(
            self.synthesized,
            S3BucketLifecycleConfiguration.TF_RESOURCE_TYPE,
            {
                "bucket": "${aws_s3_bucket.test-s3.id}",
                "rule": [
                    {
                        "id": "cleanup_noncurrent_versions",
                        "status": "Enabled",
                    }
                ],
            },
        )
