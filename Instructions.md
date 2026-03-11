Build and Push Docker Image

    Build the Docker image:
    bash

docker build -t youtube-transcript-api .
Tag and push to Amazon ECR (create a repository in ECR first):
bash

    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
    docker tag youtube-transcript-api:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/youtube-transcript-api:latest
    docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/youtube-transcript-api:latest
    Update Dockerrun.aws.json with the ECR image URL.

Deploy to Elastic Beanstalk

    Initialize Elastic Beanstalk:
    bash

eb init -p docker youtube-transcript-api --region us-east-1
Create an environment:
bash
eb create youtube-transcript-env --single
Deploy the application:
bash

    eb deploy

Access the API

    Get the endpoint: eb open
    Test the endpoint using a tool like curl or Postman:
    bash

        curl -X POST -F "file=@urls.txt" http://<your-eb-endpoint>/transcripts/

Notes

    The Free Tier includes 750 hours/month of t2.micro instances, sufficient for a single-instance Elastic Beanstalk environment.
    Monitor usage to stay within Free Tier limits.

Option 2: AWS ECS Fargate
Steps

    Create an ECS Cluster
        In the AWS Console, navigate to ECS > Clusters > Create Cluster.
        Choose "Networking only" (Fargate) and create.
    Create a Task Definition
        In ECS, create a new task definition (Fargate).
        Add a container with your Docker image from ECR.
        Set container port to 8000 and allocate 0.5 vCPU and 2GB memory (Free Tier eligible).
    Create a Service
        Create a service in the cluster, selecting the task definition.
        Use an Application Load Balancer (ALB) and map port 80 to 8000.
        Configure a target group for health checks on /health (add a health endpoint in main.py if needed).
    Push Docker Image to ECR
        Follow the same steps as in Elastic Beanstalk to push the image to ECR.
    Deploy and Test
        Deploy the service and wait for the ALB endpoint.
        Test the API using the ALB DNS name.

Notes

    Fargate Free Tier includes 400,000 seconds/month of vCPU usage. Use sparingly to avoid charges.
    Ensure security groups allow inbound traffic on port 80.

Testing Locally

    Run locally with Docker Compose:
    bash

docker-compose up --build
Test the endpoint:
bash
curl -X POST -F "file=@urls.txt" http://localhost:8000/transcripts/
Example urls.txt:
text

    https://www.youtube.com/watch?v=rVSb0u9OTtM
    https://www.youtube.com/watch?v=another-video-id

Cleanup

    Terminate Elastic Beanstalk environment or ECS service to avoid charges.
    Delete ECR images if no longer needed.

Usage Instructions:

    Prepare the URLs File:
        Create a urls.txt file with one YouTube URL per line, e.g.:
        text

    https://www.youtube.com/watch?v=rVSb0u9OTtM
    https://www.youtube.com/watch?v=another-video-id

Run Locally:

    Install Docker and Docker Compose.
    Save the provided files (main.py, Dockerfile, requirements.txt, docker-compose.yml) in a directory.
    Run docker-compose up --build.
    Test the API with:
    bash

        curl -X POST -F "file=@urls.txt" http://localhost:8000/transcripts/
    Deploy to AWS:
        Follow the instructions in the AWS Deployment Instructions artifact.
        Use either Elastic Beanstalk for simplicity or ECS Fargate for more control.
    API Response:
        The API returns a JSON list of objects, each containing:
            video_id: The extracted YouTube video ID.
            transcript: The transcript text (if successful).
            status: "success" or "error".
            error: Error message (if applicable).

Note:

    The Free Tier has limits; monitor usage via the AWS Billing Dashboard.
    The API does not save transcripts to files (unlike the original code) to keep it stateless for cloud deployment. If you need file storage, consider adding an S3 integration.
