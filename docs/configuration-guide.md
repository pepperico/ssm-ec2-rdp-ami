# 設定手順書 - AMI・インスタンス設定機能

## 概要

このドキュメントでは、SSM EC2 RDP AMI プロジェクトの設定方法を詳しく説明します。

## 基本設定

### 必須設定項目

#### 1. AMI設定（いずれか必須）

**直接AMI ID指定**:
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0"
  }
}
```

**SSMパラメータ指定**:
```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"
  }
}
```

#### 2. インスタンス設定（必須）

```json
{
  "context": {
    "instance-type": "t3.medium"
  }
}
```

### オプション設定項目

#### Key Pair設定

```json
{
  "context": {
    "key-pair-name": "my-key-pair"
  }
}
```

**注意**: Key Pairを指定しない場合、SSM Session Managerを使用した接続が推奨されます。

## 設定パターン

### パターン1: Windows Server + Key Pair

**用途**: 従来のRDP接続を行う場合

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium",
    "key-pair-name": "windows-rdp-key"
  }
}
```

**特徴**:
- Windows Server 2022 Japanese
- RDP有効化
- Key Pair認証
- セキュリティグループでRDP許可

### パターン2: Windows Server + SSM のみ

**用途**: セキュアな接続を重視する場合

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

**特徴**:
- Windows Server 2022 Japanese
- SSM Session Manager経由のみアクセス
- Key Pairなし
- セキュリティが強化

### パターン3: Amazon Linux + SSM

**用途**: Linux環境での作業が必要な場合

```json
{
  "app": "python3 app.py", 
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.medium"
  }
}
```

**特徴**:
- Amazon Linux 2023
- SSH不要（SSM Session Manager使用）
- 自動パッチ適用
- セキュリティ最適化

### パターン4: 特定AMI ID指定

**用途**: 特定のカスタムAMIを使用する場合

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "c5.xlarge",
    "key-pair-name": "custom-key"
  }
}
```

**特徴**:
- カスタムAMI使用
- 高性能インスタンス
- 任意のOS対応

## 詳細設定ガイド

### AMI設定の選択指針

#### SSMパラメータ使用推奨ケース
- 最新のAMIを常に使用したい
- 自動的なセキュリティアップデートが必要
- マルチリージョンデプロイメント

**Windows Server推奨パラメータ**:
```
/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base
/aws/service/ami-windows-latest/Windows_Server-2019-Japanese-Full-Base
```

**Amazon Linux推奨パラメータ**:
```
/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
```

#### 直接AMI ID指定推奨ケース
- 特定のAMIバージョンで固定したい
- カスタムAMIを使用する
- テスト環境での再現性重視

### インスタンスタイプ選択指針

#### 汎用ワークロード

**軽量作業**:
```
t3.micro   # 開発・テスト環境
t3.small   # 軽量本番環境
t3.medium  # 標準的な用途（推奨）
```

**継続的な負荷**:
```
m5.large   # バランス重視
m5.xlarge  # 中程度の負荷
m5.2xlarge # 高負荷環境
```

#### 特化ワークロード

**CPU集約的**:
```
c5.large
c5.xlarge
c5.2xlarge
```

**メモリ集約的**:
```  
r5.large
r5.xlarge
r5.2xlarge
```

**ストレージ集約的**:
```
i3.large
i3.xlarge
```

### Key Pair設定指針

#### Key Pair使用推奨ケース
- 従来のSSH/RDP接続が必要
- 外部ツールとの連携が必要
- レガシーアプリケーションのサポート

#### SSM Session Manager推奨ケース（Key Pairなし）
- セキュリティを最優先する
- 監査要件が厳しい環境
- ネットワーク隔離された環境

## セキュリティ設定

### ネットワーク設定

**VPCエンドポイント**:
- SSM
- SSM Messages
- EC2 Messages

**セキュリティグループ**:
- アウトバウンド: HTTPS（443）のみ
- インバウンド: 最小限（RDPが必要な場合のみ）

### IAM設定

**必須ポリシー**:
- `AmazonSSMManagedInstanceCore`

**オプションポリシー**:
- `CloudWatchAgentServerPolicy`（ログ収集時）

## トラブルシューティング

### 設定エラー

#### ConfigurationError: AMI設定が必要です

**原因**: `ami-id` と `ami-parameter` のどちらも指定されていない

**解決策**:
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"
  }
}
```

#### ConfigurationError: 両方を指定することはできません

**原因**: `ami-id` と `ami-parameter` が同時に指定されている

**解決策**: いずれか一方のみを指定
```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

#### ConfigurationError: instance-typeは必須設定項目です

**原因**: `instance-type` が指定されていない

**解決策**:
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"
  }
}
```

#### ConfigurationError: 無効なインスタンスタイプ形式

**原因**: 無効なインスタンスタイプが指定されている

**解決策**: 正しい形式で指定
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"  // 正しい形式: family.size
  }
}
```

### デプロイメントエラー

#### AMI not found エラー

**原因**: 指定されたAMI IDが存在しない、またはアクセス権限がない

**解決策**:
1. AMI IDの確認
2. リージョンの確認
3. AMI権限の確認

#### Key Pair not found エラー

**原因**: 指定されたKey Pairが存在しない

**解決策**:
1. Key Pair名の確認
2. リージョンの確認
3. Key Pairなしでの実行を検討

### 接続エラー

#### SSM Session Manager接続失敗

**チェックポイント**:
1. IAMロール設定の確認
2. VPCエンドポイント設定の確認
3. セキュリティグループ設定の確認
4. SSMエージェントの状態確認

**解決手順**:
```bash
# EC2インスタンスの状態確認
aws ssm describe-instance-information

# エージェント状態確認
aws ssm get-connection-status --target instance-id
```

#### RDP接続失敗

**チェックポイント**:
1. セキュリティグループでポート3389許可
2. Windows Remote Desktop有効化
3. Key Pairの正確性

**解決手順**:
1. EC2コンソールで「接続」を選択
2. 「RDPクライアント」タブで設定確認
3. セキュリティグループの確認

### パフォーマンス問題

#### 設定読み込み時間が長い

**原因**: ネットワーク遅延、SSMパラメータアクセス遅延

**解決策**:
1. 直接AMI ID使用を検討
2. リージョン最適化
3. ネットワーク設定の見直し

#### スタック作成時間が長い

**原因**: リソース作成の依存関係、AMI起動時間

**対処法**:
1. タイムアウト設定の調整
2. インスタンスタイプの見直し
3. 段階的デプロイメント

## ベストプラクティス

### セキュリティ

1. **Key Pairは可能な限り使用しない**
   - SSM Session Managerを優先
   
2. **最小権限の原則**
   - 必要最小限のIAMポリシー
   - セキュリティグループルール

3. **定期的な更新**
   - SSMパラメータ使用でAMI自動更新
   - セキュリティパッチの適用

### パフォーマンス

1. **適切なインスタンスタイプ選択**
   - ワークロードに応じた最適化
   - コスト効率の考慮

2. **リージョン最適化**
   - レイテンシを考慮したリージョン選択
   - 利用者との地理的近接性

### 運用

1. **設定の外部化**
   - 環境別のcdk.json
   - パラメータファイルの分離

2. **監視・ログ**
   - CloudWatch統合
   - 操作ログの記録

3. **バックアップ戦略**
   - 設定ファイルの版管理
   - インスタンススナップショット

## 環境別設定例

### 開発環境

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.micro"
  }
}
```

### ステージング環境

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

### 本番環境

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "m5.large",
    "key-pair-name": "prod-secure-key"
  }
}
```

## 設定検証

### 設定妥当性の確認

```bash
# CDKでの構文チェック
cdk synth

# 設定の詳細表示
cdk context

# リソース一覧の確認
cdk list
```

### テストデプロイメント

```bash
# テスト環境へのデプロイ
cdk deploy --profile test-env

# ヘルスチェック
aws ssm describe-instance-information

# 接続テスト
aws ssm start-session --target instance-id
```

このガイドに従って設定を行うことで、セキュアで効率的なEC2環境を構築できます。