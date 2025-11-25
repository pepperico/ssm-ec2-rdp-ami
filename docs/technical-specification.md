# 技術仕様書 - AMI・インスタンス設定機能

## 概要

このドキュメントは、SSM EC2 RDP AMI プロジェクトのAMI・インスタンス設定機能の技術仕様を説明します。

## アーキテクチャ概要

### コンポーネント構成

```
ConfigurationManager
    ├── AMIResolver
    ├── InstanceTypeValidator
    ├── KeyPairManager
    └── UserDataManager
```

### データフロー

1. **設定読み込み**: CDKコンテキストから設定パラメータを取得
2. **検証**: 各コンポーネントで設定値を検証
3. **解決**: AMI情報、インスタンス設定、Key Pair情報を解決
4. **統合**: EC2Configuration オブジェクトを構築
5. **スタック作成**: 設定に基づいてCloudFormationスタックを生成

## コンポーネント仕様

### 1. ConfigurationManager

**責務**: 全体の設定管理と調整

**主要メソッド**:
- `get_configuration() -> EC2Configuration`: 完全な設定オブジェクトを取得

**設定パラメータ**:
- `ami-id`: 直接AMI IDを指定
- `ami-parameter`: SSMパラメータからAMI IDを取得
- `instance-type`: EC2インスタンスタイプ
- `key-pair-name`: (オプション) Key Pair名

**例外処理**:
- `ConfigurationError`: 設定エラーの統一例外
- `MissingConfigError`: 必須設定不足
- `ConfigConflictError`: 設定競合
- `InvalidValueError`: 無効な値

### 2. AMIResolver

**責務**: AMI情報の解決とOS種別判定

**主要メソッド**:
- `resolve_ami(ami_config: AMIConfiguration) -> Tuple[IMachineImage, AMIInfo]`
- `get_ami_info_only(ami_config: AMIConfiguration) -> AMIInfo`

**サポート機能**:
- 直接AMI ID指定
- SSMパラメータからの解決
- OS種別の自動判定 (Windows/Linux/Unknown)
- 地域別AMI対応

### 3. InstanceTypeValidator

**責務**: インスタンスタイプの検証と情報提供

**主要メソッド**:
- `validate_instance_type(instance_type: str) -> bool`
- `validate_and_get_info(instance_type: str) -> dict`

**検証機能**:
- インスタンスタイプ形式検証
- ファミリー・サイズ分離
- バーストブル性能インスタンス判定
- カテゴリ分類

### 4. KeyPairManager

**責務**: Key Pair管理と検証

**主要メソッド**:
- `get_key_pair_info(key_pair_name: Optional[str]) -> dict`
- `get_security_recommendations(key_pair_name: Optional[str]) -> List[str]`
- `get_key_pair(key_pair_name: Optional[str]) -> Optional[IKeyPair]`

**セキュリティ機能**:
- Key Pair存在チェック
- セキュリティ推奨事項提供
- SSM Session Manager使用推奨

### 5. UserDataManager

**責務**: OSに応じたユーザーデータ生成

**主要メソッド**:
- `generate_user_data(ami_info: AMIInfo) -> UserData`
- `get_user_data_info(ami_info: AMIInfo) -> dict`

**OS対応**:
- **Windows**: PowerShell スクリプト
  - リモートデスクトップ有効化
  - Windows Update設定
  - セキュリティ設定
- **Linux**: Bash スクリプト
  - システムアップデート
  - SSMエージェント確認
  - セキュリティ設定

## データ型定義

### EC2Configuration

```python
@dataclass
class EC2Configuration:
    ami: AMIConfiguration
    instance: InstanceConfiguration
```

### AMIConfiguration

```python
@dataclass
class AMIConfiguration:
    ami_id: Optional[str]
    ami_parameter: Optional[str]
```

### InstanceConfiguration

```python
@dataclass
class InstanceConfiguration:
    instance_type: str
    key_pair_name: Optional[str]
```

### AMIInfo

```python
@dataclass
class AMIInfo:
    ami_id: str
    os_type: OSType
    description: Optional[str] = None
```

### OSType

```python
class OSType(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"
```

## エラーハンドリング

### 例外階層

```
Exception
└── ConfigurationError (基底例外)
    ├── MissingConfigError (必須設定不足)
    ├── ConfigConflictError (設定競合)
    ├── InvalidValueError (無効な値)
    ├── AMINotFoundError (AMI見つからない)
    └── KeyPairNotFoundError (Key Pair見つからない)
```

### エラー伝播ポリシー

1. **コンポーネント層**: 具体的な例外を発生
2. **統合層**: ConfigurationError でラップ
3. **スタック層**: 設定エラーとしてハンドリング

## パフォーマンス要件

- **設定読み込み時間**: 1秒以内 (複数パターン)
- **スタック作成時間**: 3分以内 (テンプレート合成)
- **メモリ使用量**: 最小限のオブジェクト保持

## セキュリティ要件

### 認証・認可
- IAMロール: AmazonSSMManagedInstanceCore
- Key Pairは任意、SSM Session Manager使用推奨

### ネットワークセキュリティ
- VPCエンドポイント経由のSSM接続
- セキュリティグループ: 必要最小限の通信許可
- Instance Connect Endpoint対応

### データ保護
- ユーザーデータでの機密情報回避
- CloudFormation出力での機密情報マスク

## 拡張ポイント

### 新しいOS種別対応
1. `OSType` 列挙型に追加
2. `AMIResolver` でOS判定ロジック追加
3. `UserDataManager` でOS固有処理追加

### 新しいインスタンスファミリー対応
1. `InstanceTypeValidator` の検証ロジック更新
2. 必要に応じてファミリー固有の設定追加

### 新しい設定パラメータ
1. `AMIConfiguration` または `InstanceConfiguration` 拡張
2. `ConfigurationManager` で検証ロジック追加
3. 必要に応じて新しいコンポーネント作成

## 運用考慮事項

### 監視
- CloudWatch Logs でのデプロイメントログ
- CloudFormation スタック状態の監視

### バックアップ・復旧
- 設定パラメータの外部保存
- CloudFormation テンプレートの版管理

### メンテナンス
- AMI定期更新の仕組み
- セキュリティパッチ適用プロセス