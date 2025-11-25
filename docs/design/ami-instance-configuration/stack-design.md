# スタック構成設計

## 概要

AMI・インスタンス設定機能のためのCDKスタック構成設計。既存の`SsmEc2RdpStack`を拡張し、新しい設定方式に対応する。

## スタック構造

### メインスタック: SsmEc2RdpStack

```python
class SsmEc2RdpStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        config: EC2Configuration,  # 新しい設定オブジェクト
        **kwargs
    ) -> None:
```

## コンポーネント設計

### 1. ConfigurationManager (新規)

```python
class ConfigurationManager:
    """設定の読み取り、検証、統合を担当"""
    
    def __init__(self, app: App):
        self.app = app
    
    def get_configuration(self) -> EC2Configuration:
        """cdk.jsonから設定を読み取り、検証済みオブジェクトを返す"""
        context = {
            'ami-id': self.app.node.try_get_context('ami-id'),
            'ami-parameter': self.app.node.try_get_context('ami-parameter'),
            'instance-type': self.app.node.try_get_context('instance-type'),
            'key-pair-name': self.app.node.try_get_context('key-pair-name')
        }
        return validate_configuration(context)
```

### 2. AMIResolver (新規)

```python
class AMIResolver:
    """AMI設定からMachineImageオブジェクトを生成"""
    
    def __init__(self, stack: Stack):
        self.stack = stack
    
    def resolve_ami(self, ami_config: AMIConfiguration) -> Tuple[ec2.MachineImage, AMIInfo]:
        """AMI設定を解決してMachineImageとAMI情報を返す"""
        if ami_config.ami_id:
            return self._resolve_by_ami_id(ami_config.ami_id)
        elif ami_config.ami_parameter:
            return self._resolve_by_parameter(ami_config.ami_parameter)
    
    def _resolve_by_ami_id(self, ami_id: str) -> Tuple[ec2.MachineImage, AMIInfo]:
        """直接AMI IDからMachineImageを作成"""
        machine_image = ec2.MachineImage.generic_linux({
            self.stack.region: ami_id
        })
        ami_info = self._get_ami_info(ami_id)
        return machine_image, ami_info
    
    def _resolve_by_parameter(self, parameter_path: str) -> Tuple[ec2.MachineImage, AMIInfo]:
        """SSMパラメータからMachineImageを作成"""
        os_type = self._detect_os_from_parameter(parameter_path)
        if os_type == OSType.WINDOWS:
            machine_image = ec2.MachineImage.from_ssm_parameter(
                parameter_name=parameter_path,
                os=ec2.OperatingSystemType.WINDOWS
            )
        else:
            machine_image = ec2.MachineImage.from_ssm_parameter(
                parameter_name=parameter_path,
                os=ec2.OperatingSystemType.LINUX
            )
        
        ami_info = AMIInfo(
            ami_id=parameter_path,  # パラメータパスを一時的に保存
            os_type=os_type
        )
        return machine_image, ami_info
```

### 3. UserDataManager (新規)

```python
class UserDataManager:
    """OS種別に応じたユーザーデータ生成"""
    
    @staticmethod
    def create_user_data(ami_info: AMIInfo) -> ec2.UserData:
        """AMI情報に基づいてユーザーデータを生成"""
        if ami_info.is_windows():
            return UserDataManager._create_windows_user_data()
        else:
            return UserDataManager._create_linux_user_data()
    
    @staticmethod
    def _create_windows_user_data() -> ec2.UserData:
        """Windows用ユーザーデータを生成"""
        user_data = ec2.UserData.for_windows()
        config = UserDataConfig.for_windows()
        for command in config.commands:
            user_data.add_commands(command)
        return user_data
    
    @staticmethod
    def _create_linux_user_data() -> ec2.UserData:
        """Linux用ユーザーデータを生成"""
        user_data = ec2.UserData.for_linux()
        config = UserDataConfig.for_linux()
        for command in config.commands:
            user_data.add_commands(command)
        return user_data
```

### 4. KeyPairManager (新規)

```python
class KeyPairManager:
    """Key Pair管理"""
    
    def __init__(self, stack: Stack):
        self.stack = stack
    
    def get_key_pair(self, key_pair_name: Optional[str]) -> Optional[ec2.IKeyPair]:
        """Key Pair名からIKeyPairオブジェクトを取得"""
        if key_pair_name:
            return ec2.KeyPair.from_key_pair_name(
                self.stack, 
                "KeyPair", 
                key_pair_name
            )
        return None
```

## 改修されたSsmEc2RdpStack

### 新しいコンストラクタ

```python
class SsmEc2RdpStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        config: EC2Configuration,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 各マネージャーの初期化
        self.ami_resolver = AMIResolver(self)
        self.user_data_manager = UserDataManager()
        self.key_pair_manager = KeyPairManager(self)
        
        # 既存リソース作成メソッドを呼び出し
        self._create_infrastructure(config)
    
    def _create_infrastructure(self, config: EC2Configuration):
        """インフラストラクチャを作成"""
        # AMI解決
        machine_image, ami_info = self.ami_resolver.resolve_ami(config.ami)
        
        # ユーザーデータ生成
        user_data = self.user_data_manager.create_user_data(ami_info)
        
        # Key Pair取得
        key_pair = self.key_pair_manager.get_key_pair(config.instance.key_pair_name)
        
        # 既存のVPC、セキュリティグループ、IAMロール作成
        vpc = self._create_vpc()
        security_group = self._create_security_group(vpc)
        ec2_role = self._create_ec2_role()
        
        # インスタンス作成
        self._create_ec2_instance(
            vpc=vpc,
            security_group=security_group,
            role=ec2_role,
            machine_image=machine_image,
            instance_type=config.instance.instance_type,
            key_pair=key_pair,
            user_data=user_data
        )
        
        # VPCエンドポイント作成
        self._create_vpc_endpoints(vpc)
        
        # EICE作成
        self._create_eice(vpc, security_group)
```

### インスタンス作成メソッド

```python
def _create_ec2_instance(
    self,
    vpc: ec2.Vpc,
    security_group: ec2.SecurityGroup,
    role: iam.Role,
    machine_image: ec2.MachineImage,
    instance_type: str,
    key_pair: Optional[ec2.IKeyPair],
    user_data: ec2.UserData
):
    """EC2インスタンスを作成"""
    instance_params = {
        "instance_type": ec2.InstanceType(instance_type),
        "machine_image": machine_image,
        "vpc": vpc,
        "vpc_subnets": ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
        "security_group": security_group,
        "role": role,
        "user_data": user_data
    }
    
    # Key Pairが指定されている場合のみ追加
    if key_pair:
        instance_params["key_pair"] = key_pair
    
    # インスタンス作成
    self.instance = ec2.Instance(self, "SsmEc2RdpInstance", **instance_params)
```

## app.py の改修

```python
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ssm_ec2_rdp.ssm_ec2_rdp_stack import SsmEc2RdpStack
from ssm_ec2_rdp.configuration_manager import ConfigurationManager

def main():
    app = cdk.App()
    
    # 設定管理
    config_manager = ConfigurationManager(app)
    
    try:
        # 設定を取得・検証
        config = config_manager.get_configuration()
        
        # スタック作成
        SsmEc2RdpStack(
            app, 
            "SsmEc2RdpDynamicStack-Takasato",
            config=config
        )
    except Exception as e:
        print(f"設定エラー: {e}")
        print(get_configuration_help())
        exit(1)
    
    app.synth()

if __name__ == "__main__":
    main()
```

## ファイル構成

### 新しいファイル構成

```
ssm_ec2_rdp/
├── __init__.py
├── ssm_ec2_rdp_stack.py          # メインスタック（改修）
├── configuration_manager.py      # 新規: 設定管理
├── ami_resolver.py               # 新規: AMI解決
├── user_data_manager.py          # 新規: ユーザーデータ管理
├── key_pair_manager.py           # 新規: Key Pair管理
├── exceptions.py                 # 新規: カスタム例外
└── types.py                      # 新規: 型定義
```

### インポート構成

```python
# ssm_ec2_rdp/__init__.py
from .ssm_ec2_rdp_stack import SsmEc2RdpStack
from .configuration_manager import ConfigurationManager
from .types import EC2Configuration, AMIConfiguration, InstanceConfiguration
from .exceptions import ConfigurationError, AMINotFoundError, KeyPairNotFoundError

__all__ = [
    'SsmEc2RdpStack',
    'ConfigurationManager', 
    'EC2Configuration',
    'AMIConfiguration',
    'InstanceConfiguration',
    'ConfigurationError',
    'AMINotFoundError',
    'KeyPairNotFoundError'
]
```

## エラーハンドリング戦略

### 1. 設定レベルのエラー
- `ConfigurationError`: 設定関連の全般的なエラー
- `MissingConfigError`: 必須項目不足
- `ConfigConflictError`: 設定競合
- `InvalidValueError`: 不正な値

### 2. リソースレベルのエラー
- `AMINotFoundError`: AMI取得失敗
- `KeyPairNotFoundError`: Key Pair取得失敗

### 3. CDKレベルのエラー
- CDK標準のエラーハンドリングに委任
- CloudFormationエラーの適切な伝播

## テスト戦略

### 1. 単体テスト
- 各マネージャークラスの個別テスト
- 設定検証ロジックのテスト
- エラーケースのテスト

### 2. 結合テスト
- スタック全体の作成テスト
- 異なる設定パターンでのテスト
- エラー伝播のテスト

### 3. E2Eテスト
- 実際のAWSリソース作成テスト
- 設定変更時の動作確認
- ロールバックテスト

## 移行戦略

### フェーズ1: 基盤実装
1. 新しい型定義とインターフェースの実装
2. 各マネージャークラスの実装
3. 単体テスト作成

### フェーズ2: スタック改修
1. SsmEc2RdpStackの改修
2. app.pyの改修
3. 結合テスト実装

### フェーズ3: 検証・デプロイ
1. 既存環境での動作確認
2. 新しい設定形式でのテスト
3. ドキュメント更新