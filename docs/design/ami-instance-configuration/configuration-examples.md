# 設定例とガイド

## cdk.json設定例

### 1. Windows Server AMI（SSMパラメータ指定）

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium",
    "key-pair-name": "windows-key-pair"
  }
}
```

### 2. Amazon Linux AMI（SSMパラメータ指定）

```json
{
  "app": "python3 app.py", 
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.small"
  }
}
```

### 3. カスタムAMI（直接AMI ID指定）

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "m5.large",
    "key-pair-name": "custom-key-pair"
  }
}
```

### 4. 高性能インスタンス設定

```json
{
  "app": "python3 app.py",
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "c5.xlarge"
  }
}
```

## 主要なSSMパラメータパス

### Windows Server AMI

```bash
# Windows Server 2022
/aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base
/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base

# Windows Server 2019  
/aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base
/aws/service/ami-windows-latest/Windows_Server-2019-Japanese-Full-Base

# Windows Server 2016
/aws/service/ami-windows-latest/Windows_Server-2016-English-Full-Base
/aws/service/ami-windows-latest/Windows_Server-2016-Japanese-Full-Base
```

### Linux AMI

```bash
# Amazon Linux 2
/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2
/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-arm64-gp2

# Amazon Linux 2023
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64

# Ubuntu 22.04 LTS
/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id
/aws/service/canonical/ubuntu/server/22.04/stable/current/arm64/hvm/ebs-gp2/ami-id
```

## インスタンスタイプ推奨設定

### 開発・テスト環境

```json
{
  "instance-type": "t3.micro"    // 最小コスト
}
{
  "instance-type": "t3.small"    // 軽い作業負荷
}
{
  "instance-type": "t3.medium"   // 標準的な作業負荷
}
```

### 本番環境

```json
{
  "instance-type": "m5.large"    // 汎用バランス型
}
{
  "instance-type": "c5.xlarge"   // CPU集約的作業
}
{
  "instance-type": "r5.large"    // メモリ集約的作業
}
```

## エラーパターンと対処法

### 1. 設定競合エラー

**エラー:**
```
ConfigConflictError: ami-idとami-parameterの両方を指定することはできません
```

**対処法:**
```json
// ❌ 間違った設定
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.medium"
  }
}

// ✅ 正しい設定（どちらか一つを選択）
{
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.medium"
  }
}
```

### 2. 必須設定不足エラー

**エラー:**
```
MissingConfigError: AMI設定が必要です。ami-idまたはami-parameterのいずれかを指定してください
```

**対処法:**
```json
// ❌ 間違った設定
{
  "context": {
    "instance-type": "t3.medium"
  }
}

// ✅ 正しい設定
{
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.medium"
  }
}
```

### 3. 無効なAMI ID形式エラー

**エラー:**
```
InvalidValueError: 無効なAMI ID形式です: ami-invalid
```

**対処法:**
```json
// ❌ 間違った設定
{
  "context": {
    "ami-id": "ami-invalid",
    "instance-type": "t3.medium"
  }
}

// ✅ 正しい設定（17文字の16進数）
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"
  }
}
```

## 移行ガイド

### 既存設定からの移行

**旧設定（廃止予定）:**
```json
{
  "context": {
    "windows-version": "2022",
    "windows-language": "Japanese",
    "key-pair-name": "my-key-pair"
  }
}
```

**新設定:**
```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium",
    "key-pair-name": "my-key-pair"
  }
}
```

### 段階的移行手順

1. **現在の設定を確認**
   ```bash
   cat cdk.json
   ```

2. **新しい設定形式に変換**
   - `windows-version: "2022"` + `windows-language: "Japanese"` 
   - → `ami-parameter: "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"`

3. **インスタンスタイプを明示的に指定**
   - デフォルト: `t3.medium`
   - 必要に応じて調整

4. **テスト環境で動作確認**
   ```bash
   cdk synth
   cdk diff
   ```

5. **本番環境に適用**
   ```bash
   cdk deploy
   ```

## ベストプラクティス

### 1. 設定の管理

- **環境別設定**: 複数の`cdk.json`ファイルを使い分け
- **バージョン管理**: 設定変更履歴をGitで管理
- **ドキュメント化**: 使用するAMIとその用途を記録

### 2. セキュリティ

- **Key Pairの使い分け**: 環境ごとに異なるKey Pairを使用
- **最小権限**: 必要最小限の権限でのSSMアクセス
- **定期更新**: AMIの定期的な更新

### 3. コスト最適化

- **インスタンスタイプ選択**: 用途に応じた適切なサイズ
- **テスト環境**: 小さいインスタンスタイプの使用
- **リソースタグ**: コスト追跡のためのタグ設定

### 4. 運用性

- **設定の標準化**: チーム内での設定形式統一
- **エラーハンドリング**: 適切なエラーメッセージの確認
- **バックアップ**: 設定ファイルのバックアップ

## トラブルシューティング

### よくある問題と解決方法

1. **AMIが見つからない**
   - リージョン固有のAMI IDを確認
   - SSMパラメータの存在確認

2. **Key Pairが見つからない**
   - Key Pairの存在確認
   - リージョンの一致確認

3. **インスタンスタイプが無効**
   - リージョンでの利用可能性確認
   - 文法の確認（例: t3.medium）

4. **権限エラー**
   - IAM権限の確認
   - SSMパラメータへのアクセス権限確認