# Techstack Justifications

## SvelteKit
SvelteKit is both performant and easy to learn, for a target audience who is
likely to have limited compute resources overhead is a concern. Svelte is
powerful enough to do what we need to do without significant performance
concerns.

## FastAPI
FastAPI is the most approachable API library for us as we're familiar with
Python. Furthermore, it is performant and easy to maintain, without unecessary
verbosity. It's modern, well-maintained and has a reputation.

## AWS Cognito
Using AWS Cognito for authentication saves us work on rolling our own
authentication stack and allows for outbound email for verification and password
resets without configuring SMTP our end.

Furthermore Cognito allows for much easier age-tier and legal compliance within
the UK.

## AWS ECS
For a small team maintained ECS is much easier than EC2.

## AWS RDS
Using RDS allows easier integration with the frontend and backend ECS
containers.

RDS specifically allows for much easier backups, patching and maintenance with
optional Multi-AZ support.

## Github GHCR + CI Automated Building
Automatically building images on merges to main with automatic version tagging
saves significant time when publishing a new release, which at this stage of the
project we are doing quite often. Furthermore, the CI is configured to
automatically redeploy the AWS containers, so the entire process is automated
post-merge.

Hosting on GHCR made sense seeing as how we're already Github-centric when it
comes to development.

## Terraform
Terraform was easier to pickup than CloudFormation just due to the wider usage
of it and more available public documentation. Furthermore the knowledge of
Terraform is provider-agnostic which can help orchestrate more infrastructure
outside AWS.
