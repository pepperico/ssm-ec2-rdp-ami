"""
SsmEc2RdpStackの統合テスト
"""
import pytest
from unittest.mock import Mock, patch
import aws_cdk as core
import aws_cdk.assertions as assertions
from ssm_ec2_rdp.ssm_ec2_rdp_stack import SsmEc2RdpStack
from ssm_ec2_rdp.types import (
    EC2Configuration, 
    AMIConfiguration, 
    InstanceConfiguration,
    AMIInfo,
    OSType,
    ConfigurationError
)


class TestSsmEc2RdpStack:
    """SsmEc2RdpStackクラスのテスト"""
    
    def test_stack_creation_with_ami_id(self):
        """AMI ID直接指定でのスタック作成テスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
            instance=InstanceConfiguration(instance_type="t3.medium")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # VPCが作成されることを確認
            template.has_resource_properties("AWS::EC2::VPC", {
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True
            })
            
            # EC2インスタンスが作成されることを確認
            template.has_resource("AWS::EC2::Instance", {})
            
            # セキュリティグループが作成されることを確認
            template.has_resource("AWS::EC2::SecurityGroup", {})
            
            # IAMロールが作成されることを確認
            template.has_resource("AWS::IAM::Role", {})
    
    def test_stack_creation_with_ssm_parameter(self):
        """SSMパラメータ指定でのスタック作成テスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"),
            instance=InstanceConfiguration(instance_type="m5.large", key_pair_name="test-key")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-87654321abcdef012", os_type=OSType.WINDOWS, description="Windows Server")
            )
            mock_get_key_pair.return_value = Mock()
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # EC2インスタンスが作成されることを確認
            template.has_resource("AWS::EC2::Instance", {})
    
    def test_stack_creation_with_linux_ami(self):
        """Linux AMIでのスタック作成テスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-linux123456789ab"),
            instance=InstanceConfiguration(instance_type="t3.small")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-linux123456789ab", os_type=OSType.LINUX, description="Amazon Linux")
            )
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # スタックが正常に作成されることを確認
            template.has_resource("AWS::EC2::Instance", {})
    
    def test_stack_creation_with_key_pair(self):
        """Key Pair指定でのスタック作成テスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
            instance=InstanceConfiguration(instance_type="c5.xlarge", key_pair_name="my-key-pair")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            mock_get_key_pair.return_value = Mock()
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # EC2インスタンスが作成されることを確認
            template.has_resource("AWS::EC2::Instance", {})
    
    def test_stack_creation_invalid_instance_type(self):
        """無効なインスタンスタイプでのエラーテスト"""
        app = core.App()
        
        # 無効なインスタンスタイプは型定義のレベルで弾かれる
        with pytest.raises(Exception):  # InvalidValueError or ConfigurationError
            config = EC2Configuration(
                ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
                instance=InstanceConfiguration(instance_type="invalid.type")
            )
    
    def test_stack_creation_ami_not_found(self):
        """AMI見つからないエラーのテスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
            instance=InstanceConfiguration(instance_type="t3.medium")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            from ssm_ec2_rdp.types import AMINotFoundError
            mock_resolve.side_effect = AMINotFoundError("AMI not found")
            
            with pytest.raises(ConfigurationError) as exc_info:
                SsmEc2RdpStack(app, "test-stack", config)
            
            assert "設定エラーが発生しました" in str(exc_info.value)
    
    def test_stack_vpc_endpoints_creation(self):
        """VPCエンドポイント作成のテスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
            instance=InstanceConfiguration(instance_type="t3.medium")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # VPCエンドポイントが作成されることを確認
            template.has_resource("AWS::EC2::VPCEndpoint", {})
    
    def test_stack_security_group_configuration(self):
        """セキュリティグループ設定のテスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
            instance=InstanceConfiguration(instance_type="t3.medium")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # セキュリティグループが適切に設定されることを確認
            template.has_resource_properties("AWS::EC2::SecurityGroup", {
                "GroupDescription": "Security group for SSM EC2 RDP access"
            })
    
    def test_stack_iam_role_configuration(self):
        """IAMロール設定のテスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-0123456789abcdef0"),
            instance=InstanceConfiguration(instance_type="t3.medium")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            
            stack = SsmEc2RdpStack(app, "test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # IAMロールが適切に設定されることを確認
            template.has_resource_properties("AWS::IAM::Role", {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "ec2.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
            })


class TestSsmEc2RdpStackIntegration:
    """SsmEc2RdpStackの統合テスト"""
    
    def test_complete_stack_workflow_windows(self):
        """Windows AMIでの完全なスタック作成ワークフローテスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"),
            instance=InstanceConfiguration(instance_type="t3.medium", key_pair_name="test-key")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-windows123456789", os_type=OSType.WINDOWS, description="Windows Server 2022")
            )
            mock_get_key_pair.return_value = Mock()
            
            # スタック作成
            stack = SsmEc2RdpStack(app, "integration-test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # 主要リソースの存在確認
            template.resource_count_is("AWS::EC2::VPC", 1)
            template.resource_count_is("AWS::EC2::Instance", 1)
            template.resource_count_is("AWS::EC2::SecurityGroup", 2)  # インスタンス用 + EICE用
            template.resource_count_is("AWS::IAM::Role", 1)
            template.has_resource("AWS::EC2::VPCEndpoint", {})
            template.has_resource("AWS::EC2::InstanceConnectEndpoint", {})
    
    def test_complete_stack_workflow_linux(self):
        """Linux AMIでの完全なスタック作成ワークフローテスト"""
        app = core.App()
        
        config = EC2Configuration(
            ami=AMIConfiguration(ami_id="ami-linux123456789ab"),
            instance=InstanceConfiguration(instance_type="m5.large")
        )
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(), 
                AMIInfo(ami_id="ami-linux123456789ab", os_type=OSType.LINUX, description="Amazon Linux 2023")
            )
            
            # スタック作成
            stack = SsmEc2RdpStack(app, "linux-integration-test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # 主要リソースの存在確認
            template.resource_count_is("AWS::EC2::VPC", 1)
            template.resource_count_is("AWS::EC2::Instance", 1)
            template.resource_count_is("AWS::EC2::SecurityGroup", 2)
            template.resource_count_is("AWS::IAM::Role", 1)