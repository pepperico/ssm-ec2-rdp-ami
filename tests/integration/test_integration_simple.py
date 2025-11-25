"""
簡素化された統合テストスイート - 実際に動作可能なテスト
"""
import pytest
from unittest.mock import patch, MagicMock
import aws_cdk as core
import aws_cdk.assertions as assertions
from ssm_ec2_rdp.configuration_manager import ConfigurationManager
from ssm_ec2_rdp.types import (
    AMIInfo,
    OSType,
    ConfigurationError,
    MissingConfigError,
    ConfigConflictError,
    InvalidValueError
)


class TestConfigurationIntegration:
    """設定管理の統合テスト"""
    
    def test_configuration_manager_ami_id_workflow(self):
        """ConfigurationManager AMI ID ワークフローテスト"""
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        app.node.set_context("key-pair-name", "test-key")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # 設定の正確性を検証
        assert config.ami.ami_id == "ami-0123456789abcdef0"
        assert config.ami.ami_parameter is None
        assert config.instance.instance_type == "t3.medium"
        assert config.instance.key_pair_name == "test-key"
    
    def test_configuration_manager_ssm_parameter_workflow(self):
        """ConfigurationManager SSMパラメータ ワークフローテスト"""
        app = core.App()
        app.node.set_context("ami-parameter", "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base")
        app.node.set_context("instance-type", "m5.large")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # 設定の正確性を検証
        assert config.ami.ami_id is None
        assert config.ami.ami_parameter == "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        assert config.instance.instance_type == "m5.large"
        assert config.instance.key_pair_name is None
    
    def test_configuration_manager_missing_ami_error(self):
        """ConfigurationManager AMI設定不足エラーテスト"""
        app = core.App()
        app.node.set_context("instance-type", "t3.medium")
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.get_configuration()
        
        assert "AMI設定が必要です" in str(exc_info.value)
    
    def test_configuration_manager_conflicting_ami_error(self):
        """ConfigurationManager AMI設定競合エラーテスト"""
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("ami-parameter", "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base")
        app.node.set_context("instance-type", "t3.medium")
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.get_configuration()
        
        assert "両方を指定することはできません" in str(exc_info.value)
    
    def test_configuration_manager_missing_instance_type_error(self):
        """ConfigurationManager インスタンスタイプ不足エラーテスト"""
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.get_configuration()
        
        assert "instance-typeは必須設定項目です" in str(exc_info.value)
    
    def test_configuration_manager_invalid_instance_type_error(self):
        """ConfigurationManager 無効インスタンスタイプエラーテスト"""
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "invalid.type")
        
        config_manager = ConfigurationManager(app)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config_manager.get_configuration()
        
        assert "無効なインスタンスタイプ形式" in str(exc_info.value)


class TestComponentIntegration:
    """コンポーネント間統合テスト"""
    
    def test_ami_resolver_with_configuration_manager(self):
        """AMIResolver と ConfigurationManager の統合テスト"""
        from ssm_ec2_rdp.ami_resolver import AMIResolver
        
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # モックスタックを作成
        mock_stack = MagicMock()
        mock_stack.region = "us-west-2"
        
        ami_resolver = AMIResolver(mock_stack)
        
        # AMI情報のみ取得（MachineImage作成はスキップ）
        ami_info = ami_resolver.get_ami_info_only(config.ami)
        
        assert ami_info.ami_id == "ami-0123456789abcdef0"
        assert ami_info.os_type == OSType.UNKNOWN  # 直接AMI IDからは判定不可
    
    def test_instance_type_validator_with_configuration_manager(self):
        """InstanceTypeValidator と ConfigurationManager の統合テスト"""
        from ssm_ec2_rdp.instance_type_validator import InstanceTypeValidator
        
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        validator = InstanceTypeValidator()
        
        # インスタンスタイプの検証と情報取得
        is_valid = validator.validate_instance_type(config.instance.instance_type)
        assert is_valid is True
        
        info = validator.validate_and_get_info(config.instance.instance_type)
        assert info['instance_type'] == "t3.medium"
        assert info['family'] == "t3"
        assert info['size'] == "medium"
        assert info['category'] == "Burstable Performance"
        assert info['is_burstable'] is True
    
    def test_key_pair_manager_with_configuration_manager(self):
        """KeyPairManager と ConfigurationManager の統合テスト"""
        from ssm_ec2_rdp.key_pair_manager import KeyPairManager
        
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "t3.medium")
        app.node.set_context("key-pair-name", "test-key")
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # モックスタックを作成
        mock_stack = MagicMock()
        
        key_pair_manager = KeyPairManager(mock_stack)
        
        # Key Pair情報の取得
        info = key_pair_manager.get_key_pair_info(config.instance.key_pair_name)
        assert info['key_pair_name'] == "test-key"
        assert info['is_specified'] is True
        assert info['is_valid_format'] is True
        
        # セキュリティ推奨事項の取得
        recommendations = key_pair_manager.get_security_recommendations(config.instance.key_pair_name)
        assert len(recommendations) > 0
        assert any("SSM Session Manager" in rec for rec in recommendations)
    
    def test_user_data_manager_with_ami_info(self):
        """UserDataManager と AMI情報の統合テスト"""
        from ssm_ec2_rdp.user_data_manager import UserDataManager
        
        user_data_manager = UserDataManager()
        
        # Windows AMI での統合テスト
        windows_ami_info = AMIInfo(
            ami_id="ami-windows123",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        windows_user_data = user_data_manager.generate_user_data(windows_ami_info)
        assert windows_user_data is not None
        
        info = user_data_manager.get_user_data_info(windows_ami_info)
        assert info['os_type'] == 'Windows'
        assert 'リモートデスクトップ有効化' in info['features']
        
        # Linux AMI での統合テスト
        linux_ami_info = AMIInfo(
            ami_id="ami-linux456",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        linux_user_data = user_data_manager.generate_user_data(linux_ami_info)
        assert linux_user_data is not None
        
        info = user_data_manager.get_user_data_info(linux_ami_info)
        assert info['os_type'] == 'Linux'
        assert 'システムアップデート' in info['features']


class TestEndToEndWorkflow:
    """End-to-End ワークフローテスト"""
    
    @pytest.mark.parametrize("config_data,expected_os", [
        ({"ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base", "instance-type": "t3.medium"}, OSType.WINDOWS),
        ({"ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2", "instance-type": "m5.large"}, OSType.LINUX),
        ({"ami-id": "ami-0123456789abcdef0", "instance-type": "c5.xlarge"}, OSType.UNKNOWN),
    ])
    def test_complete_workflow_patterns(self, config_data, expected_os):
        """複数の設定パターンでの完全ワークフローテスト"""
        from ssm_ec2_rdp.ami_resolver import AMIResolver
        from ssm_ec2_rdp.instance_type_validator import InstanceTypeValidator
        from ssm_ec2_rdp.key_pair_manager import KeyPairManager
        from ssm_ec2_rdp.user_data_manager import UserDataManager
        
        # 1. 設定管理
        app = core.App()
        for key, value in config_data.items():
            app.node.set_context(key, value)
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # 2. コンポーネント初期化
        mock_stack = MagicMock()
        mock_stack.region = "us-west-2"
        
        ami_resolver = AMIResolver(mock_stack)
        instance_validator = InstanceTypeValidator()
        key_pair_manager = KeyPairManager(mock_stack)
        user_data_manager = UserDataManager()
        
        # 3. 検証
        instance_validator.validate_instance_type(config.instance.instance_type)
        
        # 4. AMI情報取得
        ami_info = ami_resolver.get_ami_info_only(config.ami)
        if expected_os != OSType.UNKNOWN:
            assert ami_info.os_type == expected_os
        
        # 5. ユーザーデータ生成
        user_data = user_data_manager.generate_user_data(ami_info)
        assert user_data is not None
        
        # 6. Key Pair情報
        key_pair_info = key_pair_manager.get_key_pair_info(config.instance.key_pair_name)
        assert isinstance(key_pair_info, dict)
        
        # 7. 統合結果の確認
        assert isinstance(config.ami, type(config.ami))
        assert isinstance(config.instance, type(config.instance))
    
    def test_error_propagation_workflow(self):
        """エラー伝播ワークフローテスト"""
        from ssm_ec2_rdp.instance_type_validator import InstanceTypeValidator
        
        # 無効な設定でのエラー伝播確認
        app = core.App()
        app.node.set_context("ami-id", "ami-0123456789abcdef0")
        app.node.set_context("instance-type", "invalid.type")
        
        config_manager = ConfigurationManager(app)
        
        # 設定レベルでエラーが検出されることを確認
        with pytest.raises(ConfigurationError):
            config_manager.get_configuration()
        
        # バリデータ単体でも同じエラーが検出されることを確認
        validator = InstanceTypeValidator()
        with pytest.raises(InvalidValueError):
            validator.validate_instance_type("invalid.type")


class TestPerformanceIntegration:
    """パフォーマンス統合テスト"""
    
    def test_configuration_loading_performance(self):
        """設定読み込みパフォーマンステスト"""
        import time
        
        start_time = time.time()
        
        # 複数の設定パターンを連続で処理
        test_configs = [
            {"ami-id": "ami-0123456789abcdef0", "instance-type": "t3.micro"},
            {"ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base", "instance-type": "m5.large"},
            {"ami-id": "ami-087654321fedcba98", "instance-type": "c5.xlarge"},
            {"ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2", "instance-type": "r5.2xlarge"},
        ]
        
        for config_data in test_configs:
            app = core.App()
            for key, value in config_data.items():
                app.node.set_context(key, value)
            
            config_manager = ConfigurationManager(app)
            config = config_manager.get_configuration()
            
            # 基本的な検証
            assert config.ami is not None
            assert config.instance is not None
        
        execution_time = time.time() - start_time
        
        # パフォーマンス要件: 設定読み込みは1秒以内
        assert execution_time < 1.0, f"設定読み込み時間が要件を超えています: {execution_time:.2f}秒"