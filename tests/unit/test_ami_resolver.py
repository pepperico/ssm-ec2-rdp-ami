"""
AMIResolverのユニットテスト
"""
import pytest
from unittest.mock import Mock, patch
from aws_cdk import Stack, App, aws_ec2 as ec2
from ssm_ec2_rdp.ami_resolver import AMIResolver
from ssm_ec2_rdp.types import (
    AMIConfiguration,
    AMIInfo,
    OSType,
    AMINotFoundError
)


class TestAMIResolver:
    """AMIResolverクラスのテスト"""
    
    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        self.app = App()
        self.stack = Stack(self.app, "TestStack")
        self.resolver = AMIResolver(self.stack)
    
    def test_initialization(self):
        """初期化のテスト"""
        assert self.resolver.stack is self.stack
    
    def test_resolve_ami_by_ami_id(self):
        """AMI ID指定での解決テスト"""
        ami_config = AMIConfiguration(ami_id="ami-0123456789abcdef0")
        
        machine_image, ami_info = self.resolver.resolve_ami(ami_config)
        
        # MachineImageが作成されることを確認
        assert isinstance(machine_image, ec2.IMachineImage)
        
        # AMIInfoが正しく作成されることを確認
        assert isinstance(ami_info, AMIInfo)
        assert ami_info.ami_id == "ami-0123456789abcdef0"
        assert ami_info.os_type == OSType.UNKNOWN  # AMI IDからは判定不可
        assert "Custom AMI" in ami_info.description
    
    def test_resolve_ami_by_ssm_parameter_windows(self):
        """SSMパラメータ（Windows）での解決テスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        )
        
        machine_image, ami_info = self.resolver.resolve_ami(ami_config)
        
        # MachineImageが作成されることを確認
        assert isinstance(machine_image, ec2.IMachineImage)
        
        # AMIInfoが正しく作成されることを確認
        assert isinstance(ami_info, AMIInfo)
        assert ami_info.ami_id == "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        assert ami_info.os_type == OSType.WINDOWS
        assert "SSM Parameter" in ami_info.description
    
    def test_resolve_ami_by_ssm_parameter_linux(self):
        """SSMパラメータ（Linux）での解決テスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
        )
        
        machine_image, ami_info = self.resolver.resolve_ami(ami_config)
        
        # MachineImageが作成されることを確認
        assert isinstance(machine_image, ec2.IMachineImage)
        
        # AMIInfoが正しく作成されることを確認
        assert isinstance(ami_info, AMIInfo)
        assert ami_info.os_type == OSType.LINUX
        assert "SSM Parameter" in ami_info.description
    
    def test_detect_os_from_parameter_windows(self):
        """WindowsパラメータのOS検出テスト"""
        test_cases = [
            "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
            "/aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base",
            "/custom/windows-server-2016",
            "/test/WIN-SERVER"
        ]
        
        for parameter in test_cases:
            os_type = self.resolver._detect_os_from_parameter(parameter)
            assert os_type == OSType.WINDOWS, f"Failed for: {parameter}"
    
    def test_detect_os_from_parameter_linux(self):
        """LinuxパラメータのOS検出テスト"""
        test_cases = [
            "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
            "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
            "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
            "/custom/centos-7",
            "/test/debian-11"
        ]
        
        for parameter in test_cases:
            os_type = self.resolver._detect_os_from_parameter(parameter)
            assert os_type == OSType.LINUX, f"Failed for: {parameter}"
    
    def test_detect_os_from_parameter_unknown(self):
        """不明パラメータのOS検出テスト"""
        test_cases = [
            "/custom/unknown-os",
            "/test/mystery-ami",
            "/random/parameter/path"
        ]
        
        for parameter in test_cases:
            os_type = self.resolver._detect_os_from_parameter(parameter)
            assert os_type == OSType.UNKNOWN, f"Failed for: {parameter}"
    
    def test_detect_os_from_ami_id(self):
        """AMI IDからのOS検出テスト（常にUNKNOWNを返す）"""
        ami_id = "ami-0123456789abcdef0"
        os_type = self.resolver._detect_os_from_ami_id(ami_id)
        assert os_type == OSType.UNKNOWN
    
    def test_get_ami_info_only_ami_id(self):
        """AMI ID指定でのAMI情報のみ取得テスト"""
        ami_config = AMIConfiguration(ami_id="ami-0123456789abcdef0")
        
        ami_info = self.resolver.get_ami_info_only(ami_config)
        
        assert isinstance(ami_info, AMIInfo)
        assert ami_info.ami_id == "ami-0123456789abcdef0"
        assert ami_info.os_type == OSType.UNKNOWN
        assert "Custom AMI" in ami_info.description
    
    def test_get_ami_info_only_ssm_parameter(self):
        """SSMパラメータ指定でのAMI情報のみ取得テスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        )
        
        ami_info = self.resolver.get_ami_info_only(ami_config)
        
        assert isinstance(ami_info, AMIInfo)
        assert ami_info.ami_id == "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        assert ami_info.os_type == OSType.WINDOWS
        assert "SSM Parameter" in ami_info.description
    
    def test_get_ami_info_only_no_config(self):
        """設定なしでのAMI情報取得エラーテスト"""
        # 通常はAMIConfigurationのバリデーションで防がれるが、念のためテスト
        ami_config = AMIConfiguration.__new__(AMIConfiguration)
        ami_config.ami_id = None
        ami_config.ami_parameter = None
        
        with pytest.raises(AMINotFoundError) as exc_info:
            self.resolver.get_ami_info_only(ami_config)
        
        assert "AMI設定が指定されていません" in str(exc_info.value)
    
    def test_is_windows_ami_true(self):
        """Windows AMI判定（True）のテスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        )
        
        result = self.resolver.is_windows_ami(ami_config)
        assert result is True
    
    def test_is_windows_ami_false(self):
        """Windows AMI判定（False）のテスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
        )
        
        result = self.resolver.is_windows_ami(ami_config)
        assert result is False
    
    def test_is_linux_ami_true(self):
        """Linux AMI判定（True）のテスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
        )
        
        result = self.resolver.is_linux_ami(ami_config)
        assert result is True
    
    def test_is_linux_ami_false(self):
        """Linux AMI判定（False）のテスト"""
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        )
        
        result = self.resolver.is_linux_ami(ami_config)
        assert result is False
    
    def test_is_windows_ami_error_handling(self):
        """AMI判定でのエラーハンドリングテスト"""
        ami_config = AMIConfiguration.__new__(AMIConfiguration)
        ami_config.ami_id = None
        ami_config.ami_parameter = None
        
        # エラーが発生した場合はFalseを返す
        result = self.resolver.is_windows_ami(ami_config)
        assert result is False
        
        result = self.resolver.is_linux_ami(ami_config)
        assert result is False
    
    @patch('ssm_ec2_rdp.ami_resolver.AMIResolver._resolve_by_ami_id')
    def test_resolve_ami_exception_handling(self, mock_resolve):
        """AMI解決時の例外ハンドリングテスト"""
        # _resolve_by_ami_idで例外を発生させる
        mock_resolve.side_effect = Exception("Test exception")
        
        ami_config = AMIConfiguration(ami_id="ami-0123456789abcdef0")
        
        with pytest.raises(AMINotFoundError) as exc_info:
            self.resolver.resolve_ami(ami_config)
        
        assert "AMI解決中にエラーが発生しました" in str(exc_info.value)
    
    def test_resolve_ami_ami_not_found_error_passthrough(self):
        """AMINotFoundErrorの透過テスト"""
        # 実際にはAMI設定の不備でこのケースは発生しにくいが、テスト用
        ami_config = AMIConfiguration.__new__(AMIConfiguration)
        ami_config.ami_id = None
        ami_config.ami_parameter = None
        
        with pytest.raises(AMINotFoundError) as exc_info:
            self.resolver.resolve_ami(ami_config)
        
        assert "AMI設定が指定されていません" in str(exc_info.value)


class TestAMIResolverIntegration:
    """AMIResolverの統合テスト"""
    
    def test_windows_ami_workflow(self):
        """Windows AMI処理の統合ワークフローテスト"""
        app = App()
        stack = Stack(app, "TestStack", env={'region': 'us-east-1'})
        resolver = AMIResolver(stack)
        
        # Windows AMI設定
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
        )
        
        # AMI解決
        machine_image, ami_info = resolver.resolve_ami(ami_config)
        
        # 結果検証
        assert isinstance(machine_image, ec2.IMachineImage)
        assert ami_info.is_windows()
        assert not ami_info.is_linux()
        assert resolver.is_windows_ami(ami_config)
        assert not resolver.is_linux_ami(ami_config)
    
    def test_linux_ami_workflow(self):
        """Linux AMI処理の統合ワークフローテスト"""
        app = App()
        stack = Stack(app, "TestStack", env={'region': 'us-east-1'})
        resolver = AMIResolver(stack)
        
        # Linux AMI設定
        ami_config = AMIConfiguration(
            ami_parameter="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
        )
        
        # AMI解決
        machine_image, ami_info = resolver.resolve_ami(ami_config)
        
        # 結果検証
        assert isinstance(machine_image, ec2.IMachineImage)
        assert ami_info.is_linux()
        assert not ami_info.is_windows()
        assert resolver.is_linux_ami(ami_config)
        assert not resolver.is_windows_ami(ami_config)
    
    def test_custom_ami_workflow(self):
        """カスタムAMI処理の統合ワークフローテスト"""
        app = App()
        stack = Stack(app, "TestStack", env={'region': 'us-east-1'})
        resolver = AMIResolver(stack)
        
        # カスタムAMI設定
        ami_config = AMIConfiguration(ami_id="ami-0123456789abcdef0")
        
        # AMI解決
        machine_image, ami_info = resolver.resolve_ami(ami_config)
        
        # 結果検証
        assert isinstance(machine_image, ec2.IMachineImage)
        assert ami_info.os_type == OSType.UNKNOWN  # カスタムAMIはOS判定不可
        assert "Custom AMI" in ami_info.description
        
        # カスタムAMIの場合、OS判定は不確定
        assert not resolver.is_windows_ami(ami_config)  # UNKNOWNなのでFalse
        assert not resolver.is_linux_ami(ami_config)    # UNKNOWNなのでFalse