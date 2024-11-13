## Workmait Python Microservices Template

This template comes built-in with the following:

1. **Blank requirements.txt**
2. **Dockerfile with only a base python version**
3. **An extensible CI-CD workflow for dev, staging, and production**

## How to use the dev and production workflows

The CI-CD flow is set up so that pushes to the staging branch build the staging docker image and push to a repo. The repo is not 100% configured as writing this so many need to tweak slightly. However, the Docker image will push a 'staging' image to it. The goal of that is to pair with a script for deploying to AWS with non-production dependencies (i.e. Mongo, diff user pool for auth via Cognito, etc). This will also trigger integration tests between services via the central repo.
