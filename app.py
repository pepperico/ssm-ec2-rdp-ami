#!/usr/bin/env python3
import os
import sys

import aws_cdk as cdk

from ssm_ec2_rdp.ssm_ec2_rdp_stack import SsmEc2RdpStack
from ssm_ec2_rdp.configuration_manager import ConfigurationManager
from ssm_ec2_rdp.types import ConfigurationError


def main():
    app = cdk.App()
    
    try:
        # ConfigurationManagerを使用して設定を取得
        config_manager = ConfigurationManager(app)
        config = config_manager.get_configuration()
        
        # 設定情報を表示（デバッグ用）
        print(f"AMI設定: {config.ami}")
        print(f"インスタンス設定: {config.instance}")
        
        SsmEc2RdpStack(app, "SsmEc2RdpDynamicStack-Takasato", config,
            # If you don't specify 'env', this stack will be environment-agnostic.
            # Account/Region-dependent features and context lookups will not work,
            # but a single synthesized template can be deployed anywhere.

            # Uncomment the next line to specialize this stack for the AWS Account
            # and Region that are implied by the current CLI configuration.

            #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

            # Uncomment the next line if you know exactly what Account and Region you
            # want to deploy the stack to. */

            #env=cdk.Environment(account='123456789012', region='us-east-1'),

            # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
        )

        app.synth()
        
    except ConfigurationError as e:
        print(f"\n❌ 設定エラー: {str(e)}", file=sys.stderr)
        print("\n📋 cdk.jsonの設定例:", file=sys.stderr)
        print_configuration_help()
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {str(e)}", file=sys.stderr)
        print("詳細なエラー情報については、スタックトレースを確認してください。")
        sys.exit(1)


def print_configuration_help():
    """設定ヘルプメッセージを表示"""
    help_message = """
{
  "context": {
    // 必須: AMI設定（以下のいずれか一つを指定）
    "ami-id": "ami-0123456789abcdef0",          // 直接AMI IDを指定
    // または
    "ami-parameter": "/aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base",

    // 必須: インスタンスタイプ
    "instance-type": "t3.medium",

    // オプション: サブネットタイプ（デフォルト: "private"）
    "subnet-type": "private",  // "private" または "public"

    // オプション: Key Pair名（SSM Session Manager使用時は不要）
    "key-pair-name": "my-key-pair"
  }
}

📖 設定の詳細:
• AMI設定: 直接AMI IDを指定するか、SSMパラメータパスを使用
• インスタンスタイプ: EC2インスタンスタイプ（例: t3.medium, m5.large, c5.xlarge）
• サブネットタイプ: "private"（プライベートサブネット）または "public"（パブリックサブネット）
  - private: VPCエンドポイント経由でSSM接続のみ（デフォルト）
  - public: パブリックIP自動割り当て、直接SSH/RDP接続可能
• Key Pair: オプション、未指定の場合はSSM Session Managerでアクセス

🔗 利用可能なAWS公式AMIパラメータ:
• Windows Server 2022 日本語: /aws/service/ami-windows-latest/Windows_Server-2022-Japanese-Full-Base
• Windows Server 2022 英語: /aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base
• Amazon Linux 2023: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64
"""
    print(help_message, file=sys.stderr)


if __name__ == "__main__":
    main()
