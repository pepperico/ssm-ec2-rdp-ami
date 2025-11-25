# AMI・インスタンス設定機能 アーキテクチャ設計

## システム概要

現在の動的Windows Serverバージョン選択機能を廃止し、cdk.jsonによる明示的なAMI・インスタンスタイプ・Key Pair選択機能に変更する。新しいアーキテクチャでは、設定の読み取り、検証、そして適切なEC2リソース作成を行う。

## アーキテクチャパターン

- **パターン**: Configuration-driven Infrastructure as Code
- **理由**: 設定ファイルベースでインフラリソースを柔軟に制御し、コードの変更なしに異なる構成をサポートするため

## コンポーネント構成

### CDK アプリケーション層
- **フレームワーク**: AWS CDK (Python)
- **設定管理**: cdk.json + Context API
- **バリデーション**: Python型ヒント + 実行時検証

### Infrastructure as Code 層
- **スタック**: SsmEc2RdpStack
- **リソース管理**: AWS CDK Constructs
- **設定方式**: 明示的設定ベース

### AWS リソース層
- **コンピュート**: EC2 Instance
- **ネットワーク**: VPC, セキュリティグループ, VPCエンドポイント
- **管理**: IAM Role, SSM Session Manager, Key Pair

## 設計原則

### 1. 明示的設定
- AMI IDまたはSSMパラメータパスの明示的指定を必須とする
- インスタンスタイプの明示的指定を必須とする
- Key Pairは任意指定（SSM Session Manager利用を前提）

### 2. 設定の構造
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",           // 直接AMI ID指定
    "ami-parameter": "/path/to/ssm/parameter",   // SSMパラメータパス指定
    "instance-type": "t3.large",                // インスタンスタイプ
    "key-pair-name": "my-key-pair"              // Key Pair名（任意）
  }
}
```

### 3. エラーハンドリング
- 設定検証の早期実行
- 明確なエラーメッセージの提供
- 必須設定の未指定時はエラーで終了

### 4. セキュリティ
- AMI検証による不正リソース作成の防止
- SSMパラメータアクセスの適切な権限制御
- Key Pairの存在確認（指定時のみ）
- 機密情報を含まないエラーレポート

## コンポーネント詳細

### ConfigurationManager
**責任**: cdk.json設定の読み取りと検証
- 必須設定項目の存在確認
- AMI設定の排他制御（ami-idとami-parameterの両方指定エラー）
- 設定値の妥当性チェック
- Key Pair名の妥当性検証（指定時のみ）

### AMIResolver
**責任**: AMI設定からMachineImageオブジェクトの生成
- 直接AMI ID指定のサポート
- SSMパラメータパスからのAMI取得
- Windows/Linux AMIの自動判定

### InstanceTypeValidator
**責任**: インスタンスタイプの妥当性検証
- サポートされているインスタンスタイプの確認
- リージョン固有の制約チェック

### KeyPairManager
**責任**: Key Pairの管理と検証（任意機能）
- 指定されたKey Pairの存在確認
- Key Pairなしでのインスタンス作成サポート（推奨）
- Key Pairとインスタンス作成の適切な関連付け

### UserDataManager
**責任**: OS種別に応じたユーザーデータの適用
- Windows AMI用: RDP設定、タイムゾーン設定、ユーザー作成
- Linux AMI用: 基本設定のみ
- 動的な設定切り替え

## データフロー

### 初期化フロー
1. `app.py` → cdk.json設定読み取り
2. `ConfigurationManager` → 必須設定検証
3. `AMIResolver` → AMI情報解決
4. `InstanceTypeValidator` → インスタンスタイプ検証
5. `KeyPairManager` → Key Pair検証（指定されている場合）
6. `UserDataManager` → OS判定とユーザーデータ生成
7. `SsmEc2RdpStack` → リソース作成

### 設定検証フロー
1. AMI設定の排他チェック（ami-idとami-parameterの両方指定は不可）
2. 必須項目の存在確認（AMI設定、instance-type）
3. AMI解決と存在確認
4. インスタンスタイプの有効性確認
5. Key Pair存在確認（指定時のみ）

### エラーハンドリングフロー
1. 設定検証エラー → 明確なエラーメッセージで終了
2. AMI解決エラー → エラーメッセージで終了
3. Key Pair検証エラー → エラーメッセージで終了
4. リソース作成エラー → AWS CDKのエラーハンドリングに委任

## 設定仕様

### 必須設定
- **AMI設定**: `ami-id` または `ami-parameter` のいずれか一つ
- **インスタンスタイプ**: `instance-type`

### 任意設定
- **Key Pair**: `key-pair-name`

### 廃止された設定
- `windows-version`（廃止）
- `windows-language`（廃止）

## Key Pair 管理の詳細

### Key Pair 設定オプション
1. **明示的指定**: `key-pair-name`でKey Pair名を指定
2. **未指定**: Key Pairなしでインスタンス作成（推奨）

### Key Pair 検証プロセス
1. `key-pair-name`設定の確認
2. 指定されたKey Pairの存在確認（CDK参照）
3. Key Pairとリージョンの整合性確認

### セキュリティ考慮事項
- SSM Session Managerアクセスが主要手段
- Key Pairは緊急時のアクセス手段として位置づけ
- Key Pairなしでも完全なリモートアクセス機能を提供

## 技術選択の理由

### Python AWS CDK
- 既存コードベースとの一貫性
- 豊富なEC2リソース管理機能
- 強力な型システムサポート

### cdk.json Context API
- CDKネイティブな設定管理
- 環境別設定の簡単な切り替え
- JSONスキーマ検証の容易な実装

### 明示的設定アプローチ
- 設定の透明性と予測可能性
- デバッグとトラブルシューティングの容易性
- インフラリソースの完全な制御

## 拡張性の考慮

### 将来的な機能追加
- 複数インスタンス作成のサポート
- カスタムユーザーデータテンプレート
- インスタンス監視・アラート設定
- 動的Key Pair生成機能

### 設定拡張性
- 新しい設定パラメータの追加が容易
- スキーマベースの設定検証
- 設定のバージョン管理サポート