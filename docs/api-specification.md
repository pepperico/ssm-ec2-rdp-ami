# API仕様書 - AMI・インスタンス設定機能

## 概要

このドキュメントは、AMI・インスタンス設定機能の各コンポーネントのAPIを詳細に説明します。

## ConfigurationManager

### クラス定義

```python
class ConfigurationManager:
    """EC2設定の統合管理クラス"""
    
    def __init__(self, app: core.App)
```

### メソッド詳細

#### get_configuration()

**説明**: 完全なEC2設定オブジェクトを取得します。

**シグネチャ**:
```python
def get_configuration(self) -> EC2Configuration
```

**戻り値**:
- `EC2Configuration`: 完全な設定オブジェクト

**例外**:
- `ConfigurationError`: 設定エラー（基底例外）
- `MissingConfigError`: 必須設定が不足している場合
- `ConfigConflictError`: 矛盾する設定が指定された場合  
- `InvalidValueError`: 無効な値が指定された場合

**使用例**:
```python
app = core.App()
app.node.set_context("ami-id", "ami-0123456789abcdef0")
app.node.set_context("instance-type", "t3.medium")

manager = ConfigurationManager(app)
config = manager.get_configuration()
```

## AMIResolver

### クラス定義

```python
class AMIResolver:
    """AMI情報の解決とMachineImage作成を担当"""
    
    def __init__(self, scope: core.Construct)
```

### メソッド詳細

#### resolve_ami()

**説明**: AMI設定からMachineImageとAMI情報を解決します。

**シグネチャ**:
```python
def resolve_ami(self, ami_config: AMIConfiguration) -> Tuple[IMachineImage, AMIInfo]
```

**パラメータ**:
- `ami_config`: AMI設定オブジェクト

**戻り値**:
- `Tuple[IMachineImage, AMIInfo]`: CDK MachineImageとAMI情報のタプル

**例外**:
- `AMINotFoundError`: 指定されたAMIが見つからない場合
- `InvalidValueError`: 無効なAMI設定の場合

**使用例**:
```python
ami_config = AMIConfiguration(ami_id="ami-0123456789abcdef0", ami_parameter=None)
resolver = AMIResolver(stack)
machine_image, ami_info = resolver.resolve_ami(ami_config)
```

#### get_ami_info_only()

**説明**: AMI情報のみを取得します（MachineImageは作成しません）。

**シグネチャ**:
```python
def get_ami_info_only(self, ami_config: AMIConfiguration) -> AMIInfo
```

**パラメータ**:
- `ami_config`: AMI設定オブジェクト

**戻り値**:
- `AMIInfo`: AMI情報オブジェクト

**使用例**:
```python
ami_info = resolver.get_ami_info_only(ami_config)
print(f"OS Type: {ami_info.os_type}")
```

## InstanceTypeValidator

### クラス定義

```python
class InstanceTypeValidator:
    """EC2インスタンスタイプの検証を担当"""
    
    def __init__(self)
```

### メソッド詳細

#### validate_instance_type()

**説明**: インスタンスタイプの形式を検証します。

**シグネチャ**:
```python
def validate_instance_type(self, instance_type: str) -> bool
```

**パラメータ**:
- `instance_type`: インスタンスタイプ文字列

**戻り値**:
- `bool`: 有効な場合True、無効な場合False

**例外**:
- `InvalidValueError`: 無効な形式の場合

**使用例**:
```python
validator = InstanceTypeValidator()
is_valid = validator.validate_instance_type("t3.medium")  # True
```

#### validate_and_get_info()

**説明**: インスタンスタイプを検証し、詳細情報を取得します。

**シグネチャ**:
```python
def validate_and_get_info(self, instance_type: str) -> dict
```

**パラメータ**:
- `instance_type`: インスタンスタイプ文字列

**戻り値**:
```python
{
    'instance_type': str,      # 完全なインスタンスタイプ
    'family': str,             # インスタンスファミリー
    'size': str,               # インスタンスサイズ
    'category': str,           # カテゴリ
    'is_burstable': bool       # バーストブル性能インスタンスかどうか
}
```

**使用例**:
```python
info = validator.validate_and_get_info("t3.medium")
# {
#     'instance_type': 't3.medium',
#     'family': 't3',
#     'size': 'medium',
#     'category': 'Burstable Performance',
#     'is_burstable': True
# }
```

## KeyPairManager

### クラス定義

```python
class KeyPairManager:
    """Key Pairの管理と検証を担当"""
    
    def __init__(self, scope: core.Construct)
```

### メソッド詳細

#### get_key_pair_info()

**説明**: Key Pair情報を取得します。

**シグネチャ**:
```python
def get_key_pair_info(self, key_pair_name: Optional[str]) -> dict
```

**パラメータ**:
- `key_pair_name`: Key Pair名（省略可能）

**戻り値**:
```python
{
    'key_pair_name': Optional[str],  # Key Pair名
    'is_specified': bool,            # 指定されているかどうか
    'is_valid_format': bool          # 有効な形式かどうか
}
```

**使用例**:
```python
manager = KeyPairManager(stack)
info = manager.get_key_pair_info("my-key-pair")
```

#### get_security_recommendations()

**説明**: セキュリティ推奨事項を取得します。

**シグネチャ**:
```python
def get_security_recommendations(self, key_pair_name: Optional[str]) -> List[str]
```

**パラメータ**:
- `key_pair_name`: Key Pair名（省略可能）

**戻り値**:
- `List[str]`: 推奨事項のリスト

**使用例**:
```python
recommendations = manager.get_security_recommendations("my-key-pair")
for rec in recommendations:
    print(f"推奨: {rec}")
```

#### get_key_pair()

**説明**: CDK Key Pairオブジェクトを取得します。

**シグネチャ**:
```python
def get_key_pair(self, key_pair_name: Optional[str]) -> Optional[IKeyPair]
```

**パラメータ**:
- `key_pair_name`: Key Pair名（省略可能）

**戻り値**:
- `Optional[IKeyPair]`: CDK Key Pairオブジェクト（存在しない場合はNone）

**例外**:
- `KeyPairNotFoundError`: 指定されたKey Pairが見つからない場合

## UserDataManager

### クラス定義

```python
class UserDataManager:
    """OS固有のUserData生成を担当"""
    
    def __init__(self)
```

### メソッド詳細

#### generate_user_data()

**説明**: OS種別に応じたUserDataを生成します。

**シグネチャ**:
```python
def generate_user_data(self, ami_info: AMIInfo) -> UserData
```

**パラメータ**:
- `ami_info`: AMI情報オブジェクト

**戻り値**:
- `UserData`: CDK UserDataオブジェクト

**使用例**:
```python
manager = UserDataManager()
ami_info = AMIInfo(ami_id="ami-windows", os_type=OSType.WINDOWS)
user_data = manager.generate_user_data(ami_info)
```

#### get_user_data_info()

**説明**: UserDataの詳細情報を取得します。

**シグネチャ**:
```python
def get_user_data_info(self, ami_info: AMIInfo) -> dict
```

**パラメータ**:
- `ami_info`: AMI情報オブジェクト

**戻り値**:
```python
{
    'os_type': str,           # OS種別
    'features': List[str],    # 有効化される機能のリスト
    'commands_count': int,    # 実行されるコマンド数
    'estimated_time': str     # 推定実行時間
}
```

**使用例**:
```python
info = manager.get_user_data_info(ami_info)
print(f"OS: {info['os_type']}, 機能: {info['features']}")
```

## データ型

### EC2Configuration

```python
@dataclass
class EC2Configuration:
    """EC2設定の統合オブジェクト"""
    ami: AMIConfiguration
    instance: InstanceConfiguration
```

### AMIConfiguration

```python
@dataclass
class AMIConfiguration:
    """AMI設定オブジェクト"""
    ami_id: Optional[str] = None
    ami_parameter: Optional[str] = None
    
    def __post_init__(self):
        """バリデーション: ami_id と ami_parameter のいずれかが必要"""
        if not self.ami_id and not self.ami_parameter:
            raise ValueError("ami_id または ami_parameter のいずれかが必要です")
        if self.ami_id and self.ami_parameter:
            raise ValueError("ami_id と ami_parameter は同時に指定できません")
```

### InstanceConfiguration

```python
@dataclass  
class InstanceConfiguration:
    """インスタンス設定オブジェクト"""
    instance_type: str
    key_pair_name: Optional[str] = None
    
    def __post_init__(self):
        """バリデーション: instance_type は必須"""
        if not self.instance_type:
            raise ValueError("instance_type は必須です")
```

### AMIInfo

```python
@dataclass
class AMIInfo:
    """AMI情報オブジェクト"""
    ami_id: str
    os_type: OSType
    description: Optional[str] = None
```

### OSType

```python
class OSType(Enum):
    """サポートするOS種別"""
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"
```

## 例外クラス

### 基底例外

```python
class ConfigurationError(Exception):
    """設定エラーの基底例外"""
    pass
```

### 具体的な例外

```python
class MissingConfigError(ConfigurationError):
    """必須設定が不足している場合の例外"""
    pass

class ConfigConflictError(ConfigurationError):
    """設定が競合している場合の例外"""  
    pass

class InvalidValueError(ConfigurationError):
    """無効な値が指定された場合の例外"""
    pass

class AMINotFoundError(ConfigurationError):
    """AMIが見つからない場合の例外"""
    pass

class KeyPairNotFoundError(ConfigurationError):
    """Key Pairが見つからない場合の例外"""
    pass
```

## 使用パターン

### 基本的な使用方法

```python
import aws_cdk as core
from ssm_ec2_rdp.configuration_manager import ConfigurationManager
from ssm_ec2_rdp.ssm_ec2_rdp_stack import SsmEc2RdpStack

# CDK App作成と設定
app = core.App()
app.node.set_context("ami-id", "ami-0123456789abcdef0")
app.node.set_context("instance-type", "t3.medium")
app.node.set_context("key-pair-name", "my-key-pair")

# 設定管理
config_manager = ConfigurationManager(app)
config = config_manager.get_configuration()

# スタック作成
stack = SsmEc2RdpStack(app, "MyStack", config)
```

### エラーハンドリング

```python
try:
    config = config_manager.get_configuration()
except MissingConfigError as e:
    print(f"設定不足: {e}")
except ConfigConflictError as e:
    print(f"設定競合: {e}")
except InvalidValueError as e:
    print(f"無効な値: {e}")
except ConfigurationError as e:
    print(f"設定エラー: {e}")
```

### テスト用のモック

```python
from unittest.mock import patch, Mock

with patch('ssm_ec2_rdp.ami_resolver.AMIResolver.resolve_ami') as mock_resolve:
    mock_resolve.return_value = (
        Mock(),  # Mock IMachineImage
        AMIInfo(ami_id="ami-test", os_type=OSType.WINDOWS)
    )
    # テスト実行
```