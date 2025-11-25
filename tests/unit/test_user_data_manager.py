"""
UserDataManagerのユニットテスト
"""
import pytest
from unittest.mock import Mock
from aws_cdk import aws_ec2 as ec2
from ssm_ec2_rdp.user_data_manager import UserDataManager
from ssm_ec2_rdp.types import AMIInfo, OSType


class TestUserDataManager:
    """UserDataManagerクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.manager = UserDataManager()
    
    def test_initialization(self):
        """初期化のテスト"""
        assert isinstance(self.manager, UserDataManager)
    
    def test_generate_user_data_windows(self):
        """Windows用ユーザーデータ生成のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        user_data = self.manager.generate_user_data(ami_info)
        
        assert isinstance(user_data, ec2.UserData)
        # UserDataの内容は内部実装のため詳細テストは困難だが、
        # 生成されることを確認
    
    def test_generate_user_data_linux(self):
        """Linux用ユーザーデータ生成のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        user_data = self.manager.generate_user_data(ami_info)
        
        assert isinstance(user_data, ec2.UserData)
    
    def test_generate_user_data_unknown_os(self):
        """Unknown OS用ユーザーデータ生成のテスト（Linuxとして処理）"""
        ami_info = AMIInfo(
            ami_id="ami-unknown",
            os_type=OSType.UNKNOWN,
            description="Unknown AMI"
        )
        
        user_data = self.manager.generate_user_data(ami_info)
        
        assert isinstance(user_data, ec2.UserData)
        # UNKNOWN の場合はLinuxとして処理される
    
    def test_generate_user_data_with_additional_config_windows(self):
        """Windows用の追加設定付きユーザーデータ生成のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        additional_config = {
            'enable_iis': True,
            'open_ports': [80, 443],
            'custom_commands': ['Write-Host "Custom setup"']
        }
        
        user_data = self.manager.generate_user_data(ami_info, additional_config)
        
        assert isinstance(user_data, ec2.UserData)
    
    def test_generate_user_data_with_additional_config_linux(self):
        """Linux用の追加設定付きユーザーデータ生成のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        additional_config = {
            'enable_docker': True,
            'install_packages': ['git', 'nodejs'],
            'custom_commands': ['echo "Custom setup"']
        }
        
        user_data = self.manager.generate_user_data(ami_info, additional_config)
        
        assert isinstance(user_data, ec2.UserData)
    
    def test_get_default_windows_config(self):
        """Windows用デフォルト設定取得のテスト"""
        config = self.manager.get_default_windows_config()
        
        assert isinstance(config, dict)
        assert config['enable_rdp'] is True
        assert config['enable_nla'] is True
        assert config['enable_windows_update'] is True
        assert config['enable_ssm'] is True
    
    def test_get_default_linux_config(self):
        """Linux用デフォルト設定取得のテスト"""
        config = self.manager.get_default_linux_config()
        
        assert isinstance(config, dict)
        assert config['update_system'] is True
        assert config['install_ssm'] is True
        assert config['disable_password_auth'] is True
        assert config['install_basic_tools'] is True
    
    def test_get_user_data_info_windows(self):
        """Windows用ユーザーデータ情報取得のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        info = self.manager.get_user_data_info(ami_info)
        
        assert info['os_type'] == 'Windows'
        assert 'リモートデスクトップ有効化' in info['features']
        assert 'Windows ファイアウォール設定' in info['features']
        assert 'SSM Agent 設定' in info['features']
        assert 3389 in info['default_ports']  # RDP port
        assert 'enable_iis' in info['recommended_additional_config']
    
    def test_get_user_data_info_linux(self):
        """Linux用ユーザーデータ情報取得のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        info = self.manager.get_user_data_info(ami_info)
        
        assert info['os_type'] == 'Linux'
        assert 'システムアップデート' in info['features']
        assert 'SSM Agent インストール・設定' in info['features']
        assert 'SSH セキュリティ強化' in info['features']
        assert 22 in info['default_ports']  # SSH port
        assert 'enable_docker' in info['recommended_additional_config']
    
    def test_get_user_data_info_unknown_os(self):
        """Unknown OS用ユーザーデータ情報取得のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-unknown",
            os_type=OSType.UNKNOWN,
            description="Unknown AMI"
        )
        
        info = self.manager.get_user_data_info(ami_info)
        
        # UNKNOWNの場合はLinuxとして処理される
        assert info['os_type'] == 'Linux'
    
    def test_validate_additional_config_valid_windows(self):
        """Windows用の有効な追加設定検証のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        valid_config = {
            'enable_iis': True,
            'open_ports': [80, 443, 8080],
            'custom_commands': ['Write-Host "Test"', 'Get-Date']
        }
        
        errors = self.manager.validate_additional_config(ami_info, valid_config)
        
        assert errors == []
    
    def test_validate_additional_config_valid_linux(self):
        """Linux用の有効な追加設定検証のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        valid_config = {
            'enable_docker': True,
            'install_packages': ['git', 'nodejs', 'python3'],
            'custom_commands': ['echo "Hello"', 'date']
        }
        
        errors = self.manager.validate_additional_config(ami_info, valid_config)
        
        assert errors == []
    
    def test_validate_additional_config_invalid_type(self):
        """無効な型の追加設定検証のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        invalid_config = "not a dict"
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 1
        assert "追加設定は辞書形式である必要があります" in errors[0]
    
    def test_validate_additional_config_os_mismatch_windows(self):
        """Windows環境でLinux専用設定を指定した場合のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        invalid_config = {
            'enable_docker': True  # Linux専用設定
        }
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 1
        assert "enable_docker" in errors[0]
        assert "Windows環境ではサポートされていません" in errors[0]
    
    def test_validate_additional_config_os_mismatch_linux(self):
        """Linux環境でWindows専用設定を指定した場合のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        invalid_config = {
            'enable_iis': True  # Windows専用設定
        }
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 1
        assert "enable_iis" in errors[0]
        assert "Linux環境ではサポートされていません" in errors[0]
    
    def test_validate_additional_config_invalid_custom_commands(self):
        """無効なcustom_commandsの検証テスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        invalid_config = {
            'custom_commands': 'not a list'  # リストではない
        }
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 1
        assert "custom_commands" in errors[0]
        assert "リスト形式である必要があります" in errors[0]
    
    def test_validate_additional_config_invalid_custom_command_items(self):
        """custom_commandsの項目が無効な場合のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        invalid_config = {
            'custom_commands': ['valid command', 123, None]  # 文字列以外を含む
        }
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 2  # 123とNoneの2つのエラー
        assert any("カスタムコマンド2" in error for error in errors)
        assert any("カスタムコマンド3" in error for error in errors)
    
    def test_validate_additional_config_invalid_ports(self):
        """無効なポート設定の検証テスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        invalid_config = {
            'open_ports': [80, 'invalid', 65536, -1]  # 無効なポート
        }
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 3  # 'invalid', 65536, -1の3つのエラー
        assert any("invalid" in error for error in errors)
        assert any("65536" in error for error in errors)
        assert any("-1" in error for error in errors)
    
    def test_validate_additional_config_invalid_packages(self):
        """無効なパッケージ設定の検証テスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        invalid_config = {
            'install_packages': ['git', 123, '', '   ']  # 無効なパッケージ名
        }
        
        errors = self.manager.validate_additional_config(ami_info, invalid_config)
        
        assert len(errors) == 3  # 123, '', '   'の3つのエラー
    
    def test_get_supported_configurations_windows(self):
        """Windows用サポート設定オプション取得のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-12345",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        config = self.manager.get_supported_configurations(ami_info)
        
        assert 'custom_commands' in config
        assert 'enable_iis' in config
        assert 'open_ports' in config
        assert 'enable_docker' not in config  # Linux専用なので含まれない
        
        # 設定の詳細チェック
        assert config['enable_iis']['type'] == 'bool'
        assert config['enable_iis']['default'] is False
    
    def test_get_supported_configurations_linux(self):
        """Linux用サポート設定オプション取得のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-67890",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        config = self.manager.get_supported_configurations(ami_info)
        
        assert 'custom_commands' in config
        assert 'enable_docker' in config
        assert 'install_packages' in config
        assert 'enable_iis' not in config  # Windows専用なので含まれない
        
        # 設定の詳細チェック
        assert config['enable_docker']['type'] == 'bool'
        assert config['enable_docker']['default'] is False


class TestUserDataManagerIntegration:
    """UserDataManagerの統合テスト"""
    
    def test_complete_windows_workflow(self):
        """Windows用の完全なワークフローテスト"""
        manager = UserDataManager()
        ami_info = AMIInfo(
            ami_id="ami-windows",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        # 1. デフォルト設定の取得
        default_config = manager.get_default_windows_config()
        assert isinstance(default_config, dict)
        
        # 2. ユーザーデータ情報の取得
        info = manager.get_user_data_info(ami_info)
        assert info['os_type'] == 'Windows'
        
        # 3. サポートされる設定の取得
        supported = manager.get_supported_configurations(ami_info)
        assert 'enable_iis' in supported
        
        # 4. 追加設定の検証
        additional_config = {
            'enable_iis': True,
            'open_ports': [80, 443],
            'custom_commands': ['Write-Host "Setup complete"']
        }
        errors = manager.validate_additional_config(ami_info, additional_config)
        assert errors == []
        
        # 5. ユーザーデータの生成
        user_data = manager.generate_user_data(ami_info, additional_config)
        assert isinstance(user_data, ec2.UserData)
    
    def test_complete_linux_workflow(self):
        """Linux用の完全なワークフローテスト"""
        manager = UserDataManager()
        ami_info = AMIInfo(
            ami_id="ami-linux",
            os_type=OSType.LINUX,
            description="Amazon Linux 2023"
        )
        
        # 1. デフォルト設定の取得
        default_config = manager.get_default_linux_config()
        assert isinstance(default_config, dict)
        
        # 2. ユーザーデータ情報の取得
        info = manager.get_user_data_info(ami_info)
        assert info['os_type'] == 'Linux'
        
        # 3. サポートされる設定の取得
        supported = manager.get_supported_configurations(ami_info)
        assert 'enable_docker' in supported
        
        # 4. 追加設定の検証
        additional_config = {
            'enable_docker': True,
            'install_packages': ['git', 'nodejs'],
            'custom_commands': ['echo "Setup complete"']
        }
        errors = manager.validate_additional_config(ami_info, additional_config)
        assert errors == []
        
        # 5. ユーザーデータの生成
        user_data = manager.generate_user_data(ami_info, additional_config)
        assert isinstance(user_data, ec2.UserData)
    
    def test_error_handling_workflow(self):
        """エラーハンドリングワークフローテスト"""
        manager = UserDataManager()
        ami_info = AMIInfo(
            ami_id="ami-windows",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        # 無効な設定での検証
        invalid_configs = [
            # 型エラー
            "not a dict",
            # OS不適合
            {'enable_docker': True},
            # 値エラー
            {'custom_commands': 'not a list'},
            {'open_ports': [999999]},
            # 複合エラー
            {
                'enable_docker': True,
                'custom_commands': ['valid'],
                'open_ports': [-1, 'invalid']
            }
        ]
        
        for invalid_config in invalid_configs:
            errors = manager.validate_additional_config(ami_info, invalid_config)
            assert len(errors) > 0, f"Should have errors for: {invalid_config}"
    
    def test_os_detection_consistency(self):
        """OS検出の整合性テスト"""
        manager = UserDataManager()
        
        # 各OSタイプでの処理一貫性
        os_types = [OSType.WINDOWS, OSType.LINUX, OSType.UNKNOWN]
        
        for os_type in os_types:
            ami_info = AMIInfo(
                ami_id=f"ami-{os_type.value}",
                os_type=os_type,
                description=f"Test {os_type.value} AMI"
            )
            
            # 各メソッドが正常に動作することを確認
            info = manager.get_user_data_info(ami_info)
            assert isinstance(info, dict)
            
            supported = manager.get_supported_configurations(ami_info)
            assert isinstance(supported, dict)
            
            user_data = manager.generate_user_data(ami_info)
            assert isinstance(user_data, ec2.UserData)
            
            # UNKNOWNはLinuxとして処理されることを確認
            if os_type == OSType.UNKNOWN:
                assert info['os_type'] == 'Linux'