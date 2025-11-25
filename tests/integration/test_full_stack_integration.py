"""
統合テストスイート - AMI・インスタンス設定機能の完全なワークフローテスト
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import aws_cdk as core
import aws_cdk.assertions as assertions
from ssm_ec2_rdp.ssm_ec2_rdp_stack import SsmEc2RdpStack
from ssm_ec2_rdp.configuration_manager import ConfigurationManager
from ssm_ec2_rdp.types import (
    EC2Configuration,
    AMIConfiguration,
    InstanceConfiguration,
    AMIInfo,
    OSType,
    ConfigurationError,
    MissingConfigError,
    ConfigConflictError,
    InvalidValueError,
    AMINotFoundError,
    KeyPairNotFoundError
)
from .test_helpers import (
    MockMachineImage,
    MockKeyPair,
    create_test_app_with_context,
    assert_cloudformation_resources,
    create_integration_test_config,
    IntegrationTestBase
)


class TestFullStackIntegration(IntegrationTestBase):
    """完全なスタック統合テスト"""
    
    def test_ami_id_windows_with_keypair_integration(self):
        """AMI ID + Windows + Key Pair の完全ワークフローテスト"""
        context_data = create_integration_test_config("ami-id", "t3.medium", "test-key")
        app = create_test_app_with_context(context_data)
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            # CDK互換のモックオブジェクトを使用
            mock_machine_image = MockMachineImage("ami-0123456789abcdef0")
            mock_key_pair = MockKeyPair("test-key")
            
            mock_resolve.return_value = (
                mock_machine_image,
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            mock_get_key_pair.return_value = mock_key_pair
            
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            stack_id = self.create_unique_stack_id("integration-test-stack")
            stack = SsmEc2RdpStack(app, stack_id, config)
            template = assertions.Template.from_stack(stack)
            
            # CloudFormationテンプレート検証
            template.resource_count_is("AWS::EC2::VPC", 1)
            template.resource_count_is("AWS::EC2::Instance", 1)
            template.resource_count_is("AWS::EC2::SecurityGroup", 2)
            template.resource_count_is("AWS::IAM::Role", 1)
            template.has_resource("AWS::EC2::VPCEndpoint", {})
            template.has_resource("AWS::EC2::InstanceConnectEndpoint", {})
            
            # Windows固有の検証
            template.has_resource_properties("AWS::EC2::SecurityGroup", {
                "GroupDescription": "Security group for SSM EC2 RDP access"
            })
    
    def test_ssm_parameter_linux_no_keypair_integration(self):
        """SSMパラメータ + Linux + Key Pairなし の完全ワークフローテスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        
        app.node.set_context("ami-parameter", "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2")
        app.node.set_context("instance-type", "m5.large")
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(),
                AMIInfo(ami_id="ami-linux123", os_type=OSType.LINUX, description="Amazon Linux")
            )
            
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            stack = SsmEc2RdpStack(app, "linux-test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # 基本リソース検証
            template.resource_count_is("AWS::EC2::VPC", 1)
            template.resource_count_is("AWS::EC2::Instance", 1)
            template.resource_count_is("AWS::IAM::Role", 1)
    
    @pytest.mark.parametrize("instance_type", [
        "t3.micro", "t3.medium", "m5.large", "c5.xlarge", "r5.2xlarge"
    ])
    def test_various_instance_types_integration(self, instance_type):
        """様々なインスタンスタイプでの統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", instance_type)
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(),
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            stack = SsmEc2RdpStack(app, f"test-{instance_type.replace('.', '-')}", config)
            template = assertions.Template.from_stack(stack)
            
            # インスタンス作成の確認
            template.has_resource("AWS::EC2::Instance", {})


class TestConfigurationIntegration:
    """設定管理の統合テスト"""
    
    def test_configuration_manager_full_workflow(self):
        """ConfigurationManager完全ワークフローテスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        app.node.set_context("key-pair-name", "test-key")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # 設定の正確性を検証
        assert isinstance(config, EC2Configuration)
        assert isinstance(config.ami, AMIConfiguration)
        assert isinstance(config.instance, InstanceConfiguration)
        
        assert config.ami.ami_id == "ami-0123456789abcdef0"
        assert config.instance.instance_type == "t3.medium"
        assert config.instance.key_pair_name == "test-key"


class TestErrorHandlingIntegration:
    """エラーハンドリング統合テスト"""
    
    def test_missing_ami_configuration_error(self):
        """AMI設定不足エラーの統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("instance-type", "t3.medium")  # AMI設定なし
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(MissingConfigError) as exc_info:
            config_manager.get_configuration()
        
        assert "AMI設定が必要です" in str(exc_info.value)
    
    def test_conflicting_ami_configuration_error(self):
        """AMI設定競合エラーの統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("ami-parameter", "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base")
        app.node.set_context("instance-type", "t3.medium")
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(ConfigConflictError) as exc_info:
            config_manager.get_configuration()
        
        assert "両方を指定することはできません" in str(exc_info.value)
    
    def test_invalid_instance_type_error(self):
        """無効インスタンスタイプエラーの統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "invalid.type")
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(InvalidValueError) as exc_info:
            config_manager.get_configuration()
        
        assert "無効なインスタンスタイプ形式" in str(exc_info.value)
    
    def test_ami_not_found_stack_error(self):
        """AMI見つからないエラーのスタック統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.side_effect = AMINotFoundError("AMI not found")
            
            with pytest.raises(ConfigurationError) as exc_info:
                SsmEc2RdpStack(app, "error-test-stack", config)
            
            assert "設定エラーが発生しました" in str(exc_info.value)
    
    def test_keypair_not_found_stack_error(self):
        """Key Pair見つからないエラーのスタック統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        app.node.set_context("key-pair-name", "nonexistent-key")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            mock_resolve.return_value = (
                Mock(),
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            mock_get_key_pair.side_effect = KeyPairNotFoundError("Key Pair not found")
            
            with pytest.raises(ConfigurationError) as exc_info:
                SsmEc2RdpStack(app, "keypair-error-test-stack", config)
            
            assert "設定エラーが発生しました" in str(exc_info.value)


class TestCloudFormationTemplateIntegration:
    """CloudFormationテンプレート検証統合テスト"""
    
    def test_windows_template_resources_validation(self):
        """Windows用テンプレートリソース検証"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-parameter", "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base")
        app.node.set_context("instance-type", "t3.medium")
        app.node.set_context("key-pair-name", "test-key")
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            mock_resolve.return_value = (
                Mock(),
                AMIInfo(ami_id="ami-windows", os_type=OSType.WINDOWS, description="Windows Server 2022")
            )
            mock_get_key_pair.return_value = Mock()
            
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            stack = SsmEc2RdpStack(app, "windows-template-test", config)
            template = assertions.Template.from_stack(stack)
            
            # Windows固有リソースの検証
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
            
            # SSMマネージドポリシーがアタッチされていることを確認
            template.has_resource_properties("AWS::IAM::Role", {
                "ManagedPolicyArns": [
                    {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {"Ref": "AWS::Partition"},
                                ":iam::aws:policy/AmazonSSMManagedInstanceCore"
                            ]
                        ]
                    }
                ]
            })
    
    def test_security_configuration_validation(self):
        """セキュリティ設定検証統合テスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
            mock_resolve.return_value = (
                Mock(),
                AMIInfo(ami_id="ami-0123456789abcdef0", os_type=OSType.WINDOWS, description="Windows Server")
            )
            
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            stack = SsmEc2RdpStack(app, "security-test-stack", config)
            template = assertions.Template.from_stack(stack)
            
            # セキュリティグループ設定の検証
            template.has_resource_properties("AWS::EC2::SecurityGroup", {
                "GroupDescription": "Security group for SSM EC2 RDP access",
                "SecurityGroupEgress": [
                    {
                        "CidrIp": "0.0.0.0/0",
                        "Description": "HTTPS outbound for SSM",
                        "FromPort": 443,
                        "IpProtocol": "tcp",
                        "ToPort": 443
                    }
                ]
            })
            
            # VPCエンドポイントの確認（プライベートアクセス用）
            template.has_resource("AWS::EC2::VPCEndpoint", {})
    
    def test_performance_requirements_validation(self):
        """パフォーマンス要件検証"""
        # このテストは失敗するはず（実装前）
        import time
        
        start_time = time.time()
        
        # 複数のスタック作成を同時実行（パフォーマンステスト）
        test_configs = [
            {"ami-id": "ami-0123456789abcdef0", "instance-type": "t3.micro"},
            {"ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base", "instance-type": "m5.large"},
            {"ami-id": "ami-linux123456789ab", "instance-type": "c5.xlarge"},
        ]
        
        for i, config_data in enumerate(test_configs):
            app = core.App()
            for key, value in config_data.items():
                app.node.set_context(key, value)
            
            with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
                mock_resolve.return_value = (
                    Mock(),
                    AMIInfo(ami_id=f"ami-test{i}", os_type=OSType.WINDOWS, description=f"Test AMI {i}")
                )
                
                config_manager = ConfigurationManager(app)
                config = config_manager.get_configuration()
                
                stack = SsmEc2RdpStack(app, f"perf-test-stack-{i}", config)
                template = assertions.Template.from_stack(stack)
                
                # 基本リソースの存在確認
                template.has_resource("AWS::EC2::Instance", {})
        
        execution_time = time.time() - start_time
        
        # パフォーマンス要件: 3分以内（180秒）
        assert execution_time < 180, f"テスト実行時間が要件を超えています: {execution_time:.2f}秒"


class TestEndToEndIntegration:
    """End-to-End 統合テスト"""
    
    def test_complete_deployment_workflow(self):
        """完全なデプロイメントワークフローテスト"""
        # このテストは失敗するはず（実装前）
        app = core.App()
        
        # 実際のcdk.jsonと同様の設定
        app.node.set_context("ami-parameter", "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base")
        app.node.set_context("instance-type", "t3.medium")
        app.node.set_context("key-pair-name", "test-key")
        
        with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve, \
             patch('ssm_ec2_rdp.key_pair_manager.KeyPairManager.get_key_pair') as mock_get_key_pair:
            
            mock_resolve.return_value = (
                Mock(),
                AMIInfo(ami_id="ami-windows", os_type=OSType.WINDOWS, description="Windows Server 2022 Japanese")
            )
            mock_get_key_pair.return_value = Mock()
            
            # ConfigurationManager → Stack作成の完全フロー
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            # スタック作成
            stack = SsmEc2RdpStack(app, "SsmEc2RdpDynamicStack-Integration", config)
            
            # CloudFormation合成（synthに相当）
            template = assertions.Template.from_stack(stack)
            
            # 全必要リソースの存在確認
            required_resources = [
                "AWS::EC2::VPC",
                "AWS::EC2::Subnet", 
                "AWS::EC2::SecurityGroup",
                "AWS::EC2::Instance",
                "AWS::EC2::VPCEndpoint",
                "AWS::EC2::InstanceConnectEndpoint",
                "AWS::IAM::Role",
                "AWS::IAM::InstanceProfile"
            ]
            
            for resource_type in required_resources:
                template.has_resource(resource_type, {})
            
            # リソース数の妥当性確認
            template.resource_count_is("AWS::EC2::VPC", 1)
            template.resource_count_is("AWS::EC2::Instance", 1)
            template.resource_count_is("AWS::IAM::Role", 1)
            
            # 最終的な整合性チェック
            assert True  # すべてのチェックが通れば成功