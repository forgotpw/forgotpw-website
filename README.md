# Forgotpw Website

Static marketing front-end website for www.forgotpw.com.

## Deploy - Dev

Apply Terraform, then execute deployment script.

```shell
export AWS_ENV="dev" && export PROFILE="fpw$AWS_ENV"

chmod +x ./deploy.sh

# pip install iam-starter
iam-starter \
   --profile $PROFILE \
   --command ./deploy.sh
```

## Deploy - Prod

```shell
export AWS_ENV="prod" && export PROFILE="fpw$AWS_ENV"

chmod +x ./deploy.sh

# pip install iam-starter
iam-starter \
   --profile $PROFILE \
   --command ./deploy.sh
```
