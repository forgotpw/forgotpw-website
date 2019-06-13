# Forgotpw Website

**NOTE: Rosa (www.rosa.bot) is the new name for ForgotPW**

Static marketing front-end website for www.rosa.bot.

## Deploy - Dev

Apply Terraform, then execute deployment script.

```shell
# pip install iam-starter

export AWS_ENV="dev" && export PROFILE="fpw$AWS_ENV"

iam-starter \
   --profile $PROFILE \
   --command ./deploy.sh
```

## Deploy - Prod

```shell
# pip install iam-starter

export AWS_ENV="prod" && export PROFILE="fpw$AWS_ENV"

iam-starter \
   --profile $PROFILE \
   --command ./deploy.sh
```
