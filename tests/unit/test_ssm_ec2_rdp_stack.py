import aws_cdk as core
import aws_cdk.assertions as assertions

from ssm_ec2_rdp.ssm_ec2_rdp_stack import SsmEc2RdpStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ssm_ec2_rdp/ssm_ec2_rdp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SsmEc2RdpStack(app, "ssm-ec2-rdp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
