# Linux環境セットアップガイド

このガイドでは、Linux EC2インスタンスの構築とSSH接続の手順を説明します。

## 目次

- [AMI選択](#ami選択)
- [デプロイ設定](#デプロイ設定)
- [SSH接続](#ssh接続)
- [自動設定内容](#自動設定内容)
- [トラブルシューティング](#トラブルシューティング)

## AMI選択

### AWS公式のLinux AMI

SSMパラメータを使用して、常に最新のAMIを自動的に取得できます。

#### Amazon Linux 2023

```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64",
    "instance-type": "t3.small"
  }
}
```

**利用可能なAmazon Linux 2023パラメータ:**

| アーキテクチャ | カーネル | SSMパラメータ |
|---------------|---------|---------------|
| x86_64 | 6.1 | `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64` |
| x86_64 | デフォルト | `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64` |
| ARM64 | 6.1 | `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-arm64` |

#### Amazon Linux 2

```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2",
    "instance-type": "t3.small"
  }
}
```

**利用可能なAmazon Linux 2パラメータ:**

| タイプ | アーキテクチャ | SSMパラメータ |
|--------|---------------|---------------|
| HVM | x86_64 | `/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2` |
| HVM | ARM64 | `/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-arm64-gp2` |
| Minimal | x86_64 | `/aws/service/ami-amazon-linux-latest/amzn2-ami-minimal-hvm-x86_64-ebs` |

#### Ubuntu

```json
{
  "context": {
    "ami-parameter": "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
    "instance-type": "t3.small"
  }
}
```

**利用可能なUbuntuパラメータ:**

| バージョン | アーキテクチャ | SSMパラメータ |
|-----------|---------------|---------------|
| 22.04 LTS | amd64 | `/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id` |
| 20.04 LTS | amd64 | `/aws/service/canonical/ubuntu/server/20.04/stable/current/amd64/hvm/ebs-gp2/ami-id` |
| 22.04 LTS | arm64 | `/aws/service/canonical/ubuntu/server/22.04/stable/current/arm64/hvm/ebs-gp2/ami-id` |

### カスタムAMI使用

独自のLinux AMIを使用する場合は、AMI IDを直接指定します。

```json
{
  "context": {
    "ami-id": "ami-0c2d06d50ce30b442",
    "instance-type": "t3.small",
    "key-pair-name": "my-key-pair"
  }
}
```

## デプロイ設定

### 推奨インスタンスタイプ

| 用途 | インスタンスタイプ | vCPU | メモリ | 用途例 |
|------|-------------------|------|--------|--------|
| 検証・軽量 | t3.micro | 2 | 1 GB | 基本的な検証、CLIツール |
| 標準 | t3.small | 2 | 2 GB | 一般的な開発作業 |
| 開発 | t3.medium | 2 | 4 GB | コンテナ、複数サービス |
| 高パフォーマンス | m5.large | 2 | 8 GB | ビルドサーバー、データ処理 |
| コンピューティング重視 | c5.large | 2 | 4 GB | CPU集約的な処理 |

### ARM64インスタンス（Graviton）

コストパフォーマンスに優れたGravitonプロセッサを使用:

```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-arm64",
    "instance-type": "t4g.small"
  }
}
```

| インスタンスタイプ | vCPU | メモリ | コスト削減 |
|-------------------|------|--------|-----------|
| t4g.micro | 2 | 1 GB | ~20% |
| t4g.small | 2 | 2 GB | ~20% |
| t4g.medium | 2 | 4 GB | ~20% |

### デプロイ実行

```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# デプロイ
cdk deploy --profile cm --require-approval never

# または
./setup_and_deploy.sh
```

## SSH接続

### 方法1: SSM Session Manager（推奨）

キーペア不要でSSH接続が可能です。セキュアでポートフォワーディングも不要です。

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

#### ステップ2: Session Managerで接続

```bash
aws ssm start-session \
  --target $INSTANCE_ID \
  --profile cm
```

接続後、通常のシェル操作が可能です。

#### ステップ3: sudoで管理者権限

```bash
# Amazon Linux/RHEL系
sudo su -

# Ubuntu
sudo -i
```

### 方法2: SSHポートフォワーディング

標準のSSHクライアントを使用したい場合。

#### SSM Session Managerプラグインのインストール

**macOS (Homebrew):**
```bash
brew install --cask session-manager-plugin
```

**Linux:**
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

#### SSH接続設定

`~/.ssh/config` に以下を追加:

```ssh-config
# SSM経由のSSH接続
host i-* mi-*
    ProxyCommand sh -c "aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p' --profile cm"
    User ec2-user
```

#### 接続

```bash
# Amazon Linux
ssh $INSTANCE_ID

# Ubuntu（ユーザー名が異なる）
ssh -l ubuntu $INSTANCE_ID

# または直接
ssh ec2-user@$INSTANCE_ID
```

### 方法3: キーペアでSSH（Session Manager経由）

キーペアを指定している場合、SSH認証にも使用できます。

```bash
ssh -i ~/.ssh/my-key-pair.pem ec2-user@$INSTANCE_ID
```

**デフォルトユーザー名:**

| ディストリビューション | デフォルトユーザー名 |
|---------------------|-------------------|
| Amazon Linux 2023/2 | ec2-user |
| Ubuntu | ubuntu |
| Debian | admin |
| RHEL | ec2-user |
| SUSE | ec2-user |

## 自動設定内容

このプロジェクトでは、UserDataを使用して以下の設定が自動的に行われます。

### システムアップデート

```bash
# Amazon Linux/RHEL系
yum update -y

# Ubuntu/Debian系
apt-get update && apt-get upgrade -y
```

### SSM Agentのインストールと有効化

```bash
# Amazon Linux/RHEL系
yum install -y amazon-ssm-agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Ubuntu/Debian系（必要に応じて）
wget https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_amd64/amazon-ssm-agent.deb
dpkg -i amazon-ssm-agent.deb
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent
```

### 基本ツールのインストール

```bash
# Amazon Linux/RHEL系
yum install -y htop curl wget unzip

# Ubuntu/Debian系
apt-get install -y htop curl wget unzip
```

### SSH セキュリティ強化

```bash
# パスワード認証を無効化（キーペア認証を推奨）
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config
systemctl reload sshd
```

### セットアップログ

```bash
echo 'User data setup completed successfully at $(date)' | tee /tmp/userdata-completion.log
```

## 高度な使い方

### ポートフォワーディング（ローカル→リモート）

リモートインスタンス上のサービス（Webサーバーなど）にローカルからアクセス:

```bash
# 例: リモートの8080ポートをローカルの8080で公開
aws ssm start-session \
  --target $INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}' \
  --profile cm
```

ブラウザで `http://localhost:8080` にアクセス可能。

### ファイル転送

#### SCPを使用（SSH設定済みの場合）

```bash
# ローカル → リモート
scp -i ~/.ssh/my-key.pem local-file.txt ec2-user@$INSTANCE_ID:/home/ec2-user/

# リモート → ローカル
scp -i ~/.ssh/my-key.pem ec2-user@$INSTANCE_ID:/home/ec2-user/remote-file.txt ./
```

#### S3経由

```bash
# ローカルからS3へアップロード
aws s3 cp local-file.txt s3://my-bucket/file.txt --profile cm

# インスタンスからS3からダウンロード
aws ssm start-session --target $INSTANCE_ID --profile cm
aws s3 cp s3://my-bucket/file.txt /home/ec2-user/
```

### コマンドの実行（Run Command）

インスタンスに接続せずにコマンドを実行:

```bash
aws ssm send-command \
  --instance-ids $INSTANCE_ID \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["df -h","free -m","uptime"]' \
  --profile cm
```

## トラブルシューティング

### SSM接続ができない

#### 1. インスタンスがSSMに登録されているか確認

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
  --profile cm
```

出力がない場合:
- IAMロールが正しくアタッチされているか確認
- VPCエンドポイント（SSM、SSM Messages）が作成されているか確認
- SSM Agentが起動しているか確認

#### 2. SSM Agentの状態確認

インスタンスに別の方法（EC2 Instance Connect等）で接続し:

```bash
# SSM Agentの状態確認
sudo systemctl status amazon-ssm-agent

# ログの確認
sudo tail -f /var/log/amazon/ssm/amazon-ssm-agent.log
```

#### 3. IAMロールの確認

```bash
# インスタンスプロファイルの確認
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].IamInstanceProfile' \
  --profile cm

# ロールにSSM権限があるか確認
aws iam list-attached-role-policies \
  --role-name <role-name> \
  --profile cm
```

### SSH接続エラー

#### Permission denied (publickey)

```bash
# 正しいユーザー名を使用しているか確認
# Amazon Linux: ec2-user
# Ubuntu: ubuntu

ssh -l ubuntu $INSTANCE_ID

# キーペアのパーミッション確認
chmod 400 ~/.ssh/my-key-pair.pem
```

#### SSH設定が機能しない

```bash
# ProxyCommandが正しく設定されているか確認
ssh -v $INSTANCE_ID

# Session Managerプラグインがインストールされているか確認
session-manager-plugin --version
```

### UserDataが実行されない

#### 実行ログの確認

```bash
# Amazon Linux/RHEL系
sudo cat /var/log/cloud-init-output.log

# Ubuntu
sudo cat /var/log/cloud-init.log

# UserData完了ログ
cat /tmp/userdata-completion.log
```

#### 再実行

UserDataは初回起動時のみ実行されます。再実行する場合:

```bash
# cloud-initの状態をクリア
sudo rm -rf /var/lib/cloud/instances
sudo reboot
```

### パフォーマンスが遅い

#### システムリソースの確認

```bash
# CPU/メモリ使用状況
htop

# ディスク使用状況
df -h

# ディスクI/O
iostat -x 1
```

#### EBSボリューム最適化

```bash
# EBSボリューム情報確認
aws ec2 describe-volumes \
  --filters "Name=attachment.instance-id,Values=$INSTANCE_ID" \
  --profile cm

# gp3ボリュームへの変更（コンソールで実行推奨）
# IOPS/スループットの調整が可能
```

## セキュリティのベストプラクティス

### 本番環境での推奨事項

1. **パスワード認証の無効化**
   ```bash
   # すでにUserDataで設定済み
   sudo grep PasswordAuthentication /etc/ssh/sshd_config
   ```

2. **定期的なセキュリティアップデート**
   ```bash
   # Amazon Linux
   sudo yum update -y

   # Ubuntu
   sudo apt-get update && sudo apt-get upgrade -y
   ```

3. **fail2banの導入**（外部アクセスがある場合）
   ```bash
   # インストール
   sudo yum install -y fail2ban  # Amazon Linux
   sudo apt-get install -y fail2ban  # Ubuntu

   # 有効化
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

4. **CloudWatch Logsへのログ転送**
   ```bash
   # CloudWatch Agentのインストール
   wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
   sudo rpm -U ./amazon-cloudwatch-agent.rpm
   ```

5. **必要最小限のパッケージのみインストール**
   ```bash
   # 不要なサービスの停止
   sudo systemctl disable <unnecessary-service>
   ```

## パッケージ管理

### よく使うコマンド

#### Amazon Linux/RHEL系 (yum/dnf)

```bash
# パッケージ検索
yum search <package-name>

# パッケージインストール
sudo yum install -y <package-name>

# パッケージ削除
sudo yum remove <package-name>

# インストール済みパッケージ一覧
yum list installed
```

#### Ubuntu/Debian系 (apt)

```bash
# パッケージ検索
apt-cache search <package-name>

# パッケージインストール
sudo apt-get install -y <package-name>

# パッケージ削除
sudo apt-get remove <package-name>

# インストール済みパッケージ一覧
dpkg -l
```

## 次のステップ

- [Windows環境セットアップガイド](windows-setup.md) - Windows環境の構築
- [アーキテクチャ詳細](architecture.md) - ネットワーク・セキュリティ設計の詳細
- [メインドキュメント](../README.md) - プロジェクト全体のドキュメント
