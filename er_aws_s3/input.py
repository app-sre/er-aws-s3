from collections.abc import Sequence
from typing import Any, Literal

from external_resources_io.input import AppInterfaceProvision
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

DEFAULT_S3_SSE_CONFIGURATION = {
    "rule": {"apply_server_side_encryption_by_default": {"sse_algorithm": "AES256"}}
}


class S3ReplicationConfiguration(BaseModel):
    "Model Class for replication configurations"

    rule_name: str
    status: str
    destination_bucket_identifier: str
    storage_class: str | None = Field(default=None)


class S3EventNotification(BaseModel):
    """Model class for Event notifications"""

    destination_type: Literal["sns", "sqs"]
    destination_identifier: str
    event_type: list[str]
    filter_prefix: str
    filter_suffix: str

    @property
    @computed_field
    def identifier(self) -> str:
        """Returns the destionation identifier"""
        if self.destination_identifier.startswith("arn:"):
            return self.destination_identifier.split(":")[-1]
        return self.destination_identifier


class S3AppInterface(BaseModel):
    """S3 input data from AppInterface. Theses attributes are defined in AppInterface"""

    identifier: str = Field(exclude=True)
    allow_object_tagging: bool | None = Field(default=False, exclude=True)
    bucket_policy: str | None = Field(default=None)
    replication_configurations: list[S3ReplicationConfiguration] | None = Field(
        default=None, exclude=True
    )
    event_notifications: list[S3EventNotification] | None = Field(
        default=None, exclude=True
    )
    s3_bucket_logging: dict[str, Any] | None = Field(default=None, exclude=True)
    region: str = Field(default="us-east-1", exclude=True)
    default_tags: Sequence[dict[str, Any]] = Field(default=None, exclude=True)
    output_prefix: str = Field(exclude=True)

    # Deprecated attributes in aws_s3_bucket
    acl: (
        Literal[
            "private",
            "public-read",
            "public-read-write",
            "aws-exec-read",
            "authenticated-read",
            "bucket-owner-read",
            "bucket-owner-full-control",
        ]
        | None
    ) = Field(default=None, exclude=True)
    cors_rules: list[dict[str, Any]] | None = Field(default=None, exclude=True)
    lifecycle_rules: list[dict[str, Any]] | None = Field(default=None, exclude=True)
    request_payer: Literal["BucketOwner", "Requester"] | None = Field(
        default=None, exclude=True
    )
    server_side_encryption_configuration: dict[str, Any] = DEFAULT_S3_SSE_CONFIGURATION
    #    sqs_identifier: str | None = Field(default=None)
    storage_class: (
        Literal[
            "GLACIER",
            "STANDARD_IA",
            "ONEZONE_IA",
            "INTELLIGENT_TIERING",
            "DEEP_ARCHIVE",
            "GLACIER_IR",
        ]
        | None
    ) = Field(default=None, exclude=True)
    versioning: bool | dict[str, bool] = Field(default=True, exclude=True)
    website: dict[str, Any] | None = Field(default=None, exclude=True)


class S3(S3AppInterface):
    """S3 bucket Terraform attributes"""

    model_config = ConfigDict(extra="allow")
    bucket_prefix: str | None = Field(default=None)
    force_destroy: bool | None = Field(default=None)
    object_lock_enabled: bool | None = Field(default=None)
    tags: dict[str, Any] | None = Field(default=None)

    @model_validator(mode="after")
    def bucket_identifier(self) -> "S3":
        """Assigns identifier to bucket"""
        self.bucket = self.identifier
        return self

    @field_validator("storage_class", mode="before")
    @classmethod
    def upper_storage_class(cls, v: str) -> str:
        """AppInterface allows lowercase values"""
        return v.upper()


class AppInterfaceInput(BaseModel):
    """The input model class"""

    data: S3
    provision: AppInterfaceProvision
