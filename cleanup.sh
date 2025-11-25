#!/bin/bash

# SSM-EC2-RDP 環境クリーンアップスクリプト
# リソース削除とオプションで仮想環境も削除

set -e  # エラー時に停止

echo "============================================================="
echo "  SSM-EC2-RDP 環境クリーンアップスクリプト"
echo "============================================================="

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

# スクリプトが実行されているディレクトリの確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="ssm-ec2-rdp-dynamic"
STACK_NAME="SsmEc2RdpDynamicStack-Takasato"

print_info "プロジェクトディレクトリ: $SCRIPT_DIR"
print_info "プロジェクト名: $PROJECT_NAME"
print_info "スタック名: $STACK_NAME"

# 仮想環境をアクティベート（存在する場合）
if [ -d ".venv" ]; then
    print_info "仮想環境をアクティベートしています..."
    source .venv/bin/activate
else
    print_warning "仮想環境が見つかりません。グローバル環境でCDKを実行します。"
fi

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
            print_info "手動でAWS認証を設定してください。"
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

# リージョン確認
REGION=$(aws configure get region)
if [ -z "$REGION" ]; then
    REGION="ap-northeast-1"
    print_warning "AWSリージョンが設定されていません。デフォルトでap-northeast-1を使用します。"
else
    print_info "使用するAWSリージョン: $REGION"
fi

# スタックの存在確認
print_info "スタックの存在を確認しています..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION > /dev/null 2>&1; then
    print_success "$STACK_NAME が見つかりました。"
    
    # スタック情報の表示
    print_info "削除対象のスタック情報:"
    aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].[StackName,StackStatus,CreationTime]' --output table
    
    # スタック内リソースの一覧表示
    print_info "削除されるリソース:"
    aws cloudformation describe-stack-resources --stack-name $STACK_NAME --region $REGION --query 'StackResources[*].[ResourceType,LogicalResourceId,ResourceStatus]' --output table
    
    echo ""
    print_warning "========== 重要：削除に関する警告 =========="
    print_warning "この操作により以下のリソースが削除されます："
    print_warning "• Windows Server EC2インスタンス"
    print_warning "• EBSボリューム"
    print_warning "• VPC/サブネット/セキュリティグループ"
    print_warning "• IAMロール・ポリシー"
    print_warning "• Systems Manager関連リソース"
    print_warning ""
    print_warning "削除されたリソースは復旧できません！"
    print_warning "========================================="
    
    # 削除前の最終確認
    echo ""
    print_error "本当にすべてのリソースを削除しますか？"
    print_info "削除を実行するには 'DELETE' と入力してください:"
    read -r confirmation
    
    if [ "$confirmation" = "DELETE" ]; then
        print_info "スタックの削除を開始しています..."
        
        # CDKでスタックを削除
        print_info "CDKスタックを削除しています..."
        if cdk destroy --profile cm --force; then
            print_success "============================================"
            print_success "  スタックの削除が正常に完了しました！"
            print_success "============================================"
            
            # 削除確認
            print_info "削除の確認を行っています..."
            sleep 10
            
            if ! aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION > /dev/null 2>&1; then
                print_success "スタックが正常に削除されました。"
            else
                print_warning "スタックの削除が進行中です。AWSコンソールで進行状況を確認してください。"
            fi
            
            # クリーンアップ完了情報
            echo ""
            print_info "=== クリーンアップ完了情報 ==="
            print_success "主要リソースの削除が完了しました。"
            print_info ""
            print_info "念のため、以下を手動で確認することをお勧めします："
            print_info "1. AWSコンソール > CloudFormation でスタックが削除されているか確認"
            print_info "2. AWSコンソール > EC2 でインスタンスが削除されているか確認"
            print_info "3. AWSコンソール > VPC で関連VPCリソースが削除されているか確認"
            print_info ""
            print_info "削除確認用コマンド:"
            print_info "  aws cloudformation list-stacks --stack-status-filter DELETE_COMPLETE --query 'StackSummaries[?StackName==\`$STACK_NAME\`]'"
            
        else
            print_error "スタックの削除に失敗しました。"
            print_info "エラーの詳細:"
            print_info "1. 依存関係のあるリソースが存在する可能性があります"
            print_info "2. 削除保護が有効になっている可能性があります" 
            print_info "3. 権限不足の可能性があります"
            print_info ""
            print_info "手動での削除が必要な場合があります："
            print_info "1. AWSコンソール > CloudFormation からスタックを削除"
            print_info "2. EC2インスタンスを個別に削除"
            print_info "3. 残存リソースを個別に削除"
            exit 1
        fi
        
    else
        print_info "削除がキャンセルされました。"
        print_info "スタックは保持されます。"
        exit 0
    fi
    
else
    print_warning "$STACK_NAME が見つかりません。"
    print_info "削除するリソースがありません。"
fi

# ローカルファイルのクリーンアップ（オプション）
echo ""
print_info "ローカルファイルのクリーンアップを行いますか？"
print_info "以下のファイル/ディレクトリが削除されます："
print_info "• cdk.out/ (CDK生成ファイル)"
print_info "• .venv/ (Python仮想環境)"
print_info "• __pycache__/ (Pythonキャッシュ)"
print_info "(y/n)"
read -r answer

if [ "$answer" = "y" ]; then
    print_info "ローカルファイルをクリーンアップしています..."
    
    # CDK出力ディレクトリの削除
    if [ -d "cdk.out" ]; then
        rm -rf cdk.out
        print_success "cdk.out/ を削除しました。"
    fi
    
    # Python仮想環境の削除
    if [ -d ".venv" ]; then
        rm -rf .venv
        print_success ".venv/ を削除しました。"
    fi
    
    # Pythonキャッシュの削除
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Pythonキャッシュファイルを削除しました。"
    
    print_success "ローカルファイルのクリーンアップが完了しました。"
else
    print_info "ローカルファイルは保持されます。"
fi

echo ""
print_info "============================================================="
print_info "  SSM-EC2-RDP 環境クリーンアップスクリプト完了"
print_info "============================================================="
print_success "すべてのリソースが正常に削除されました。"
print_info "AWS料金の発生を停止しました。"