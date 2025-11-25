"""
CDK設定用の型定義とデータクラス
AMI・インスタンス設定機能で使用する型定義とバリデーション機能を提供
"""

from typing import Optional, Union, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum
import re


class OSType(Enum):
    """OS種別の列挙型"""
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"


class ConfigurationError(Exception):
    """設定エラーの基底クラス"""
    pass


class MissingConfigError(ConfigurationError):
    """必須設定項目が不足している場合のエラー"""
    pass


class ConfigConflictError(ConfigurationError):
    """設定項目が競合している場合のエラー"""
    pass


class InvalidValueError(ConfigurationError):
    """設定値が不正な場合のエラー"""
    pass


class AMINotFoundError(Exception):
    """指定されたAMIが見つからない場合のエラー"""
    pass


class KeyPairNotFoundError(Exception):
    """指定されたKey Pairが見つからない場合のエラー"""
    pass


@dataclass
class AMIConfiguration:
    """AMI設定を表すデータクラス"""
    ami_id: Optional[str] = None
    ami_parameter: Optional[str] = None
    
    def __post_init__(self):
        """設定の妥当性を検証"""
        if self.ami_id and self.ami_parameter:
            raise ConfigConflictError(
                "ami-idとami-parameterの両方を指定することはできません。"
                "いずれか一つを選択してください。"
            )
        
        if not self.ami_id and not self.ami_parameter:
            raise MissingConfigError(
                "AMI設定が必要です。ami-idまたはami-parameterのいずれかを指定してください。"
            )
        
        if self.ami_id and not self._is_valid_ami_id(self.ami_id):
            raise InvalidValueError(
                f"無効なAMI ID形式です: {self.ami_id}. "
                "AMI IDは 'ami-' で始まる17文字の文字列である必要があります。"
            )
        
        if self.ami_parameter and not self._is_valid_ssm_parameter(self.ami_parameter):
            raise InvalidValueError(
                f"無効なSSMパラメータパス形式です: {self.ami_parameter}. "
                "パラメータパスは '/' で始まる必要があります。"
            )
    
    @staticmethod
    def _is_valid_ami_id(ami_id: str) -> bool:
        """
        AMI IDの形式をチェック
        
        AMI IDは 'ami-' プレフィックス + 17文字の16進数文字列
        例: ami-0123456789abcdef0
        """
        return bool(re.match(r'^ami-[0-9a-f]{17}$', ami_id))
    
    @staticmethod
    def _is_valid_ssm_parameter(parameter_path: str) -> bool:
        """
        SSMパラメータパスの形式をチェック
        
        パラメータパスは '/' で始まる1文字以上のパス
        例: /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
        """
        return parameter_path.startswith('/') and len(parameter_path) > 1


@dataclass
class InstanceConfiguration:
    """インスタンス設定を表すデータクラス"""
    instance_type: str
    key_pair_name: Optional[str] = None
    subnet_type: str = "private"  # デフォルトはプライベートサブネット

    def __post_init__(self):
        """設定の妥当性を検証"""
        if not self.instance_type:
            raise MissingConfigError("instance-typeは必須設定項目です。")

        if not self._is_valid_instance_type(self.instance_type):
            raise InvalidValueError(
                f"無効なインスタンスタイプ形式です: {self.instance_type}. "
                "例: t3.medium, m5.large, c5.xlarge"
            )

        if self.key_pair_name is not None and not self._is_valid_key_pair_name(self.key_pair_name):
            raise InvalidValueError(
                f"無効なKey Pair名形式です: {self.key_pair_name}. "
                "Key Pair名は英数字、ハイフン、アンダースコアのみ使用できます。"
            )

        if not self._is_valid_subnet_type(self.subnet_type):
            raise InvalidValueError(
                f"無効なサブネットタイプです: {self.subnet_type}. "
                "'private' または 'public' を指定してください。"
            )
    
    @staticmethod
    def _is_valid_instance_type(instance_type: str) -> bool:
        """
        インスタンスタイプの形式をチェック
        
        形式: {ファミリー}[世代][属性].{サイズ}
        例: t3.medium, m5.large, c5.xlarge, r5.2xlarge
        """
        pattern = r'^[a-z]+[0-9]*[a-z]*\.(nano|micro|small|medium|large|xlarge|[0-9]+xlarge)$'
        return bool(re.match(pattern, instance_type))
    
    @staticmethod
    def _is_valid_key_pair_name(key_pair_name: str) -> bool:
        """
        Key Pair名の形式をチェック

        英数字、ハイフン、アンダースコアのみ許可
        例: my-key-pair, test_key, MyKey123
        """
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', key_pair_name))

    @staticmethod
    def _is_valid_subnet_type(subnet_type: str) -> bool:
        """
        サブネットタイプの妥当性をチェック

        許可される値: 'private', 'public'
        """
        return subnet_type in ['private', 'public']


@dataclass
class EC2Configuration:
    """EC2設定の統合クラス"""
    ami: AMIConfiguration
    instance: InstanceConfiguration
    
    @classmethod
    def from_context(cls, context: Dict[str, Any]) -> 'EC2Configuration':
        """cdk.jsonのcontextから設定を作成"""
        ami_config = AMIConfiguration(
            ami_id=context.get('ami-id'),
            ami_parameter=context.get('ami-parameter')
        )

        instance_config = InstanceConfiguration(
            instance_type=context.get('instance-type'),
            key_pair_name=context.get('key-pair-name'),
            subnet_type=context.get('subnet-type', 'private')  # デフォルトはprivate
        )

        return cls(ami=ami_config, instance=instance_config)


@dataclass
class AMIInfo:
    """解決されたAMI情報を表すクラス"""
    ami_id: str
    os_type: OSType
    description: Optional[str] = None
    
    def is_windows(self) -> bool:
        """Windows AMIかどうかを判定"""
        return self.os_type == OSType.WINDOWS
    
    def is_linux(self) -> bool:
        """Linux AMIかどうかを判定"""
        return self.os_type == OSType.LINUX


@dataclass
class UserDataConfig:
    """ユーザーデータ設定を表すクラス"""
    os_type: OSType
    commands: list[str]
    
    @classmethod
    def for_windows(cls) -> 'UserDataConfig':
        """Windows用のユーザーデータ設定を作成"""
        commands = [
            "# リモートデスクトップを有効化",
            "Set-ItemProperty -Path \"HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\" -Name \"fDenyTSConnections\" -Value 0",
            "Enable-NetFirewallRule -DisplayGroup \"Remote Desktop\"",
            "# SSM Agentが正常に動作するためのレジストリ設定",
            "Set-ItemProperty -Path \"HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System\" -Name \"LocalAccountTokenFilterPolicy\" -Value 1",
            "# タイムゾーンを東京時間に変更",
            "tzutil /s \"Tokyo Standard Time\"",
            "# 新しいユーザーを作成（任意）",
            "net user rdpuser Password123! /add",
            "net localgroup administrators rdpuser /add",
            "net localgroup \"Remote Desktop Users\" rdpuser /add"
        ]
        return cls(os_type=OSType.WINDOWS, commands=commands)
    
    @classmethod
    def for_linux(cls) -> 'UserDataConfig':
        """Linux用のユーザーデータ設定を作成"""
        commands = [
            "#!/bin/bash",
            "# 基本的なパッケージ更新",
            "yum update -y",
            "# SSM Agentが動作していることを確認",
            "systemctl enable amazon-ssm-agent",
            "systemctl start amazon-ssm-agent"
        ]
        return cls(os_type=OSType.LINUX, commands=commands)


def validate_configuration(context: Dict[str, Any]) -> EC2Configuration:
    """
    設定の検証を行い、EC2Configuration オブジェクトを返す
    
    Args:
        context: cdk.jsonのcontextセクション
        
    Returns:
        EC2Configuration: 検証済みの設定オブジェクト
        
    Raises:
        ConfigurationError: 設定に問題がある場合
    """
    try:
        return EC2Configuration.from_context(context)
    except Exception as e:
        raise ConfigurationError(f"設定検証エラー: {str(e)}") from e


def get_configuration_help() -> str:
    """設定ヘルプメッセージを返す"""
    return """
cdk.json 設定ガイド:

必須設定:
- ami-id または ami-parameter のいずれか一つ
- instance-type

任意設定:
- key-pair-name

設定例:
1. 直接AMI ID指定:
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.large"
  }
}

2. SSMパラメータ指定:
{
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "m5.xlarge",
    "key-pair-name": "my-key-pair"
  }
}
"""