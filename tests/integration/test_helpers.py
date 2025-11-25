"""
統合テスト用ヘルパー関数とフィクスチャ
"""
import pytest
from unittest.mock import Mock, MagicMock
from aws_cdk import aws_ec2 as ec2
from ssm_ec2_rdp.types import AMIInfo, OSType


class MockMachineImage:
    """CDK MachineImage互換のモック"""
    
    def __init__(self, ami_id: str = "ami-test123456789ab"):
        self.ami_id = ami_id
        self.__jsii_type__ = "aws-cdk-lib.aws_ec2.IMachineImage"
    
    def get_image(self, scope, **kwargs):
        """CDK MachineImage互換メソッド"""
        return Mock()


class MockKeyPair:
    """CDK KeyPair互換のモック"""
    
    def __init__(self, key_name: str = "test-key"):
        self.key_name = key_name
        self.__jsii_type__ = "aws-cdk-lib.aws_ec2.IKeyPair"


@pytest.fixture
def mock_windows_ami_info():
    """Windows AMI情報のフィクスチャ"""
    return AMIInfo(
        ami_id="ami-0123456789abcdef0",
        os_type=OSType.WINDOWS,
        description="Windows Server 2022 Japanese"
    )


@pytest.fixture
def mock_linux_ami_info():
    """Linux AMI情報のフィクスチャ"""
    return AMIInfo(
        ami_id="ami-linux123456789ab",
        os_type=OSType.LINUX,
        description="Amazon Linux 2023"
    )


@pytest.fixture
def mock_cdk_machine_image():
    """CDK互換のMachineImageモック"""
    return MockMachineImage()


@pytest.fixture
def mock_cdk_keypair():
    """CDK互換のKeyPairモック"""
    return MockKeyPair()


def create_test_app_with_context(context_data: dict):
    """テスト用のCDK Appとコンテキストを作成"""
    import aws_cdk as core
    
    app = core.App()
    for key, value in context_data.items():
        app.node.set_context(key, value)
    
    return app


def assert_cloudformation_resources(template, expected_resources: dict):
    """CloudFormationリソースの存在確認ヘルパー"""
    for resource_type, count in expected_resources.items():
        if count > 0:
            template.resource_count_is(resource_type, count)
        else:
            template.has_resource(resource_type, {})


def assert_security_configuration(template):
    """セキュリティ設定の妥当性確認ヘルパー"""
    # セキュリティグループの基本設定確認
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "GroupDescription": "Security group for SSM EC2 RDP access"
    })
    
    # IAMロールの確認
    template.has_resource_properties("AWS::IAM::Role", {
        "AssumeRolePolicyDocument": {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    })


def create_integration_test_config(ami_type="ami-id", instance_type="t3.medium", key_pair_name=None):
    """統合テスト用の設定作成ヘルパー"""
    context = {"instance-type": instance_type}
    
    if ami_type == "ami-id":
        context["ami-id"] = "ami-0123456789abcdef0"
    elif ami_type == "ami-parameter":
        context["ami-parameter"] = "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
    
    if key_pair_name:
        context["key-pair-name"] = key_pair_name
    
    return context


class IntegrationTestBase:
    """統合テスト用ベースクラス"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.test_counter = 0
    
    def create_unique_stack_id(self, base_name: str) -> str:
        """ユニークなスタックIDを生成"""
        self.test_counter += 1
        return f"{base_name}-{self.test_counter}"
    
    def verify_basic_resources(self, template):
        """基本リソースの存在確認"""
        basic_resources = {
            "AWS::EC2::VPC": 1,
            "AWS::EC2::Instance": 1,
            "AWS::IAM::Role": 1
        }
        assert_cloudformation_resources(template, basic_resources)
    
    def verify_windows_resources(self, template):
        """Windows固有リソースの確認"""
        self.verify_basic_resources(template)
        
        # Windows固有の追加確認があればここに追加
        template.has_resource("AWS::EC2::InstanceConnectEndpoint", {})
        template.has_resource("AWS::EC2::VPCEndpoint", {})
    
    def verify_linux_resources(self, template):
        """Linux固有リソースの確認"""
        self.verify_basic_resources(template)
        
        # Linux固有の追加確認があればここに追加
        # 現在はWindows環境と同じリソース構成