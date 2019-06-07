# Forgotpw Website

**NOTE: Rosa (www.rosa.bot) is the new name for ForgotPW**

Static marketing front-end website for www.rosa.bot.

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
