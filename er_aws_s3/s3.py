import json
from typing import Any, ClassVar

from cdktf import ITerraformDependable, S3Backend, TerraformOutput, TerraformStack
from cdktf_cdktf_provider_aws.data_aws_sns_topic import DataAwsSnsTopic
from cdktf_cdktf_provider_aws.data_aws_sqs_queue import DataAwsSqsQueue
from cdktf_cdktf_provider_aws.iam_access_key import IamAccessKey
from cdktf_cdktf_provider_aws.iam_policy import IamPolicy
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_role_policy_attachment import IamRolePolicyAttachment
from cdktf_cdktf_provider_aws.iam_user import IamUser
from cdktf_cdktf_provider_aws.iam_user_policy_attachment import IamUserPolicyAttachment
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_bucket_acl import S3BucketAcl
from cdktf_cdktf_provider_aws.s3_bucket_cors_configuration import (
    S3BucketCorsConfiguration,
)
from cdktf_cdktf_provider_aws.s3_bucket_lifecycle_configuration import (
    S3BucketLifecycleConfiguration,
    S3BucketLifecycleConfigurationRule,
    S3BucketLifecycleConfigurationRuleNoncurrentVersionExpiration,
    S3BucketLifecycleConfigurationRuleNoncurrentVersionTransition,
)
from cdktf_cdktf_provider_aws.s3_bucket_logging import S3BucketLoggingA
from cdktf_cdktf_provider_aws.s3_bucket_notification import (
    S3BucketNotification,
    S3BucketNotificationQueue,
    S3BucketNotificationTopic,
)
from cdktf_cdktf_provider_aws.s3_bucket_ownership_controls import (
    S3BucketOwnershipControls,
    S3BucketOwnershipControlsRule,
)
from cdktf_cdktf_provider_aws.s3_bucket_policy import S3BucketPolicy
from cdktf_cdktf_provider_aws.s3_bucket_request_payment_configuration import (
    S3BucketRequestPaymentConfiguration,
)
from cdktf_cdktf_provider_aws.s3_bucket_server_side_encryption_configuration import (
    S3BucketServerSideEncryptionConfigurationA,
)
from cdktf_cdktf_provider_aws.s3_bucket_versioning import (
    S3BucketVersioningA,
    S3BucketVersioningVersioningConfiguration,
)
from cdktf_cdktf_provider_aws.s3_bucket_website_configuration import (
    S3BucketWebsiteConfiguration,
)
from constructs import Construct

from er_aws_s3.input import (
    AppInterfaceInput,
    S3EventNotification,
    S3ReplicationConfiguration,
)


class S3ReplicationConfigsHelper:
    """Helper class for creating S3 replication configs"""

    assume_role_policy: ClassVar[dict[str, Any]] = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {"Service": "s3.amazonaws.com"},
                "Effect": "Allow",
                "Sid": "",
            }
        ],
    }

    def __init__(
        self, construct: TerraformStack, app_interface_input: AppInterfaceInput
    ) -> None:
        self.construct = construct
        self.input = app_interface_input

    def _create_iam_policy(self, config: S3ReplicationConfiguration) -> IamPolicy:
        return IamPolicy(
            self.construct,
            id_=f"${self.input.data.identifier}_${config.rule_name}",
            name=f"${config.rule_name}_iam_policy",
            policy=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": [
                                "s3:GetReplicationConfiguration",
                                "s3:ListBucket",
                            ],
                            "Effect": "Allow",
                            "Resource": [
                                "${aws_s3_bucket."
                                + self.input.data.identifier
                                + ".arn}",
                                "${aws_s3_bucket."
                                + config.destination_bucket_identifier
                                + ".arn}",
                            ],
                        },
                        {
                            "Action": ["s3:GetObjectVersion", "s3:GetObjectVersionAcl"],
                            "Effect": "Allow",
                            "Resource": [
                                "${aws_s3_bucket."
                                + self.input.data.identifier
                                + ".arn}/*"
                            ],
                        },
                        {
                            "Action": ["s3:ReplicateObject", "s3:ReplicateDelete"],
                            "Effect": "Allow",
                            "Resource": f"${{aws_s3_bucket.${config.destination_bucket_identifier}.arn}}/*",
                        },
                    ],
                },
                sort_keys=True,
            ),
        )

    def _create_aws_iam_role(
        self,
        config: S3ReplicationConfiguration,
    ) -> IamRole:
        """Creates the necessary IAM role for the replication bucket"""
        return IamRole(
            self.construct,
            id_=f"${self.input.data.identifier}_${config.rule_name}",
            name=f"${config.rule_name}_iam_role",
            assume_role_policy=json.dumps(
                S3ReplicationConfigsHelper.assume_role_policy, sort_keys=True
            ),
        )

    def _create_aws_iam_policy_attachment(
        self, config: S3ReplicationConfiguration, role: IamRole, policy: IamPolicy
    ) -> None:
        IamRolePolicyAttachment(
            self.construct,
            id_=f"${self.input.data.identifier}_${config.rule_name}",
            role=role.name,
            policy_arn=policy.arn,
        )

    def create_replication_rule_iam_configuration(
        self, config: S3ReplicationConfiguration
    ) -> None:
        """Creates the necessary IAM objects for a replication configuration"""
        role = self._create_aws_iam_role(config)
        policy = self._create_iam_policy(config)
        self._create_aws_iam_policy_attachment(config, role, policy)


class S3EventNotificationsHelper:
    """Helper class for creating S3 Evet notifications"""

    def __init__(
        self,
        construct: TerraformStack,
        app_interface_input: AppInterfaceInput,
    ) -> None:
        self.construct = construct
        self.input = app_interface_input

    def _get_sqs_queue_arn(self, config: S3EventNotification) -> str:
        if config.destination_identifier.startswith("arn"):
            return config.destination_identifier
        ds_identifier = f"{config.identifier}-sqs-ds"
        DataAwsSqsQueue(self.construct, id_=f"${ds_identifier}", name=config.identifier)
        return f"${{data.aws_sqs_queue.${ds_identifier}.arn}}"

    def _get_sns_topic_arn(self, config: S3EventNotification) -> str:
        if config.destination_identifier.startswith("arn"):
            return config.destination_identifier
        ds_identifier = f"{config.identifier}-sns-ds"
        DataAwsSnsTopic(self.construct, id_=f"${ds_identifier}", name=config.identifier)
        return f"${{data.aws_sns_topic.${ds_identifier}.arn}}"

    def _get_sqs_event_notification(
        self, config: S3EventNotification
    ) -> S3BucketNotificationQueue:
        return S3BucketNotificationQueue(
            events=config.event_type,
            queue_arn=self._get_sqs_queue_arn(config),
            filter_prefix=config.filter_prefix,
            filter_suffix=config.filter_suffix,
        )

    def _get_sns_event_notification(
        self, config: S3EventNotification
    ) -> S3BucketNotificationTopic:
        return S3BucketNotificationTopic(
            events=config.event_type,
            topic_arn=self._get_sns_topic_arn(config),
            filter_prefix=config.filter_prefix,
            filter_suffix=config.filter_suffix,
        )

    def create_s3_bucket_notification(self, bucket_id: str) -> None:
        """Creates the bucket notification configuration"""
        S3BucketNotification(
            self.construct,
            id_=f"{self.input.data.identifier}-event-notifications",
            bucket=bucket_id,
            queue=[
                self._get_sqs_event_notification(config)
                for config in self.input.data.event_notifications or []
                if config.destination_type == "sqs"
            ],
            topic=[
                self._get_sns_event_notification(config)
                for config in self.input.data.event_notifications or []
                if config.destination_type == "sns"
            ],
        )


class Stack(TerraformStack):
    "AWS S3"

    db_dependencies: ClassVar[list[ITerraformDependable]] = []

    def __init__(
        self, scope: Construct, id_: str, app_interface_input: AppInterfaceInput
    ) -> None:
        super().__init__(scope, id_)
        self.input = app_interface_input
        self._init_providers()
        self._run()

    def _init_providers(self) -> None:
        S3Backend(
            self,
            bucket=self.input.provision.module_provision_data.tf_state_bucket,
            key=self.input.provision.module_provision_data.tf_state_key,
            encrypt=True,
            region=self.input.provision.module_provision_data.tf_state_region,
            dynamodb_table=self.input.provision.module_provision_data.tf_state_dynamodb_table,
            profile="external-resources-state",
        )
        AwsProvider(
            self,
            "Aws",
            region=self.input.data.region,
            default_tags=self.input.data.default_tags,
        )

    def _outputs(self) -> None:
        TerraformOutput(
            self,
            self.input.data.output_prefix + "__bucket",
            value=self.input.data.identifier,
        )
        TerraformOutput(
            self,
            self.input.data.output_prefix + "__aws_region",
            value=self.input.data.region,
        )
        TerraformOutput(
            self,
            self.input.data.output_prefix + "__endpoint",
            value=f"s3.{self.input.data.region}.amazonaws.com",
        )

    def _s3_bucket_logging(self) -> None:
        if self.input.data.s3_bucket_logging:
            # Ignore changes
            target_bucket = self.input.data.s3_bucket_logging.get("identifier")
            logging_values = {
                "bucket": f"${{aws_s3_bucket.${self.input.data.identifier}.id}}",
                "target_bucket": f"${{aws_s3_bucket.${target_bucket}.id}}",
                "target_prefix": self.input.data.s3_bucket_logging.get(
                    "target_prefix", ""
                ),
            }
            S3BucketLoggingA(
                id_=f"{self.input.data.identifier}-logging", **logging_values
            )

    def _s3_bucket_ownership_controls(self) -> S3BucketOwnershipControls:
        return S3BucketOwnershipControls(
            self,
            id_="bucket_ownership_controls",
            bucket=self.bucket_obj.id,
            rule=S3BucketOwnershipControlsRule(object_ownership="BucketOwnerPreferred"),
        )

    def _s3_bucket_acl(self) -> None:
        # aws_s3_bucket_public_access_block not implemented for now
        S3BucketAcl(
            self,
            id_="bucket_acl",
            bucket=self.bucket_obj.id,
            acl="private",
            depends_on=[self.bucket_ownership_controls],
        )

    def _s3_server_side_encryption(self) -> None:
        S3BucketServerSideEncryptionConfigurationA(
            self,
            id_="s3ss_enc_conf",
            bucket=self.bucket_obj.id,
            rule=[self.input.data.server_side_encryption_configuration["rule"]],
        )

    def _s3_lifecycle_rules(self) -> None:
        for rule in self.input.data.lifecycle_rules or []:
            rule["status"] = rule["enabled"]
            S3BucketLifecycleConfiguration(
                self, id_=rule["id"], bucket=self.bucket_obj.id, rule=[rule]
            )

    def _s3_bucket(self) -> S3Bucket:
        return S3Bucket(
            self,
            id_=self.input.data.identifier,
            **self.input.data.model_dump(exclude_none=True),
        )

    def _exists_noncurrent_version_expiration_lifecycle_rule(self) -> bool:
        """Returns true if lifecycle rule with a noncurrent_version_expiration exixts"""
        return bool([
            r
            for r in self.input.data.lifecycle_rules or []
            if "noncurrent_version_expiration" in r
        ])

    def _s3_versioning(self) -> None:
        if not self.input.data.versioning:
            return
        S3BucketVersioningA(
            self,
            id_="bucket_versioning",
            bucket=self.bucket_obj.id,
            versioning_configuration=S3BucketVersioningVersioningConfiguration(
                status="Enabled"
            ),
        )
        if not self._exists_noncurrent_version_expiration_lifecycle_rule():
            S3BucketLifecycleConfiguration(
                self,
                id_="noncurrent_version_expiration_lifecycle_rule",
                bucket=self.bucket_obj.id,
                rule=[
                    S3BucketLifecycleConfigurationRule(
                        id="expire_noncurrent_versions",
                        status="Enabled",
                        noncurrent_version_expiration=S3BucketLifecycleConfigurationRuleNoncurrentVersionExpiration(
                            noncurrent_days=30
                        ),
                    )
                ],
            )

    def _s3_storage_class(self) -> None:
        if not self.input.data.storage_class:
            return
        days = 1
        if self.input.data.storage_class in {"STANDARD_IA", "ONEZONE_IA"}:
            # Infrequent Access storage class has minimum 30 days
            # before transition
            days = 30

        S3BucketLifecycleConfiguration(
            self,
            id_="storage_class_lifecycle_rule",
            bucket=self.bucket_obj.id,
            rule=[
                S3BucketLifecycleConfigurationRule(
                    id=f"${self.input.data.storage_class}_storage_class",
                    status="Enabled",
                    noncurrent_version_transition=[
                        S3BucketLifecycleConfigurationRuleNoncurrentVersionTransition(
                            storage_class=self.input.data.storage_class,
                            noncurrent_days=days,
                        )
                    ],
                )
            ],
        )

    def _s3_cors_rules(self) -> None:
        if not self.input.data.cors_rules:
            return
        S3BucketCorsConfiguration(
            self,
            id_="bucket_cors_config",
            bucket=self.bucket_obj.id,
            cors_rule=self.input.data.cors_rules,
        )

    def _s3_replication_configs(self) -> None:
        if not self.input.data.replication_configurations:
            return
        helper = S3ReplicationConfigsHelper(self, self.input)
        for config in self.input.data.replication_configurations:
            helper.create_replication_rule_iam_configuration(config)

    def _s3_event_notifications(self) -> None:
        if not self.input.data.event_notifications:
            return
        helper = S3EventNotificationsHelper(self, self.input)
        helper.create_s3_bucket_notification(self.bucket_obj.id)

    def _s3_bucket_policy(self) -> None:
        if not self.input.data.bucket_policy:
            return
        S3BucketPolicy(
            self,
            id_=f"${self.input.data.identifier}-bucket_policy",
            bucket=self.bucket_obj.id,
            policy=self.input.data.bucket_policy,
        )

    def _get_s3_bucket_iam_policy(self) -> str:
        action = ["s3:*Object"]
        if self.input.data.acl == "public-read":
            action.append("s3:PutObjectAcl")
        if self.input.data.allow_object_tagging:
            action.append("s3:*ObjectTagging")

        return json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "ListObjectsInBucket",
                        "Effect": "Allow",
                        "Action": ["s3:ListBucket", "s3:PutBucketCORS"],
                        "Resource": self.bucket_obj.arn,
                    },
                    {
                        "Sid": "AllObjectActions",
                        "Effect": "Allow",
                        "Action": action,
                        "Resource": f"${self.bucket_obj.arn}/*",
                    },
                ],
            },
            sort_keys=True,
        )

    def _s3_bucket_iam_user(self) -> None:
        user = IamUser(
            self,
            id_=self.input.data.identifier + "_user",
            name=self.input.data.identifier,
            depends_on=[self.bucket_obj],
        )
        key = IamAccessKey(
            self,
            id_=self.input.data.identifier + "_iam_key",
            user=user.id,
            depends_on=[user],
        )

        policy = IamPolicy(
            self,
            id_=self.input.data.identifier + "iam_policy",
            policy=self._get_s3_bucket_iam_policy(),
        )

        IamUserPolicyAttachment(
            self,
            id_=self.input.data.identifier + "iam_policy_attachment",
            user=user.name,
            policy_arn=policy.arn,
        )

        TerraformOutput(
            self,
            id=f"${self.input.data.output_prefix}__aws_access_key_id",
            value=key.id,
            sensitive=True,
        )
        TerraformOutput(
            self,
            id=f"${self.input.data.output_prefix}__aws_secret_access_key",
            value=key.secret,
            sensitive=True,
        )

    def _s3_website(self) -> None:
        if not self.input.data.website:
            return
        S3BucketWebsiteConfiguration(
            self,
            id_=f"{self.input.data.identifier}-website-conf",
            bucket=self.bucket_obj.id,
            **self.input.data.website,
        )

    def _s3_request_payer(self) -> None:
        if not self.input.data.request_payer:
            return

        S3BucketRequestPaymentConfiguration(
            self,
            id_=f"{self.input.data.identifier}-request-payer",
            bucket=self.bucket_obj.id,
            payer=self.input.data.request_payer,
        )

    def _run(self) -> None:
        self.bucket_obj = self._s3_bucket()
        self.bucket_ownership_controls = self._s3_bucket_ownership_controls()
        self._s3_bucket_acl()
        self._s3_bucket_logging()
        self._s3_server_side_encryption()
        self._s3_lifecycle_rules()
        self._s3_versioning()
        self._s3_storage_class()
        self._s3_cors_rules()
        self._s3_replication_configs()
        self._s3_event_notifications()
        self._s3_bucket_policy()
        self._s3_bucket_iam_user()
        self._outputs()
