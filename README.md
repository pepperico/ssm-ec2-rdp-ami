# SSM経由でEC2にセキュアにアクセスする環境構築

AWS CDKを使用して、SSM (Session Manager) 経由でセキュアにアクセス可能なEC2環境を構築するプロジェクトです。
Windows ServerとLinuxの両方に対応しており、プライベートサブネットに配置されたEC2インスタンスにインターネットゲートウェイなしでアクセスできます。

## 主な機能

- 🔒 **セキュアなアクセス**: SSM経由のみでEC2にアクセス（インターネットゲートウェイ不要）
- 🖥️ **柔軟なAMI選択**: 直接AMI IDまたはSSMパラメータで任意のOSを選択可能
- 🪟 **Windows対応**: RDP接続をEC2 Instance Connect Endpoint経由で実現
- 🐧 **Linux対応**: SSH接続をSSM Session Manager経由で実現
- ⚙️ **自動設定**: UserDataによるOS別の初期設定を自動実行

## 構築されるリソース

| リソース | 説明 |
|---------|------|
| VPC | NAT Gateway無し、Public + Private Isolated サブネット (2 AZ) |
| セキュリティグループ | HTTPS送信のみ許可（SSM通信用） |
| EC2インスタンス | 任意のAMI、インスタンスタイプを指定可能 |
| IAMロール | SSM Session Manager用の権限 |
| VPCエンドポイント | SSM、SSM Messages用 |
| EC2 Instance Connect Endpoint | RDPアクセス用（Windows環境） |

## 前提条件

- AWS CLI設定済み
- AWS CDK CLI インストール済み (`npm install -g aws-cdk`)
- Python 3.7以上
- 仮想環境（推奨）

## クイックスタート

### 1. 環境準備

```bash
# リポジトリのクローン（既にある場合はスキップ）
cd /Users/takasato.wataru/claudecode-pj/ssm-ec2-rdp-ami

# 仮想環境をアクティベート
source .venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 設定ファイルの編集

`cdk.json` の `context` セクションを編集します:

```json
{
  "context": {
    "ami-id": "ami-xxxxxxxxxxxxxxxxx",
    "instance-type": "t3.medium",
    "key-pair-name": "your-key-pair"
  }
}
```

#### 設定パラメータ

| パラメータ | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| `ami-id` | ◯* | AMI ID | `"ami-0a71a0b9c988d5e5e"` |
| `ami-parameter` | ◯* | SSMパラメータパス | `"/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base"` |
| `instance-type` | ◯ | EC2インスタンスタイプ | `"t3.medium"`, `"m5.large"` |
| `key-pair-name` | - | キーペア名（オプション） | `"my-key-pair"` |

\* `ami-id` または `ami-parameter` のいずれか一つを指定

#### よく使うSSMパラメータ例

**Windows Server:**
- Windows Server 2022 日本語: `/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base`
- Windows Server 2022 英語: `/aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base`
- Windows Server 2019 日本語: `/aws/service/ami-windows-latest/Windows_Server-2019-Japanese-Full-Base`

**Linux:**
- Amazon Linux 2023: `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64`
- Amazon Linux 2: `/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2`
- Ubuntu 22.04: `/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id`

### 3. デプロイ

```bash
# CDKブートストラップ（初回のみ）
cdk bootstrap --profile cm

# デプロイ実行
cdk deploy --profile cm --require-approval never

# または便利なスクリプトを使用
./setup_and_deploy.sh
```

### 4. アクセス方法

デプロイ完了後のアクセス方法はOSによって異なります。

- **Windows環境**: [Windows接続ガイド](docs/windows-setup.md)を参照
- **Linux環境**: [Linux接続ガイド](docs/linux-setup.md)を参照

## ドキュメント

- 📘 [Windows環境セットアップガイド](docs/windows-setup.md) - Windows Server特有の設定とRDPアクセス手順
- 📗 [Linux環境セットアップガイド](docs/linux-setup.md) - Linux特有の設定とSSHアクセス手順
- 📙 [アーキテクチャ詳細](docs/architecture.md) - ネットワーク構成、セキュリティ設計の詳細

## セキュリティ設計

- ✅ プライベートサブネットに配置、インターネットゲートウェイなし
- ✅ SSM経由のみでアクセス可能
- ✅ 最小限のアウトバウンドルール（HTTPS/443のみ）
- ✅ VPCエンドポイント経由でAWSサービスと通信
- ✅ EC2 Instance Connect Endpointによる安全なRDPアクセス（Windows）

## クリーンアップ

リソースを削除する場合:

```bash
cdk destroy --profile cm

# または
./cleanup.sh
```

## 注意事項

- ⚠️ このサンプルは検証・開発目的です。本番環境では適切なセキュリティ設定を行ってください
- ⚠️ デフォルトパスワードが設定されています。本番環境では強力なパスワードまたは証明書認証を使用してください
- 💰 VPCエンドポイントにより料金が発生します（約$0.01/時間 + データ転送量）

## トラブルシューティング

### インスタンスがSSMに表示されない

1. IAMロールが正しく設定されているか確認
2. VPCエンドポイント（SSM、SSM Messages）が正常に作成されているか確認
3. セキュリティグループでHTTPS送信が許可されているか確認
4. SSM Agentが起動しているか確認（最新のAMIでは自動起動）

### デプロイエラーが発生する

1. `cdk.json`の設定を確認（AMI ID、インスタンスタイプの形式）
2. AWS認証情報が正しく設定されているか確認
3. 指定したAMI IDが存在するか確認
4. 指定したKey Pairが存在するか確認（指定した場合）

詳細は各OS別ドキュメントのトラブルシューティングセクションを参照してください。

## ライセンス

MIT License

## 参考リンク

- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [AWS CDK Python Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [EC2 Instance Connect Endpoint](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-using-eice.html)
