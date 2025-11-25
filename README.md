# SSM経由でリモートデスクトップ接続可能なEC2環境（動的パラメータ対応版）

このプロジェクトでは、AWS CDKを使用してSSM（Session Manager）経由でリモートデスクトップ接続が可能なWindows EC2インスタンスを作成します。

**🆕 新機能**: cdk.jsonコンテキスト値でWindows Serverのバージョンと言語を動的に選択可能！

## 構築されるリソース

- VPC（NAT Gateway無し）
- プライベートサブネット（2つのAZ）
- セキュリティグループ（HTTPS送信のみ許可）
- Windows Server EC2インスタンス（t3.medium、動的に選択可能なバージョン・言語）
- SSM用IAMロール
- VPCエンドポイント（SSM、SSM Messages、EC2 Messages）
- EC2 Instance Connect Endpoint（EICEによるRDPアクセス用）

## 前提条件

- AWS CLI設定済み
- AWS CDK CLI インストール済み
- Python 3.7以上

## デプロイ手順

1. 仮想環境をアクティベート：
```bash
source .venv/bin/activate
```

2. 依存関係をインストール：
```bash
pip install -r requirements.txt
```

3. CDKをブートストラップ（初回のみ）：
```bash
cdk bootstrap
```

4. スタックをデプロイ：

### パラメータ設定方法

**cdk.jsonを編集:**
```json
{
  "context": {
    "windows-version": "2019",
    "windows-language": "Japanese",
    "key-pair-name": "your-key-pair-name"
  }
}
```

**利用可能なwindows-versionの値**: `"2016"`, `"2019"`, `"2022"`, `"2025"`

**デプロイ実行:**
```bash
# CDKコマンドを直接使用
cdk deploy --profile cm --require-approval never

# または便利なスクリプトを使用
./setup_and_deploy.sh
```

**注意**: 異なるバージョンをデプロイするには事前にcdk.jsonを手動編集してください。

## リモートデスクトップ接続方法

### 1. EC2 Instance Connect Endpointでポートフォワーディング

```bash
# 新しいインスタンスIDを取得
aws ec2 describe-instances --filters "Name=tag:Name,Values=SsmEc2RdpDynamicStack-Takasato/SsmEc2RdpInstance" "Name=instance-state-name,Values=running" --profile cm --query 'Reservations[0].Instances[0].InstanceId' --output text

# RDPポートフォワーディング
aws ec2-instance-connect open-tunnel --instance-id i-xxxxxxxxx --remote-port 3389 --local-port 13389 --profile cm
```

### 2. Session Managerでポートフォワーディング（代替方法）

```bash
# Windows用（PowerShell）
aws ssm start-session --target i-xxxxxxxxx --document-name AWS-StartPortForwardingSession --parameters "portNumber=3389,localPortNumber=3389"

# macOS/Linux用
aws ssm start-session --target i-xxxxxxxxx --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["3389"],"localPortNumber":["3389"]}'
```

### 3. リモートデスクトップクライアントで接続

- **接続先**: localhost:13389 (EC2 Instance Connect使用時) または localhost:3389 (Session Manager使用時)
- **ユーザー名**: rdpuser
- **パスワード**: Password123!

## 作成されるユーザー

- **ユーザー名**: rdpuser
- **パスワード**: Password123!
- **権限**: Administratorsグループ、Remote Desktop Usersグループ

## セキュリティ設定

- インスタンスはプライベートサブネットに配置
- SSM経由でのアクセスのみ許可
- キーペアは不要
- リモートデスクトップポートの直接アクセスは禁止

## クリーンアップ

```bash
cdk destroy
```

## 動的パラメータ機能

### サポートされるWindows Serverバージョン
- **2016**: Windows Server 2016
- **2019**: Windows Server 2019
- **2022**: Windows Server 2022（デフォルト）
- **2025**: Windows Server 2025

### サポートされる言語
- **English**: 英語版
- **Japanese**: 日本語版（デフォルト）

### 設定可能なパラメータ
- **windows-version**: Windows Serverバージョン（2016, 2019, 2022, または 2025）
- **windows-language**: Windows Server言語（English または Japanese）
- **key-pair-name**: EC2キーペア名（既存のキーペアを指定）

### 有効な組み合わせ
- Windows Server 2016 + English
- Windows Server 2016 + Japanese
- Windows Server 2019 + English
- Windows Server 2019 + Japanese
- Windows Server 2022 + English
- Windows Server 2022 + Japanese
- Windows Server 2025 + English
- Windows Server 2025 + Japanese

### パラメータ指定方法
**cdk.jsonのコンテキスト値のみ**（実装済み）
- デフォルト値: 2022 + Japanese

### 実装方式の特徴
- **cdk.json方式**: `cdk deploy`実行時も一貫した値が使用される
- **明示的設定**: 予測可能で設定ミスが少ない
- **シンプルな設定**: ファイル編集のみで全ての設定が完了

## 注意事項

- このサンプルは検証目的のため、本番環境では適切なセキュリティ設定を行ってください
- パスワードはデフォルトで設定されているため、本番環境では強力なパスワードまたは証明書認証を使用してください
- VPCエンドポイントにより料金が発生します

## トラブルシューティング

### インスタンスがSSMに表示されない場合

1. IAMロールが正しく設定されているか確認
2. VPCエンドポイントが正常に作成されているか確認
3. セキュリティグループでHTTPS送信が許可されているか確認

### リモートデスクトップ接続ができない場合

1. ポートフォワーディングが正常に動作しているか確認
2. インスタンスでリモートデスクトップが有効になっているか確認
3. ファイアウォール設定を確認