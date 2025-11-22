# Deploying YouTube Transcript API on AWS Free Tier

## Option 1: AWS Elastic Beanstalk

### Prerequisites

- AWS CLI installed and configured (aws configure)
- Docker installed
- An AWS account with Free Tier eligibilty

### Steps

1. Prepare the Application
   - Ensure main.py, Dockerfile, and requirements.txt are in your project directory.
   - Create a Dockerrun.aws.json file

{"AWSEBDockerrunVersion": "1", "Image":{"Name": "", "Update": "true"}, "Ports":[{"ContainerPort": 8000, "HostPort": 80}]}
