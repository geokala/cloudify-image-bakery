# Cloudify AMI builder

## How to use this?

# TODO: Improve prerequisites instructions and listing- make script to verify? What OSes are supported for running this on?
1. Install prerequisites (packer, aws CLI)
2. Copy the sample vars file for the environment you are using (e.g. inputs_aws-example.json) and edit it as appropriate. Note that you should generally not change values that are not an all caps description of what the variable is for unless you have good reason.
# TODO: Improve packer run information to allow for different types once they exist, and to account for different var file naming
3. Run `packer build -var-file inputs_aws.json cloudify_aws.json`

## Prerequisites

1. Packer 0.8.6+ (Older versions were not tested)

## Copying AMI to different regions (manually)

1. Copy: `aws ec2 copy-image --source-image-id <source_ami> --source-region <region> --region <dest_region> --name "Cloudify <version> Release"`
2. Make public: `aws ec2 modify-image-attribute --image-id <image_id> --region <image_region> --launch-permission "{\"Add\":[{\"Group\":\"all\"}]}"`
