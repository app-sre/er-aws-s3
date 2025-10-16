# External Resources S3 Module

External Resources module to provision and manage S3 buckets in AWS with App-Interface.

## Tech stack

* Terraform
* AWS provider
* Random provider
* Python 3.12
* Pydantic

## Development

Ensure `uv` is installed.

Prepare local development environment:

```shell
make dev
```

This will auto create a `venv`, to activate in shell:

```shell
source .venv/bin/activate
```

## Debugging

Export `input.json` via `qontract-cli` and place it in the current project root dir.

```shell
qontract-cli --config $CONFIG external-resources --provisioner $PROVISIONER --provider $PROVIDER --identifier $IDENTIFIER get-input > input.json
```

Get `credentials`

```shell
qontract-cli --config $CONFIG external-resources --provisioner $PROVISIONER --provider $PROVIDER --identifier $IDENTIFIER get-credentials > credentials
```

Optional config `.env`:

```shell
cp .env.example .env
```

Populate `.env` values with absolute path

Export to current shell

```shell
export $(cat .env | xargs)
```

### On Host

Generate terraform config.

```shell
generate-tf-config
```

Ensure AWS credentials set in current shell, then use `terraform` to verify.

```shell
cd module
terraform init
terraform plan -out=plan
terraform show -json plan > plan.json
```

Test hooks

```shell
hooks/post_plan.py
```

### In Container

Build image first

```shell
make build
```

Start container

```shell
docker run --rm -ti \
  --entrypoint /bin/bash \
  -v $PWD/input.json:/inputs/input.json:Z \
  -v $PWD/credentials:/credentials:Z \
  -e AWS_SHARED_CREDENTIALS_FILE=/credentials \
  -e WORK=/tmp/work \
  er-aws-s3:prod
```

Run the whole process

```shell
./entrypoint.sh
```
