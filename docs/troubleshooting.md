# トラブルシューティングガイド - AMI・インスタンス設定機能

## 概要

このドキュメントでは、AMI・インスタンス設定機能で発生する可能性のある問題とその解決方法を説明します。

## エラー分類

### 設定エラー（Configuration Errors）

#### ConfigurationError: AMI設定が必要です

**症状**:
```
ssm_ec2_rdp.types.ConfigurationError: AMI設定が必要です。ami-id または ami-parameter のいずれかを指定してください。
```

**原因**: 
- `ami-id` と `ami-parameter` のどちらも指定されていない

**解決方法**:
```json
// cdk.json に以下のいずれかを追加
{
  "context": {
    // パターン1: 直接AMI ID指定
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"
  }
}

// または

{
  "context": {
    // パターン2: SSMパラメータ指定
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

**検証コマンド**:
```bash
cdk context
```

#### ConfigurationError: ami-id と ami-parameter の両方を指定することはできません

**症状**:
```
ssm_ec2_rdp.types.ConfigurationError: ami-id と ami-parameter の両方を指定することはできません。いずれか一方のみを指定してください。
```

**原因**: 
- `ami-id` と `ami-parameter` が同時に指定されている

**解決方法**:
```json
// 誤った設定例
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base", // 削除
    "instance-type": "t3.medium"
  }
}

// 正しい設定例
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"
  }
}
```

#### ConfigurationError: instance-typeは必須設定項目です

**症状**:
```
ssm_ec2_rdp.types.ConfigurationError: instance-typeは必須設定項目です。
```

**原因**: 
- `instance-type` が指定されていない

**解決方法**:
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"  // 追加
  }
}
```

#### ConfigurationError: 無効なインスタンスタイプ形式

**症状**:
```
ssm_ec2_rdp.types.InvalidValueError: 無効なインスタンスタイプ形式: invalid.type
```

**原因**: 
- インスタンスタイプの形式が正しくない

**解決方法**:
```json
// 誤った形式の例
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "invalid.type"  // 無効
  }
}

// 正しい形式の例
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",
    "instance-type": "t3.medium"  // 有効
  }
}
```

**有効なインスタンスタイプの例**:
- `t3.micro`, `t3.small`, `t3.medium`, `t3.large`
- `m5.large`, `m5.xlarge`, `m5.2xlarge`
- `c5.large`, `c5.xlarge`, `c5.2xlarge`
- `r5.large`, `r5.xlarge`, `r5.2xlarge`

### デプロイメントエラー（Deployment Errors）

#### AMINotFoundError: AMI not found

**症状**:
```
ssm_ec2_rdp.types.AMINotFoundError: 指定されたAMI 'ami-0123456789abcdef0' が見つかりません。
```

**原因**: 
1. AMI IDが存在しない
2. AMIが異なるリージョンに存在する
3. AMIへのアクセス権限がない
4. AMIが廃止されている

**解決方法**:

1. **AMI IDの確認**:
```bash
aws ec2 describe-images --image-ids ami-0123456789abcdef0
```

2. **リージョンの確認**:
```bash
aws ec2 describe-images --image-ids ami-0123456789abcdef0 --region us-east-1
```

3. **利用可能なAMIの検索**:
```bash
# Windows Server 2022 Japanese
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=Windows_Server-2022-Japanese-Full-Base*" \
  --query 'Images[*].[ImageId,Name,CreationDate]' \
  --output table

# Amazon Linux 2023  
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-*" \
  --query 'Images[*].[ImageId,Name,CreationDate]' \
  --output table
```

4. **SSMパラメータの使用を検討**:
```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
  }
}
```

#### KeyPairNotFoundError: Key Pair not found

**症状**:
```
ssm_ec2_rdp.types.KeyPairNotFoundError: 指定されたKey Pair 'nonexistent-key' が見つかりません。
```

**原因**: 
1. Key Pair名が存在しない
2. Key Pairが異なるリージョンに存在する
3. Key Pairへのアクセス権限がない

**解決方法**:

1. **Key Pairの確認**:
```bash
aws ec2 describe-key-pairs --key-names your-key-name
```

2. **利用可能なKey Pairの一覧**:
```bash
aws ec2 describe-key-pairs --query 'KeyPairs[*].[KeyName,KeyFingerprint]' --output table
```

3. **新しいKey Pairの作成**:
```bash
aws ec2 create-key-pair --key-name my-new-key --output text --query 'KeyMaterial' > my-new-key.pem
chmod 400 my-new-key.pem
```

4. **Key Pairなしでの実行を検討**:
```json
{
  "context": {
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",
    "instance-type": "t3.medium"
    // key-pair-name を削除してSSM Session Managerを使用
  }
}
```

### CDKエラー（CDK Errors）

#### JSII Type Error

**症状**:
```
AttributeError: 'MockMachineImage' object has no attribute '__jsii_type__'
```

**原因**: 
- テスト時のMockオブジェクトが不完全

**解決方法** (テスト用):
```python
class MockMachineImage:
    def __init__(self, ami_id: str):
        self.ami_id = ami_id
        self.__jsii_type__ = "aws-cdk-lib.aws_ec2.IMachineImage"  # 追加
```

#### CloudFormation Resource Limit Error

**症状**:
```
CREATE_FAILED: Resource limit exceeded
```

**原因**: 
- AWSアカウントでのリソース制限に達している

**解決方法**:
1. **現在の使用量確認**:
```bash
aws service-quotas list-service-quotas --service-code ec2
```

2. **制限緩和の申請**:
- AWS Service Quotas コンソールから申請

3. **既存リソースの清理**:
```bash
# 使用していないスタックの削除
cdk destroy unused-stack
```

### ネットワークエラー（Network Errors）

#### VPC Endpoint接続エラー

**症状**:
- SSM Session Manager接続失敗
- インスタンスがSSMに登録されない

**原因**: 
- VPCエンドポイント設定の問題
- セキュリティグループ設定の問題

**解決方法**:

1. **VPCエンドポイントの確認**:
```bash
aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[*].[ServiceName,State]' --output table
```

2. **セキュリティグループの確認**:
```bash
aws ec2 describe-security-groups --group-names SSM-SecurityGroup
```

3. **アウトバウンドルールの確認**:
- HTTPS（ポート443）が許可されているか確認

4. **DNS設定の確認**:
```bash
# インスタンス内から実行
nslookup ssm.region.amazonaws.com
```

#### Session Manager接続失敗

**症状**:
```
SessionManagerPlugin is not found. Please refer to SessionManager Documentation here: http://docs.aws.amazon.com/console/systems-manager/session-manager-plugin-not-found
```

**原因**: 
- Session Manager プラグインがインストールされていない

**解決方法**:

1. **macOS**:
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip" -o "sessionmanager-bundle.zip"
unzip sessionmanager-bundle.zip
sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin
```

2. **Ubuntu/Debian**:
```bash
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

3. **Windows**:
- [公式インストーラ](https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe)をダウンロードして実行

### パフォーマンス問題（Performance Issues）

#### 設定読み込み時間が長い

**症状**:
- `ConfigurationManager.get_configuration()` の実行に時間がかかる

**原因**: 
- SSMパラメータの解決に時間がかかっている
- ネットワーク遅延

**解決方法**:

1. **直接AMI IDの使用**:
```json
{
  "context": {
    "ami-id": "ami-0123456789abcdef0",  // SSMパラメータの代わりに直接指定
    "instance-type": "t3.medium"
  }
}
```

2. **リージョンの最適化**:
```bash
export AWS_DEFAULT_REGION=us-west-2  # 最も近いリージョンを選択
```

3. **ネットワーク設定の確認**:
```bash
ping s3.amazonaws.com
traceroute s3.amazonaws.com
```

#### スタック作成時間が長い

**症状**:
- `cdk deploy` が完了するまでに時間がかかる

**原因**: 
- EC2インスタンスの起動時間
- UserDataスクリプトの実行時間

**解決方法**:

1. **より小さなインスタンスタイプの検討**:
```json
{
  "context": {
    "instance-type": "t3.micro"  // t3.mediumの代わりに
  }
}
```

2. **UserDataの最適化**:
- 必要最小限のコマンドのみ実行
- 並列実行の活用

3. **タイムアウト設定の調整**:
```python
# CDKスタック内で
ec2.Instance(...,
  user_data_causes_replacement=False,
  user_data=user_data
)
```

### 権限エラー（Permission Errors）

#### IAM Role権限不足

**症状**:
```
AccessDenied: User: arn:aws:iam::account:user/username is not authorized to perform: ec2:DescribeImages
```

**原因**: 
- 必要なIAMポリシーが不足している

**解決方法**:

1. **必要なポリシーの確認**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeImages",
                "ec2:DescribeKeyPairs",
                "ec2:CreateTags",
                "ec2:DescribeInstances",
                "ssm:GetParameter",
                "ssm:GetParameters"
            ],
            "Resource": "*"
        }
    ]
}
```

2. **現在の権限確認**:
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::account:user/username \
  --action-names ec2:DescribeImages
```

3. **管理者による権限付与**:
```bash
aws iam attach-user-policy \
  --user-name username \
  --policy-arn arn:aws:iam::aws:policy/EC2FullAccess
```

## 診断ツール

### 設定診断スクリプト

```python
#!/usr/bin/env python3
"""設定診断スクリプト"""

import json
import boto3
from ssm_ec2_rdp.configuration_manager import ConfigurationManager
import aws_cdk as core

def diagnose_configuration():
    """設定の診断を実行"""
    
    # cdk.jsonの読み込み
    try:
        with open('cdk.json', 'r') as f:
            config = json.load(f)
        print("✓ cdk.json の読み込み成功")
    except Exception as e:
        print(f"✗ cdk.json の読み込み失敗: {e}")
        return
    
    # コンテキスト設定の確認
    context = config.get('context', {})
    
    # AMI設定チェック
    ami_id = context.get('ami-id')
    ami_parameter = context.get('ami-parameter')
    
    if not ami_id and not ami_parameter:
        print("✗ AMI設定が不足しています")
        return
    elif ami_id and ami_parameter:
        print("✗ AMI設定が競合しています")
        return
    else:
        print("✓ AMI設定は適切です")
    
    # インスタンスタイプチェック
    instance_type = context.get('instance-type')
    if not instance_type:
        print("✗ instance-type が指定されていません")
        return
    else:
        print(f"✓ インスタンスタイプ: {instance_type}")
    
    # ConfigurationManager テスト
    try:
        app = core.App()
        for key, value in context.items():
            app.node.set_context(key, value)
        
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        print("✓ ConfigurationManager の実行成功")
        
        # 設定内容の表示
        print(f"  AMI ID: {config.ami.ami_id}")
        print(f"  AMI Parameter: {config.ami.ami_parameter}")
        print(f"  Instance Type: {config.instance.instance_type}")
        print(f"  Key Pair: {config.instance.key_pair_name}")
        
    except Exception as e:
        print(f"✗ ConfigurationManager の実行失敗: {e}")
        return

if __name__ == "__main__":
    diagnose_configuration()
```

### AWS リソース確認スクリプト

```bash
#!/bin/bash
# aws-resource-check.sh

echo "=== AWS リソース確認 ==="

# 現在のリージョン確認
echo "リージョン: $(aws configure get region)"

# AMI確認
if [ ! -z "$1" ]; then
  echo "AMI確認: $1"
  aws ec2 describe-images --image-ids $1 --query 'Images[0].[ImageId,Name,State]' --output table
fi

# Key Pair確認
if [ ! -z "$2" ]; then
  echo "Key Pair確認: $2"
  aws ec2 describe-key-pairs --key-names $2 --query 'KeyPairs[0].[KeyName,KeyFingerprint]' --output table
fi

# VPCエンドポイント確認
echo "VPCエンドポイント:"
aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[?ServiceName==`com.amazonaws.region.ssm`].[ServiceName,State]' --output table

# IAM権限確認
echo "IAM権限確認:"
aws sts get-caller-identity
```

### ログ分析

```bash
# CloudFormationスタックイベント確認
aws cloudformation describe-stack-events --stack-name SsmEc2RdpDynamicStack

# EC2インスタンス起動ログ確認
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,StateReason.Message]' --output table

# SSM接続状態確認
aws ssm describe-instance-information --query 'InstanceInformationList[*].[InstanceId,PingStatus,LastPingDateTime]' --output table
```

## 予防措置

### 設定検証の自動化

```python
# pre-deploy-check.py
def pre_deploy_validation():
    """デプロイ前の検証"""
    checks = [
        validate_cdk_json,
        validate_aws_credentials,
        validate_ami_availability,
        validate_instance_type,
        validate_key_pair
    ]
    
    for check in checks:
        if not check():
            print(f"検証失敗: {check.__name__}")
            return False
    
    return True
```

### 監視設定

```json
{
  "CloudWatchAlarms": [
    {
      "AlarmName": "EC2-InstanceStatus-Check",
      "MetricName": "StatusCheckFailed",
      "Namespace": "AWS/EC2"
    },
    {
      "AlarmName": "SSM-ConnectionLost",
      "MetricName": "ConnectionLost",
      "Namespace": "AWS/SSM-RunCommand"
    }
  ]
}
```

このトラブルシューティングガイドを活用することで、問題の早期発見と迅速な解決が可能になります。