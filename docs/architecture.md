# アーキテクチャ詳細

このドキュメントでは、SSM経由EC2アクセス環境のネットワーク構成、セキュリティ設計、IAM権限の詳細を説明します。

## 目次

- [全体構成](#全体構成)
- [ネットワーク設計](#ネットワーク設計)
- [セキュリティ設計](#セキュリティ設計)
- [IAM権限](#iam権限)
- [VPCエンドポイント](#vpcエンドポイント)
- [コスト見積もり](#コスト見積もり)
- [スケーリング考慮事項](#スケーリング考慮事項)

## 全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                           │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    VPC (10.0.0.0/16)                  │  │
│  │                                                       │  │
│  │  ┌──────────────────┐      ┌──────────────────┐     │  │
│  │  │  Public Subnet   │      │  Public Subnet   │     │  │
│  │  │   (AZ-a)         │      │   (AZ-c)         │     │  │
│  │  │  10.0.0.0/24     │      │  10.0.1.0/24     │     │  │
│  │  │                  │      │                  │     │  │
│  │  │  (使用しない)     │      │  (使用しない)     │     │  │
│  │  └──────────────────┘      └──────────────────┘     │  │
│  │                                                       │  │
│  │  ┌──────────────────┐      ┌──────────────────┐     │  │
│  │  │ Private Isolated │      │ Private Isolated │     │  │
│  │  │ Subnet (AZ-a)    │      │ Subnet (AZ-c)    │     │  │
│  │  │  10.0.2.0/24     │      │  10.0.3.0/24     │     │  │
│  │  │                  │      │                  │     │  │
│  │  │  ┌────────────┐  │      │                  │     │  │
│  │  │  │   EC2      │  │      │  ┌────────────┐  │     │  │
│  │  │  │ Instance   │  │      │  │VPC         │  │     │  │
│  │  │  │            │  │      │  │Endpoints   │  │     │  │
│  │  │  └─────┬──────┘  │      │  └─────┬──────┘  │     │  │
│  │  │        │         │      │        │         │     │  │
│  │  │        │         │      │        │         │     │  │
│  │  │  ┌─────▼──────┐  │      │  ┌─────▼──────┐  │     │  │
│  │  │  │   EICE     │  │      │  │VPC Endpoint│  │     │  │
│  │  │  │(RDP用)     │  │      │  │- SSM       │  │     │  │
│  │  │  └────────────┘  │      │  │- SSM Msg   │  │     │  │
│  │  │                  │      │  └────────────┘  │     │  │
│  │  └──────────────────┘      └──────────────────┘     │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│        ▲                                                    │
│        │ HTTPS (443)                                       │
│        │ SSM API経由                                       │
└────────┼─────────────────────────────────────────────────────┘
         │
         │
    ┌────┴────┐
    │ User    │
    │(AWS CLI)│
    └─────────┘
```

## ネットワーク設計

### VPC構成

| リソース | 値 | 説明 |
|---------|-----|------|
| VPC CIDR | 10.0.0.0/16 | 65,536個のIPアドレス |
| AZ数 | 2 | 冗長性のため複数AZを使用 |
| NAT Gateway | 0 | コスト削減、VPCエンドポイントで代替 |

### サブネット設計

#### Public Subnet

| 項目 | AZ-a | AZ-c |
|------|------|------|
| CIDR | 10.0.0.0/24 | 10.0.1.0/24 |
| 利用可能IP | 251 | 251 |
| 用途 | **現在未使用** | **現在未使用** |
| インターネットゲートウェイ | あり（アタッチのみ） | あり（アタッチのみ） |

**注意**: Public Subnetは作成されますが、EC2インスタンスは配置されません。将来の拡張用に予約されています。

#### Private Isolated Subnet

| 項目 | AZ-a | AZ-c |
|------|------|------|
| CIDR | 10.0.2.0/24 | 10.0.3.0/24 |
| 利用可能IP | 251 | 251 |
| 用途 | EC2インスタンス配置 | VPCエンドポイント |
| インターネットアクセス | なし | なし |
| ルート | ローカルのみ | ローカルのみ |

### ルートテーブル

#### Private Isolated Subnet ルートテーブル

| 送信先 | ターゲット | 説明 |
|--------|-----------|------|
| 10.0.0.0/16 | local | VPC内通信 |

**インターネット向けルートなし** - すべての外部通信はVPCエンドポイント経由

## セキュリティ設計

### セキュリティグループ

#### EC2インスタンス用セキュリティグループ

**インバウンドルール:**

| タイプ | プロトコル | ポート範囲 | ソース | 説明 |
|--------|-----------|----------|--------|------|
| RDP | TCP | 3389 | EICE SG | EC2 Instance Connect Endpointからのみ（Windows） |
| すべて | すべて | すべて | 自身のSG | 同一SG内通信許可 |

**アウトバウンドルール:**

| タイプ | プロトコル | ポート範囲 | 送信先 | 説明 |
|--------|-----------|----------|--------|------|
| HTTPS | TCP | 443 | 0.0.0.0/0 | SSM、VPCエンドポイント通信用 |

#### EC2 Instance Connect Endpoint用セキュリティグループ

**インバウンドルール:**

| タイプ | プロトコル | ポート範囲 | ソース | 説明 |
|--------|-----------|----------|--------|------|
| なし | - | - | - | インバウンド通信不要 |

**アウトバウンドルール:**

| タイプ | プロトコル | ポート範囲 | 送信先 | 説明 |
|--------|-----------|----------|--------|------|
| すべて | すべて | すべて | 0.0.0.0/0 | すべての送信を許可 |

### セキュリティ設計の原則

1. **最小権限の原則**
   - 必要最小限のポートのみ開放
   - インバウンド通信はEICE経由のみ（Windows RDP）
   - SSM経由の接続はポート開放不要

2. **Defense in Depth（多層防御）**
   - Private Subnetに配置（第1層）
   - セキュリティグループによる制限（第2層）
   - IAMロールによる権限制御（第3層）
   - VPCエンドポイントによるトラフィック制御（第4層）

3. **インターネット隔離**
   - インターネットゲートウェイへのルートなし
   - NAT Gatewayなし
   - すべての通信はAWSバックボーン経由

## IAM権限

### EC2インスタンス用IAMロール

#### 信頼ポリシー

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### アタッチされるマネージドポリシー

**AmazonSSMManagedInstanceCore**

主要な権限:
- `ssm:UpdateInstanceInformation` - SSMへの登録
- `ssmmessages:CreateControlChannel` - Session Manager接続
- `ssmmessages:CreateDataChannel` - Session Managerデータ転送
- `ssmmessages:OpenControlChannel` - Session Manager制御
- `ssmmessages:OpenDataChannel` - Session Managerデータ通信
- `ec2messages:*` - EC2メッセージング

### ユーザー/管理者に必要な権限

SSM Session Manager経由で接続するには、以下の権限が必要です:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:StartSession"
      ],
      "Resource": [
        "arn:aws:ec2:*:*:instance/*",
        "arn:aws:ssm:*:*:document/AWS-StartSSHSession",
        "arn:aws:ssm:*:*:document/AWS-StartPortForwardingSession"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:TerminateSession",
        "ssm:ResumeSession"
      ],
      "Resource": [
        "arn:aws:ssm:*:*:session/${aws:username}-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2-instance-connect:OpenTunnel"
      ],
      "Resource": "*"
    }
  ]
}
```

## VPCエンドポイント

### 必須エンドポイント

#### 1. SSM Endpoint

| 項目 | 値 |
|------|-----|
| サービス名 | com.amazonaws.[region].ssm |
| タイプ | Interface |
| サブネット | Private Isolated Subnet |
| プライベートDNS | 有効 |
| 用途 | Systems Manager API通信 |

#### 2. SSM Messages Endpoint

| 項目 | 値 |
|------|-----|
| サービス名 | com.amazonaws.[region].ssmmessages |
| タイプ | Interface |
| サブネット | Private Isolated Subnet |
| プライベートDNS | 有効 |
| 用途 | Session Managerメッセージング |

### オプションのエンドポイント

本プロジェクトでは作成されませんが、用途に応じて追加可能です:

#### EC2 Messages Endpoint

```typescript
vpc.add_interface_endpoint(
    "Ec2MessagesVpcEndpoint",
    service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
    subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
)
```

| 用途 | 必要性 |
|------|--------|
| Run Command | オプション |
| State Manager | オプション |
| Patch Manager | オプション |

#### S3 Gateway Endpoint

```python
vpc.add_gateway_endpoint(
    "S3Endpoint",
    service=ec2.GatewayVpcEndpointAwsService.S3,
    subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)]
)
```

| 用途 | 必要性 | コスト |
|------|--------|--------|
| S3アクセス | データ転送時 | 無料 |
| yum/aptリポジトリ | 推奨 | 無料 |

#### CloudWatch Logs Endpoint

```python
vpc.add_interface_endpoint(
    "CloudWatchLogsEndpoint",
    service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
    subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
)
```

## EC2 Instance Connect Endpoint (EICE)

### 概要

Windows環境でのRDPアクセスを実現するために使用。

| 項目 | 値 |
|------|-----|
| 配置サブネット | Private Isolated Subnet (AZ-a) |
| セキュリティグループ | EICE専用SG |
| preserve_client_ip | False（推奨） |
| 用途 | RDPポートフォワーディング |

### 動作原理

```
ユーザー
  ↓ aws ec2-instance-connect open-tunnel
  ↓ --local-port 13389 --remote-port 3389
  ↓
EICE (Private Subnet内)
  ↓ セキュリティグループ許可
  ↓ TCP 3389
  ↓
EC2インスタンス (Private Subnet内)
```

### セキュリティ上のメリット

1. **インターネット露出なし** - RDPポートが外部に露出しない
2. **IAM認証** - AWS認証情報で接続制御
3. **CloudTrail監査** - すべての接続が記録される
4. **VPC内通信** - トラフィックがVPC内で完結

## コスト見積もり

### 月額コスト（東京リージョン、2024年想定）

#### 必須リソース

| リソース | 時間単価 | 月額（730h） | 備考 |
|---------|---------|-------------|------|
| EC2 t3.medium | $0.0544 | $39.71 | Windows |
| EC2 t3.small | $0.0272 | $19.86 | Linux |
| VPCエンドポイント (SSM) | $0.014 | $10.22 | インターフェース型 |
| VPCエンドポイント (SSM Messages) | $0.014 | $10.22 | インターフェース型 |
| EBS gp3 30GB | - | $2.76 | $0.092/GB-月 |
| **合計（Windows）** | - | **$62.91** | データ転送費別 |
| **合計（Linux）** | - | **$43.06** | データ転送費別 |

#### オプションリソース

| リソース | 時間単価 | 月額（730h） | 用途 |
|---------|---------|-------------|------|
| NAT Gateway | $0.062 | $45.26 | 不要（VPCエンドポイントで代替） |
| VPCエンドポイント (S3) | 無料 | $0 | Gateway型 |
| VPCエンドポイント (EC2 Messages) | $0.014 | $10.22 | Run Command等 |

#### データ転送費

| 方向 | 料金 | 備考 |
|------|------|------|
| VPCエンドポイント経由 | $0.01/GB | SSM通信 |
| インターネット送信 | $0.114/GB | 本構成では発生しない |
| AZ間転送 | $0.01/GB | マルチAZ構成時 |

### コスト削減のヒント

1. **Gravitonインスタンス使用（Linux）**
   - t4g.small: $0.0218/時間（約20%削減）
   - ARM64対応が必要

2. **不要時の停止**
   ```bash
   # インスタンス停止
   aws ec2 stop-instances --instance-ids $INSTANCE_ID --profile cm

   # 停止中のコスト: EBS料金のみ（約$2.76/月）
   ```

3. **Spot Instances（非本番環境）**
   - 最大90%のコスト削減
   - 中断の可能性あり

4. **Savings PlansまたはReserved Instances**
   - 1年契約: 約30%削減
   - 3年契約: 約50%削減

## スケーリング考慮事項

### 複数インスタンス構成

複数のEC2インスタンスを構築する場合:

```python
# app.pyでループ処理
for i in range(3):
    SsmEc2RdpStack(
        app,
        f"SsmEc2RdpStack-{i}",
        config,
        env=cdk.Environment(...)
    )
```

**考慮点:**
- サブネット配分の計画
- VPCエンドポイントは共有可能（追加コストなし）
- セキュリティグループの分離

### マルチAZ配置

高可用性が必要な場合:

```python
# 各AZにインスタンスを配置
subnets = vpc.select_subnets(
    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
).subnet_ids

for i, subnet_id in enumerate(subnets):
    ec2.CfnInstance(
        self, f"Instance-AZ{i}",
        subnet_id=subnet_id,
        ...
    )
```

### Auto Scaling

SSM経由のアクセスはAuto Scalingと互換性があります:

```python
auto_scaling_group = autoscaling.AutoScalingGroup(
    self, "ASG",
    vpc=vpc,
    instance_type=ec2.InstanceType(config.instance.instance_type),
    machine_image=machine_image,
    role=ec2_role,  # SSM権限付きロール
    vpc_subnets=ec2.SubnetSelection(
        subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
    ),
    min_capacity=1,
    max_capacity=5
)
```

## トラブルシューティング

### VPCエンドポイントの確認

```bash
# エンドポイント一覧取得
aws ec2 describe-vpc-endpoints --profile cm

# 特定エンドポイントの詳細
aws ec2 describe-vpc-endpoints \
  --filters "Name=service-name,Values=com.amazonaws.ap-northeast-1.ssm" \
  --profile cm
```

### セキュリティグループルールの確認

```bash
# セキュリティグループ一覧
aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=<vpc-id>" \
  --profile cm

# 特定セキュリティグループの詳細
aws ec2 describe-security-groups \
  --group-ids <sg-id> \
  --profile cm
```

### ネットワーク疎通確認

インスタンス上で:

```bash
# VPCエンドポイントへの疎通確認
nslookup ssm.ap-northeast-1.amazonaws.com

# HTTPS接続確認
curl -I https://ssm.ap-northeast-1.amazonaws.com

# SSM接続テスト
sudo systemctl status amazon-ssm-agent
```

## 参考資料

### AWS公式ドキュメント

- [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
- [Systems Manager Prerequisites](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-prereqs.html)
- [EC2 Instance Connect Endpoint](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-using-eice.html)
- [VPC Endpoint Pricing](https://aws.amazon.com/privatelink/pricing/)

### CDKドキュメント

- [aws-cdk.aws-ec2](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2.html)
- [aws-cdk.aws-iam](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam.html)
- [VPC Construct](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)

## 次のステップ

- [Windows環境セットアップガイド](windows-setup.md) - Windows特有の設定
- [Linux環境セットアップガイド](linux-setup.md) - Linux特有の設定
- [メインドキュメント](../README.md) - プロジェクト概要
