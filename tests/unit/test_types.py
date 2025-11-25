"""
型定義とデータクラスのユニットテスト
"""
import pytest
from ssm_ec2_rdp.types import (
    OSType,
    ConfigurationError,
    MissingConfigError,
    ConfigConflictError,
    InvalidValueError,
    AMINotFoundError,
    KeyPairNotFoundError,
    AMIConfiguration,
    InstanceConfiguration,
    EC2Configuration,
    AMIInfo,
    UserDataConfig,
    validate_configuration,
    get_configuration_help
)


class TestOSType:
    """OSType列挙型のテスト"""
    
    def test_os_type_values(self):
        """OSType列挙型の値をテスト"""
        assert OSType.WINDOWS.value == "windows"
        assert OSType.LINUX.value == "linux"
        assert OSType.UNKNOWN.value == "unknown"


class TestCustomExceptions:
    """カスタム例外クラスのテスト"""
    
    def test_exception_inheritance(self):
        """例外クラスの継承関係をテスト"""
        assert issubclass(ConfigurationError, Exception)
        assert issubclass(MissingConfigError, ConfigurationError)
        assert issubclass(ConfigConflictError, ConfigurationError)
        assert issubclass(InvalidValueError, ConfigurationError)
        assert issubclass(AMINotFoundError, Exception)
        assert issubclass(KeyPairNotFoundError, Exception)
    
    def test_exception_messages(self):
        """例外メッセージのテスト"""
        error = ConfigurationError("テストエラー")
        assert str(error) == "テストエラー"


class TestAMIConfiguration:
    """AMIConfigurationデータクラスのテスト"""
    
    def test_valid_ami_id(self):
        """有効なAMI IDでの正常作成テスト"""
        config = AMIConfiguration(ami_id="ami-0123456789abcdef0")
        assert config.ami_id == "ami-0123456789abcdef0"
        assert config.ami_parameter is None
    
    def test_valid_ami_parameter(self):
        """有効なSSMパラメータでの正常作成テスト"""
        config = AMIConfiguration(ami_parameter="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2")
        assert config.ami_parameter == "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
        assert config.ami_id is None
    
    def test_both_ami_settings_raise_conflict_error(self):
        """AMI設定の両方指定でConfigConflictErrorが発生することをテスト"""
        with pytest.raises(ConfigConflictError) as exc_info:
            AMIConfiguration(
                ami_id="ami-0123456789abcdef0",
                ami_parameter="/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
            )
        assert "両方を指定することはできません" in str(exc_info.value)
    
    def test_missing_ami_settings_raise_missing_error(self):
        """AMI設定の両方未指定でMissingConfigErrorが発生することをテスト"""
        with pytest.raises(MissingConfigError) as exc_info:
            AMIConfiguration()
        assert "AMI設定が必要です" in str(exc_info.value)
    
    def test_invalid_ami_id_format_raise_invalid_error(self):
        """無効なAMI ID形式でInvalidValueErrorが発生することをテスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            AMIConfiguration(ami_id="invalid-ami-id")
        assert "無効なAMI ID形式" in str(exc_info.value)
    
    def test_invalid_ami_parameter_format_raise_invalid_error(self):
        """無効なSSMパラメータ形式でInvalidValueErrorが発生することをテスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            AMIConfiguration(ami_parameter="invalid-parameter")
        assert "無効なSSMパラメータパス形式" in str(exc_info.value)
    
    def test_ami_id_validation_edge_cases(self):
        """AMI ID形式の境界値テスト"""
        # 正しい形式
        AMIConfiguration(ami_id="ami-0123456789abcdef0")  # 正確に17文字
        
        # 間違った形式
        with pytest.raises(InvalidValueError):
            AMIConfiguration(ami_id="ami-0123456789abcdef")  # 16文字
        
        with pytest.raises(InvalidValueError):
            AMIConfiguration(ami_id="ami-0123456789abcdef00")  # 18文字
        
        with pytest.raises(InvalidValueError):
            AMIConfiguration(ami_id="img-0123456789abcdef0")  # 間違ったプレフィックス
    
    def test_ssm_parameter_validation_edge_cases(self):
        """SSMパラメータ形式の境界値テスト"""
        # 正しい形式
        AMIConfiguration(ami_parameter="/valid/parameter/path")
        
        # 間違った形式
        with pytest.raises(InvalidValueError):
            AMIConfiguration(ami_parameter="invalid-parameter-path")  # '/'で始まらない
        
        with pytest.raises(InvalidValueError):
            AMIConfiguration(ami_parameter="/")  # 1文字のみ


class TestInstanceConfiguration:
    """InstanceConfigurationデータクラスのテスト"""
    
    def test_valid_instance_type(self):
        """有効なインスタンスタイプでの正常作成テスト"""
        config = InstanceConfiguration(instance_type="t3.medium")
        assert config.instance_type == "t3.medium"
        assert config.key_pair_name is None
    
    def test_valid_instance_type_with_key_pair(self):
        """Key Pair指定での正常作成テスト"""
        config = InstanceConfiguration(
            instance_type="m5.large",
            key_pair_name="my-key-pair"
        )
        assert config.instance_type == "m5.large"
        assert config.key_pair_name == "my-key-pair"
    
    def test_missing_instance_type_raise_error(self):
        """インスタンスタイプ未指定でMissingConfigErrorが発生することをテスト"""
        with pytest.raises(MissingConfigError) as exc_info:
            InstanceConfiguration(instance_type="")
        assert "instance-typeは必須設定項目" in str(exc_info.value)
    
    def test_invalid_instance_type_format_raise_error(self):
        """無効なインスタンスタイプ形式でInvalidValueErrorが発生することをテスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            InstanceConfiguration(instance_type="invalid-instance")
        assert "無効なインスタンスタイプ形式" in str(exc_info.value)
    
    def test_invalid_key_pair_name_raise_error(self):
        """無効なKey Pair名でInvalidValueErrorが発生することをテスト"""
        with pytest.raises(InvalidValueError) as exc_info:
            InstanceConfiguration(
                instance_type="t3.medium",
                key_pair_name="invalid@keypair"
            )
        assert "無効なKey Pair名形式" in str(exc_info.value)
    
    def test_instance_type_validation_edge_cases(self):
        """インスタンスタイプ形式の境界値テスト"""
        # 正しい形式
        valid_types = [
            "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge", "t3.2xlarge",
            "m5.large", "c5.xlarge", "r5.2xlarge", "i3.4xlarge", "d2.8xlarge"
        ]
        for instance_type in valid_types:
            config = InstanceConfiguration(instance_type=instance_type)
            assert config.instance_type == instance_type
        
        # 間違った形式
        invalid_types = [
            "invalid", "t3", "t3.", ".medium", "t3-medium", "T3.medium"
        ]
        for instance_type in invalid_types:
            with pytest.raises(InvalidValueError):
                InstanceConfiguration(instance_type=instance_type)
    
    def test_key_pair_name_validation_edge_cases(self):
        """Key Pair名形式の境界値テスト"""
        # 正しい形式
        valid_names = ["my-key", "my_key", "mykey123", "KEY-123", "test_key_1"]
        for key_pair_name in valid_names:
            config = InstanceConfiguration(
                instance_type="t3.medium",
                key_pair_name=key_pair_name
            )
            assert config.key_pair_name == key_pair_name
        
        # 間違った形式
        invalid_names = ["my@key", "my key", "my.key", "my#key", ""]
        for key_pair_name in invalid_names:
            with pytest.raises(InvalidValueError):
                InstanceConfiguration(
                    instance_type="t3.medium",
                    key_pair_name=key_pair_name
                )


class TestEC2Configuration:
    """EC2Configurationデータクラスのテスト"""
    
    def test_from_context_ami_id(self):
        """AMI ID指定でのfrom_contextテスト"""
        context = {
            "ami-id": "ami-0123456789abcdef0",
            "instance-type": "t3.medium"
        }
        config = EC2Configuration.from_context(context)
        
        assert config.ami.ami_id == "ami-0123456789abcdef0"
        assert config.ami.ami_parameter is None
        assert config.instance.instance_type == "t3.medium"
        assert config.instance.key_pair_name is None
    
    def test_from_context_ami_parameter(self):
        """SSMパラメータ指定でのfrom_contextテスト"""
        context = {
            "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
            "instance-type": "m5.large",
            "key-pair-name": "test-key"
        }
        config = EC2Configuration.from_context(context)
        
        assert config.ami.ami_parameter == "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
        assert config.ami.ami_id is None
        assert config.instance.instance_type == "m5.large"
        assert config.instance.key_pair_name == "test-key"
    
    def test_from_context_invalid_settings(self):
        """無効な設定でのfrom_contextテスト"""
        context = {
            "ami-id": "ami-0123456789abcdef0",
            "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
            "instance-type": "t3.medium"
        }
        with pytest.raises(ConfigConflictError):
            EC2Configuration.from_context(context)


class TestAMIInfo:
    """AMIInfoデータクラスのテスト"""
    
    def test_windows_ami_info(self):
        """Windows AMI情報のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-0123456789abcdef0",
            os_type=OSType.WINDOWS,
            description="Windows Server 2022"
        )
        
        assert ami_info.ami_id == "ami-0123456789abcdef0"
        assert ami_info.os_type == OSType.WINDOWS
        assert ami_info.description == "Windows Server 2022"
        assert ami_info.is_windows() is True
        assert ami_info.is_linux() is False
    
    def test_linux_ami_info(self):
        """Linux AMI情報のテスト"""
        ami_info = AMIInfo(
            ami_id="ami-0123456789abcdef1",
            os_type=OSType.LINUX
        )
        
        assert ami_info.ami_id == "ami-0123456789abcdef1"
        assert ami_info.os_type == OSType.LINUX
        assert ami_info.description is None
        assert ami_info.is_windows() is False
        assert ami_info.is_linux() is True


class TestUserDataConfig:
    """UserDataConfigデータクラスのテスト"""
    
    def test_for_windows(self):
        """Windows用UserDataConfig作成テスト"""
        config = UserDataConfig.for_windows()
        
        assert config.os_type == OSType.WINDOWS
        assert len(config.commands) > 0
        assert any("リモートデスクトップ" in cmd for cmd in config.commands)
        assert any("タイムゾーン" in cmd for cmd in config.commands)
    
    def test_for_linux(self):
        """Linux用UserDataConfig作成テスト"""
        config = UserDataConfig.for_linux()
        
        assert config.os_type == OSType.LINUX
        assert len(config.commands) > 0
        assert any("#!/bin/bash" in cmd for cmd in config.commands)
        assert any("amazon-ssm-agent" in cmd for cmd in config.commands)


class TestUtilityFunctions:
    """ユーティリティ関数のテスト"""
    
    def test_validate_configuration_success(self):
        """正常なvalidate_configurationテスト"""
        context = {
            "ami-id": "ami-0123456789abcdef0",
            "instance-type": "t3.medium"
        }
        config = validate_configuration(context)
        
        assert isinstance(config, EC2Configuration)
        assert config.ami.ami_id == "ami-0123456789abcdef0"
        assert config.instance.instance_type == "t3.medium"
    
    def test_validate_configuration_error(self):
        """エラー時のvalidate_configurationテスト"""
        context = {
            "instance-type": "t3.medium"  # AMI設定不足
        }
        with pytest.raises(ConfigurationError) as exc_info:
            validate_configuration(context)
        assert "設定検証エラー" in str(exc_info.value)
    
    def test_get_configuration_help(self):
        """get_configuration_helpテスト"""
        help_text = get_configuration_help()
        
        assert isinstance(help_text, str)
        assert "cdk.json 設定ガイド" in help_text
        assert "ami-id" in help_text
        assert "ami-parameter" in help_text
        assert "instance-type" in help_text