# Windows Server環境セットアップガイド

このガイドでは、Windows Server EC2インスタンスの構築とリモートデスクトップ接続の手順を説明します。

## 目次

- [AMI選択](#ami選択)
- [デプロイ設定](#デプロイ設定)
- [リモートデスクトップ接続](#リモートデスクトップ接続)
- [自動設定内容](#自動設定内容)
- [トラブルシューティング](#トラブルシューティング)

## AMI選択

### AWS公式のWindows Server AMI

SSMパラメータを使用して、常に最新のAMIを自動的に取得できます。

#### Windows Server 2022

```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

**利用可能なWindows Server 2022パラメータ:**

| 言語 | エディション | SSMパラメータ |
|------|-------------|---------------|
| 日本語 | Full | `/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base` |
| 英語 | Full | `/aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base` |
| 英語 | Core | `/aws/service/ami-windows-latest/Windows_Server-2022-English-Core-Base` |

#### Windows Server 2019

```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2019-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

**利用可能なWindows Server 2019パラメータ:**

| 言語 | エディション | SSMパラメータ |
|------|-------------|---------------|
| 日本語 | Full | `/aws/service/ami-windows-latest/Windows_Server-2019-Japanese-Full-Base` |
| 英語 | Full | `/aws/service/ami-windows-latest/Windows_Server-2019-English-Full-Base` |
| 英語 | Core | `/aws/service/ami-windows-latest/Windows_Server-2019-English-Core-Base` |

#### Windows Server 2016

```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2016-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

### カスタムAMI使用

独自のWindows AMIを使用する場合は、AMI IDを直接指定します。

```json
{
  "context": {
    "ami-id": "ami-0a71a0b9c988d5e5e",
    "instance-type": "t3.medium",
    "key-pair-name": "my-key-pair"
  }
}
```

## デプロイ設定

### 推奨インスタンスタイプ

| 用途 | インスタンスタイプ | vCPU | メモリ | 用途例 |
|------|-------------------|------|--------|--------|
| 検証・開発 | t3.medium | 2 | 4 GB | 基本的な検証、軽量な開発作業 |
| 標準 | t3.large | 2 | 8 GB | 一般的なアプリケーション開発 |
| 高パフォーマンス | m5.xlarge | 4 | 16 GB | 重い開発作業、複数アプリケーション |
| メモリ重視 | r5.large | 2 | 16 GB | メモリ消費の多いアプリケーション |

### デプロイ実行

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# デプロイ
cdk deploy --profile cm --require-approval never

# または
./setup_and_deploy.sh
```

## リモートデスクトップ接続

### 方法1: EC2 Instance Connect Endpoint（推奨）

この方法は、最新のAWS CLIを使用してRDPポートフォワーディングを行います。

#### ステップ1: インスタンスIDを取得

```bash
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=SsmEc2RdpDynamicStack-Takasato/SsmEc2RdpInstance" \
            "Name=instance-state-name,Values=running" \
  --profile cm \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

echo "Instance ID: $INSTANCE_ID"
```

#### ステップ2: RDPポートフォワーディング開始

```bash
aws ec2-instance-connect open-tunnel \
  --instance-id $INSTANCE_ID \
  --remote-port 3389 \
  --local-port 13389 \
  --profile cm
```

このコマンドは実行したままにしておきます（Ctrl+Cで終了）。

#### ステップ3: リモートデスクトップクライアントで接続

**macOS (Microsoft Remote Desktop):**
1. App Storeから「Microsoft Remote Desktop」をインストール
2. 新しいPCを追加
   - PC名: `localhost:13389`
   - ユーザーアカウント: 必要に応じて追加
   - 接続

**Windows (標準リモートデスクトップ接続):**
1. `mstsc.exe` を起動
2. コンピューター: `localhost:13389`
3. 接続

**認証情報:**
- ユーザー名: `Administrator` または `rdpuser`（UserDataで作成される場合）
- パスワード: EC2コンソールまたはSSM経由で取得

### 方法2: Session Manager経由（代替方法）

AWS Session Managerのポートフォワーディング機能を使用します。

```bash
# macOS/Linux
aws ssm start-session \
  --target $INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["3389"],"localPortNumber":["3389"]}' \
  --profile cm

# Windows PowerShell
aws ssm start-session `
  --target $INSTANCE_ID `
  --document-name AWS-StartPortForwardingSession `
  --parameters "portNumber=3389,localPortNumber=3389" `
  --profile cm
```

接続先: `localhost:3389`

## 自動設定内容

このプロジェクトでは、UserDataを使用して以下の設定が自動的に行われます。

### リモートデスクトップの有効化

```powershell
# RDP接続を許可
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name 'fDenyTSConnections' -Value 0

# ファイアウォールでRDPを許可
Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'
```

### Network Level Authentication (NLA) の有効化

セキュリティ強化のため、NLAが有効化されます。

```powershell
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name 'UserAuthentication' -Value 1
```

### SSM Agentの確認

```powershell
Get-Service AmazonSSMAgent | Restart-Service
```

### その他の設定

- 管理者アカウントの有効化（オプション）
- Windows Updateの設定
- セットアップ完了ログの記録（`C:\userdata-completion.log`）

## パスワード取得

### EC2コンソールから取得

1. EC2コンソールでインスタンスを選択
2. 「アクション」→「セキュリティ」→「Windowsパスワードを取得」
3. キーペア（指定している場合）を使用して復号化

### SSM経由でパスワードを変更

```bash
# Session Managerでインスタンスに接続
aws ssm start-session --target $INSTANCE_ID --profile cm

# PowerShellで管理者パスワードを変更
net user Administrator 'NewSecurePassword123!'
```

## トラブルシューティング

### RDP接続ができない

#### 1. ポートフォワーディングの確認

```bash
# ポートフォワーディングが動作しているか確認
lsof -i :13389  # macOS/Linux
netstat -an | findstr 13389  # Windows
```

#### 2. インスタンスのSSM接続確認

```bash
# インスタンスがSSMで管理されているか確認
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
  --profile cm
```

#### 3. RDPサービスの状態確認

SSM Session Managerでインスタンスに接続し、PowerShellで確認:

```powershell
# RDPサービスの状態
Get-Service TermService

# RDP設定の確認
Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name 'fDenyTSConnections'

# ファイアウォールルールの確認
Get-NetFirewallRule -DisplayGroup "Remote Desktop"
```

#### 4. UserDataの実行確認

```powershell
# セットアップログの確認
Get-Content C:\userdata-completion.log

# UserData実行ログの確認
Get-Content C:\ProgramData\Amazon\EC2-Windows\Launch\Log\UserdataExecution.log
```

### 「認証エラー」が発生する

#### CredSSPエラーの場合（macOS/Linuxクライアント）

Microsoft Remote Desktopの設定:
1. PC設定を開く
2. 「管理」タブ
3. 「すべての証明書を受け入れる」にチェック

#### Windowsクライアントの場合

グループポリシーを一時的に変更（非推奨・検証環境のみ）:
1. `gpedit.msc` を実行
2. コンピューターの構成 → 管理用テンプレート → システム → 資格情報の委任
3. 「暗号化オラクルの修復」を有効化し、「脆弱」に設定

### インスタンスがSSMに表示されない

1. **IAMロールの確認**
   ```bash
   aws iam get-role --role-name <role-name> --profile cm
   ```

2. **VPCエンドポイントの確認**
   ```bash
   aws ec2 describe-vpc-endpoints --profile cm
   ```

3. **セキュリティグループの確認**
   ```bash
   aws ec2 describe-security-groups \
     --filters "Name=tag:Name,Values=*SsmEc2Rdp*" \
     --profile cm
   ```

### パフォーマンスが遅い

1. **インスタンスタイプの変更**
   - `cdk.json`の`instance-type`を変更
   - 再デプロイまたはAWSコンソールで変更

2. **EBSボリュームの最適化**
   - gp3ボリュームの使用を検討
   - IOPSとスループットの調整

## セキュリティのベストプラクティス

### 本番環境での推奨事項

1. **強力なパスワードの使用**
   ```powershell
   # 複雑なパスワードを設定
   net user Administrator 'Complex!Pass123@Word'
   ```

2. **証明書ベース認証の導入**
   - Active Directoryとの統合
   - スマートカード認証

3. **NLAの必須化**
   - すでにUserDataで有効化済み

4. **CloudWatch Logsへのログ転送**
   - RDPログインイベントの監視
   - セキュリティイベントの記録

5. **定期的なパスワードローテーション**
   - AWS Secrets Managerとの統合
   - 自動パスワード変更の実装

## 次のステップ

- [Linux環境セットアップガイド](linux-setup.md) - Linux環境の構築
- [アーキテクチャ詳細](architecture.md) - ネットワーク・セキュリティ設計の詳細
- [メインドキュメント](../README.md) - プロジェクト全体のドキュメント
