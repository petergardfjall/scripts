This directory contains utility scripts for working with docker registries.


## Transfer images between registries

The scripts can be used to transfer images from a remote Docker registry `A`
to a different remote registry `B`.

For example, to transfer from the local `a.mydocker.com` to the Amazon ECR
registry `123456789123.dkr.ecr.us-east-1.amazonaws.com`, follow these steps:

1. Log in to `a.mydocker.com`:

        docker login -u foo -p bar a.mydocker.com

1. Set your AWS account credentials

        export AWS_ACCESS_KEY_ID="ABC..123"
        export AWS_SECRET_ACCESS_KEY="DEF...456"
        export AWS_DEFAULT_REGION="us-east-1

2. Create temporary docker login credentials and log in to the AWS registry:

        eval $(aws ecr get-login --no-include-email --region us-east-1)

3. List the images from the source registry (with tags):

        ./list-remote-images.sh --show-tags a.mydocker.com > images.txt

4. Edit `images.txt` to only include images (and tags) that you want to
   transfer.

5. Make sure a "repoistory" exists for every image in AWS ECR:

        cat my-images.txt | ./aws-create-ecr-repo.sh 123456789123.dkr.ecr.us-east-1.amazonaws.com

5. Copy images from source to destination.

        cat my-images.txt | ./copy-images.sh a.mydocker.com 123456789123.dkr.ecr.us-east-1.amazonaws.com
