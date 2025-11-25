#!/bin/bash

# SSM-EC2-RDP 環境セットアップ・デプロイ自動化スクリプト（動的パラメータ対応版）
# 仮想環境の作成・アクティベートからデプロイまでを一括実行

set -e  # エラー時に停止

# 色付きメッセージのための関数
print_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[0;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# 使用方法の表示
usage() {
    echo "使用方法: $0"
    echo ""
    echo "注意: バージョンやパラメータの変更はcdk.jsonファイルを編集してください"
    echo ""
    echo "例:"
    echo "  $0                                # cdk.jsonの設定に従ってデプロイ"
    exit 0
}

# スクリプトが実行されているディレクトリの確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ssm-ec2-rdp-dynamic"

echo "============================================================="
echo "  SSM-EC2-RDP 自動セットアップ・デプロイスクリプト"
echo "============================================================="

print_info "プロジェクトディレクトリ: $SCRIPT_DIR"
print_info "プロジェクト名: $PROJECT_NAME"
print_info "設定: cdk.jsonで指定されたパラメータを使用"

# 仮想環境の確認とアクティベート
print_info "Python仮想環境を確認しています..."
if [ ! -d ".venv" ]; then
    print_warning "仮想環境が見つかりません。作成しています..."
    python3 -m venv .venv
fi

print_info "仮想環境をアクティベートしています..."
source .venv/bin/activate

# 依存関係のインストール
print_info "Python依存関係をインストールしています..."
pip install --upgrade pip
pip install -r requirements.txt

# AWS認証の確認
print_info "AWS認証を確認しています..."

# cmプロファイルを自動設定
if [ -z "$AWS_PROFILE" ]; then
    export AWS_PROFILE=cm
    print_info "AWSプロファイルを 'cm' に設定しました"
fi

if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS認証が設定されていません。"
    print_info "認証設定スクリプトを実行しますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        if [ -f "/Users/takasato.wataru/script/AutoSetProfile.sh" ]; then
            print_info "認証設定スクリプトを実行しています..."
            /Users/takasato.wataru/script/AutoSetProfile.sh
        else
            print_error "認証設定スクリプトが見つかりません。"
            print_info "手動でAWS認証を設定してください："
            print_info "  aws configure"
            print_info "または"
            print_info "  aws sso login --profile your-profile"
            exit 1
        fi
    else
        print_error "AWS認証を手動で設定してからもう一度実行してください。"
        exit 1
    fi
fi

# AWS認証情報の表示
print_success "AWS認証が確認されました："
aws sts get-caller-identity --query '[Account, UserId, Arn]' --output table

# CDKバージョンの確認
print_info "CDKバージョンを確認しています..."
if ! command -v cdk &> /dev/null; then
    print_error "AWS CDKがインストールされていません。"
    print_info "CDKをインストールしますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        print_info "CDKをインストールしています..."
        npm install -g aws-cdk
    else
        print_error "CDKをインストールしてからもう一度実行してください："
        print_info "  npm install -g aws-cdk"
        exit 1
    fi
fi

print_info "CDKバージョン: $(cdk --version)"

# リージョン確認
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="ap-northeast-1"
    print_warning "AWSリージョンが設定されていません。デフォルトでap-northeast-1を使用します。"
else
    print_info "使用するAWSリージョン: $REGION"
fi

# アカウントID取得
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_info "AWSアカウントID: $ACCOUNT_ID"

# CDKブートストラップの確認
print_info "CDKブートストラップを確認しています..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region $REGION > /dev/null 2>&1; then
    print_warning "CDKブートストラップが必要です。"
    print_info "CDKブートストラップを実行しますか？ (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        print_info "CDKブートストラップを実行しています..."
        cdk bootstrap aws://$ACCOUNT_ID/$REGION --profile cm
        print_success "CDKブートストラップが完了しました。"
    else
        print_error "CDKブートストラップを手動で実行してからもう一度試してください："
        print_info "  cdk bootstrap --profile cm"
        exit 1
    fi
else
    print_success "CDKブートストラップが確認されました。"
fi

# CloudFormationテンプレートの生成
print_info "CloudFormationテンプレートを生成しています..."
cdk synth --profile cm

# コスト警告
print_warning "========== 重要：コストに関する注意 =========="
print_warning "このデプロイには以下のリソースが含まれ、料金が発生します："
print_warning "• Windows Server EC2インスタンス (t3.medium または t3.large)"
print_warning "• EBSボリューム (gp3)"
print_warning "• VPC/サブネット/セキュリティグループ"
print_warning "• Systems Manager セッション"
print_warning ""
print_warning "予想月額コスト: 約 $30-80 USD (インスタンスサイズによる)"
print_warning "=============================================="

# デプロイの実行確認
print_info "cdk.jsonで指定されたパラメータでデプロイしますか？ (y/n)"
read -r answer

if [ "$answer" = "y" ]; then
    print_info "デプロイを開始しています..."
    
    # デプロイ実行
    if cdk deploy --profile cm --require-approval never; then
        print_success "============================================"
        print_success "  デプロイが正常に完了しました！"
        print_success "============================================"
        
        # デプロイメント情報の表示
        print_info "スタック情報を取得しています..."
        
        # スタック出力の表示
        STACK_NAME="SsmEc2RdpDynamicStack-Takasato"
        if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION > /dev/null 2>&1; then
            print_info "スタック出力:"
            aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs' --output table
        fi
        
        # 次のステップの案内
        echo ""
        print_success "=== 次のステップ ==="
        print_info "1. インスタンスIDを確認:"
        print_info "   aws ec2 describe-instances --profile cm --filters \"Name=tag:Name,Values=SsmEc2RdpDynamicStack-Takasato/SsmEc2RdpInstance\" \"Name=instance-state-name,Values=running\" --query 'Reservations[0].Instances[0].InstanceId' --output text"
        print_info ""
        print_info "2. ポートフォワーディング開始:"
        print_info "   aws ssm start-session --profile cm --target <INSTANCE_ID> --document-name AWS-StartPortForwardingSession --parameters '{\"portNumber\":[\"3389\"],\"localPortNumber\":[\"3389\"]}'"
        print_info ""
        print_info "3. リモートデスクトップ接続:"
        print_info "   接続先: localhost:3389"
        print_info "   ユーザー: rdpuser"
        print_info "   パスワード: Password123!"
        print_info ""
        print_info "4. リソースを削除する場合:"
        print_info "   cdk destroy --profile cm"
        print_info ""
        print_warning "注意: 使用完了後は必ずリソースを削除してコストを防止してください"
        
    else
        print_error "デプロイに失敗しました。"
        print_info "エラーの詳細を確認し、問題を解決してから再実行してください。"
        exit 1
    fi
else
    print_info "デプロイがキャンセルされました。"
    print_info "後でデプロイする場合は、以下のコマンドを実行してください："
    print_info "  ./setup_and_deploy.sh"
    exit 0
fi

echo ""
print_info "仮想環境は引き続きアクティブ状態です。"
print_info "非アクティブ化するには 'deactivate' コマンドを実行してください。"

echo ""
print_info "============================================================="
print_info "  SSM-EC2-RDP 自動セットアップ・デプロイスクリプト完了"
print_info "============================================================="