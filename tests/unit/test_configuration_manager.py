"""
ConfigurationManagerのユニットテスト
"""
import pytest
from unittest.mock import Mock, MagicMock
from aws_cdk import App
from ssm_ec2_rdp.configuration_manager import ConfigurationManager
from ssm_ec2_rdp.types import (
    EC2Configuration,
    ConfigurationError,
    MissingConfigError,
    ConfigConflictError
)


class TestConfigurationManager:
    """ConfigurationManagerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.app = Mock(spec=App)
        self.app.node = Mock()
        self.manager = ConfigurationManager(self.app)
    
    def test_initialization(self):
        """初期化のテスト"""
        assert self.manager.app is self.app
    
    def test_extract_context_values(self):
        """context値抽出のテスト"""
        # モックの設定
        self.app.node.try_get_context.side_effect = lambda key: {
            'ami-id': 'ami-0123456789abcdef0',
            'ami-parameter': None,
            'instance-type': 't3.medium',
            'key-pair-name': 'test-key'
        }.get(key)
        
        # テスト実行
        context = self.manager._extract_context_values()
        
        # 検証
        expected = {
            'ami-id': 'ami-0123456789abcdef0',
            'ami-parameter': None,
            'instance-type': 't3.medium',
            'key-pair-name': 'test-key'
        }
        assert context == expected
        
        # try_get_contextが正しい回数呼ばれることを確認
        assert self.app.node.try_get_context.call_count == 4
    
    def test_get_configuration_success_ami_id(self):
        """AMI ID指定での設定取得成功テスト"""
        # モックの設定
        self.app.node.try_get_context.side_effect = lambda key: {
            'ami-id': 'ami-0123456789abcdef0',
            'ami-parameter': None,
            'instance-type': 't3.medium',
            'key-pair-name': None
        }.get(key)
        
        # テスト実行
        config = self.manager.get_configuration()
        
        # 検証
        assert isinstance(config, EC2Configuration)
        assert config.ami.ami_id == 'ami-0123456789abcdef0'
        assert config.ami.ami_parameter is None
        assert config.instance.instance_type == 't3.medium'
        assert config.instance.key_pair_name is None
    
    def test_get_configuration_success_ami_parameter(self):
        """SSMパラメータ指定での設定取得成功テスト"""
        # モックの設定
        self.app.node.try_get_context.side_effect = lambda key: {
            'ami-id': None,
            'ami-parameter': '/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2',
            'instance-type': 'm5.large',
            'key-pair-name': 'my-key'
        }.get(key)
        
        # テスト実行
        config = self.manager.get_configuration()
        
        # 検証
        assert isinstance(config, EC2Configuration)
        assert config.ami.ami_id is None
        assert config.ami.ami_parameter == '/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2'
        assert config.instance.instance_type == 'm5.large'
        assert config.instance.key_pair_name == 'my-key'
    
    def test_get_configuration_missing_ami_settings(self):
        """AMI設定不足での設定取得失敗テスト"""
        # モックの設定（AMI設定なし）
        self.app.node.try_get_context.side_effect = lambda key: {
            'ami-id': None,
            'ami-parameter': None,
            'instance-type': 't3.medium',
            'key-pair-name': None
        }.get(key)
        
        # テスト実行と検証
        with pytest.raises(ConfigurationError) as exc_info:
            self.manager.get_configuration()
        
        assert "設定検証エラー" in str(exc_info.value)
    
    def test_get_configuration_missing_instance_type(self):
        """インスタンスタイプ不足での設定取得失敗テスト"""
        # モックの設定（インスタンスタイプなし）
        self.app.node.try_get_context.side_effect = lambda key: {
            'ami-id': 'ami-0123456789abcdef0',
            'ami-parameter': None,
            'instance-type': None,
            'key-pair-name': None
        }.get(key)
        
        # テスト実行と検証
        with pytest.raises(ConfigurationError) as exc_info:
            self.manager.get_configuration()
        
        assert "設定検証エラー" in str(exc_info.value)
    
    def test_get_configuration_conflict_ami_settings(self):
        """AMI設定競合での設定取得失敗テスト"""
        # モックの設定（AMI設定の両方指定）
        self.app.node.try_get_context.side_effect = lambda key: {
            'ami-id': 'ami-0123456789abcdef0',
            'ami-parameter': '/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2',
            'instance-type': 't3.medium',
            'key-pair-name': None
        }.get(key)
        
        # テスト実行と検証
        with pytest.raises(ConfigurationError) as exc_info:
            self.manager.get_configuration()
        
        assert "設定検証エラー" in str(exc_info.value)
    
    def test_get_context_value(self):
        """個別context値取得のテスト"""
        # モックの設定
        self.app.node.try_get_context.return_value = 't3.medium'
        
        # テスト実行
        value = self.manager.get_context_value('instance-type')
        
        # 検証
        assert value == 't3.medium'
        self.app.node.try_get_context.assert_called_once_with('instance-type')
    
    def test_get_context_value_none(self):
        """存在しないcontext値取得のテスト"""
        # モックの設定
        self.app.node.try_get_context.return_value = None
        
        # テスト実行
        value = self.manager.get_context_value('non-existent-key')
        
        # 検証
        assert value is None
        self.app.node.try_get_context.assert_called_once_with('non-existent-key')
    
    def test_has_context_value_true(self):
        """context値存在確認（存在する場合）のテスト"""
        # モックの設定
        self.app.node.try_get_context.return_value = 't3.medium'
        
        # テスト実行
        exists = self.manager.has_context_value('instance-type')
        
        # 検証
        assert exists is True
    
    def test_has_context_value_false_none(self):
        """context値存在確認（Noneの場合）のテスト"""
        # モックの設定
        self.app.node.try_get_context.return_value = None
        
        # テスト実行
        exists = self.manager.has_context_value('instance-type')
        
        # 検証
        assert exists is False
    
    def test_has_context_value_false_empty(self):
        """context値存在確認（空文字の場合）のテスト"""
        # モックの設定
        self.app.node.try_get_context.return_value = ""
        
        # テスト実行
        exists = self.manager.has_context_value('instance-type')
        
        # 検証
        assert exists is False
    
    def test_validate_context_completeness_complete(self):
        """完全な設定での完全性チェックテスト"""
        # モックの設定（完全な設定）
        def mock_has_context_value(key):
            return key in ['instance-type', 'ami-id']
        
        self.manager.has_context_value = Mock(side_effect=mock_has_context_value)
        
        # テスト実行
        is_complete, missing_keys = self.manager.validate_context_completeness()
        
        # 検証
        assert is_complete is True
        assert missing_keys == []
    
    def test_validate_context_completeness_missing_instance_type(self):
        """インスタンスタイプ不足での完全性チェックテスト"""
        # モックの設定（インスタンスタイプなし）
        def mock_has_context_value(key):
            return key == 'ami-id'
        
        self.manager.has_context_value = Mock(side_effect=mock_has_context_value)
        
        # テスト実行
        is_complete, missing_keys = self.manager.validate_context_completeness()
        
        # 検証
        assert is_complete is False
        assert 'instance-type' in missing_keys
    
    def test_validate_context_completeness_missing_ami_settings(self):
        """AMI設定不足での完全性チェックテスト"""
        # モックの設定（AMI設定なし）
        def mock_has_context_value(key):
            return key == 'instance-type'
        
        self.manager.has_context_value = Mock(side_effect=mock_has_context_value)
        
        # テスト実行
        is_complete, missing_keys = self.manager.validate_context_completeness()
        
        # 検証
        assert is_complete is False
        assert 'ami-id または ami-parameter' in missing_keys
    
    def test_validate_context_completeness_missing_all(self):
        """全設定不足での完全性チェックテスト"""
        # モックの設定（全設定なし）
        self.manager.has_context_value = Mock(return_value=False)
        
        # テスト実行
        is_complete, missing_keys = self.manager.validate_context_completeness()
        
        # 検証
        assert is_complete is False
        assert 'instance-type' in missing_keys
        assert 'ami-id または ami-parameter' in missing_keys
        assert len(missing_keys) == 2
    
    def test_print_help(self, capsys):
        """ヘルプ表示のテスト"""
        # テスト実行
        self.manager.print_help()
        
        # 出力を取得
        captured = capsys.readouterr()
        
        # 検証
        assert "cdk.json 設定ガイド" in captured.out
        assert "ami-id" in captured.out
        assert "ami-parameter" in captured.out
        assert "instance-type" in captured.out


class TestConfigurationManagerIntegration:
    """ConfigurationManagerの統合テスト"""
    
    def test_real_cdk_app_integration(self):
        """実際のCDK Appとの統合テスト（モック使用）"""
        # CDK Appのモックを作成
        app = Mock(spec=App)
        app.node = Mock()
        
        # context値を設定
        context_values = {
            'ami-parameter': '/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base',
            'instance-type': 't3.medium',
            'key-pair-name': 'windows-key'
        }
        
        def mock_try_get_context(key):
            return context_values.get(key)
        
        app.node.try_get_context = Mock(side_effect=mock_try_get_context)
        
        # ConfigurationManagerを初期化
        manager = ConfigurationManager(app)
        
        # 設定を取得
        config = manager.get_configuration()
        
        # 検証
        assert isinstance(config, EC2Configuration)
        assert config.ami.ami_parameter == '/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base'
        assert config.instance.instance_type == 't3.medium'
        assert config.instance.key_pair_name == 'windows-key'
        
        # context値の取得回数を確認
        assert app.node.try_get_context.call_count == 4