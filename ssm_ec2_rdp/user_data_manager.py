"""
UserData管理クラス
OSタイプに応じてユーザーデータを生成
"""

from typing import Dict, List, Optional
from aws_cdk import aws_ec2 as ec2
from .types import AMIInfo, OSType


class UserDataManager:
    """OSタイプに応じたユーザーデータ生成を担当するクラス"""
    
    def __init__(self):
        """UserDataManagerを初期化"""
        pass
    
    def generate_user_data(self, ami_info: AMIInfo, additional_config: Optional[Dict] = None) -> ec2.UserData:
        """
        AMI情報に基づいてユーザーデータを生成
        
        Args:
            ami_info: AMI情報オブジェクト
            additional_config: 追加設定（オプション）
            
        Returns:
            ec2.UserData: 生成されたユーザーデータ
        """
        if ami_info.is_windows():
            return self._generate_windows_user_data(ami_info, additional_config)
        else:
            # Linux、またはUnknownの場合はLinuxとして処理
            return self._generate_linux_user_data(ami_info, additional_config)
    
    def _generate_windows_user_data(self, ami_info: AMIInfo, additional_config: Optional[Dict] = None) -> ec2.UserData:
        """
        Windows用ユーザーデータを生成
        
        Args:
            ami_info: AMI情報
            additional_config: 追加設定
            
        Returns:
            ec2.UserData: Windows用ユーザーデータ
        """
        user_data = ec2.UserData.for_windows()
        
        # 基本的なWindows設定
        user_data.add_commands(
            "# Windows Server基本設定",
            "",
            "# リモートデスクトップの有効化",
            "Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections' -Value 0",
            "",
            "# Windowsファイアウォールでリモートデスクトップを許可",
            "Enable-NetFirewallRule -DisplayGroup 'Remote Desktop'",
            "",
            "# 管理者アカウントの有効化（必要に応じて）",
            "net user administrator /active:yes",
            "",
            "# セキュリティ設定",
            "# NLA（Network Level Authentication）の有効化",
            "Set-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'UserAuthentication' -Value 1",
            "",
            "# AWS Systems Manager Agent の設定確認",
            "Get-Service AmazonSSMAgent | Restart-Service",
            "",
            "# Windows Update設定",
            "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU' -Name 'NoAutoUpdate' -Value 0",
            "",
            "# ログ記録のセットアップ",
            "Write-Host 'User data setup completed successfully'",
            "Get-Date | Out-File -Append C:\\userdata-completion.log"
        )
        
        # 追加設定の適用
        if additional_config:
            self._apply_windows_additional_config(user_data, additional_config)
        
        return user_data
    
    def _generate_linux_user_data(self, ami_info: AMIInfo, additional_config: Optional[Dict] = None) -> ec2.UserData:
        """
        Linux用ユーザーデータを生成
        
        Args:
            ami_info: AMI情報
            additional_config: 追加設定
            
        Returns:
            ec2.UserData: Linux用ユーザーデータ
        """
        user_data = ec2.UserData.for_linux()
        
        # 基本的なLinux設定
        user_data.add_commands(
            "#!/bin/bash",
            "",
            "# Linux系基本設定",
            "echo 'Starting user data setup...'",
            "",
            "# システムアップデート",
            "if command -v yum &> /dev/null; then",
            "    yum update -y",
            "elif command -v apt-get &> /dev/null; then",
            "    apt-get update && apt-get upgrade -y",
            "fi",
            "",
            "# AWS Systems Manager Agent のインストール・設定",
            "if command -v yum &> /dev/null; then",
            "    # Amazon Linux/RHEL系",
            "    if ! rpm -q amazon-ssm-agent; then",
            "        yum install -y amazon-ssm-agent",
            "    fi",
            "    systemctl enable amazon-ssm-agent",
            "    systemctl start amazon-ssm-agent",
            "elif command -v apt-get &> /dev/null; then",
            "    # Ubuntu/Debian系",
            "    if ! dpkg -l | grep amazon-ssm-agent; then",
            "        wget https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_amd64/amazon-ssm-agent.deb",
            "        dpkg -i amazon-ssm-agent.deb",
            "    fi",
            "    systemctl enable amazon-ssm-agent",
            "    systemctl start amazon-ssm-agent",
            "fi",
            "",
            "# 基本ツールのインストール",
            "if command -v yum &> /dev/null; then",
            "    yum install -y htop curl wget unzip",
            "elif command -v apt-get &> /dev/null; then",
            "    apt-get install -y htop curl wget unzip",
            "fi",
            "",
            "# セキュリティ設定",
            "# SSH設定の最適化",
            "if [ -f /etc/ssh/sshd_config ]; then",
            "    # パスワード認証を無効化（Key Pairまたはクロス認証を推奨）",
            "    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/g' /etc/ssh/sshd_config",
            "    systemctl reload sshd",
            "fi",
            "",
            "# 完了ログの記録",
            "echo 'User data setup completed successfully at $(date)' | tee /tmp/userdata-completion.log",
            "",
            "# 追加のセキュリティ強化（必要に応じて）",
            "# 不要なサービスの停止",
            "# ファイアウォール設定",
            "",
            "echo 'User data execution completed.'"
        )
        
        # 追加設定の適用
        if additional_config:
            self._apply_linux_additional_config(user_data, additional_config)
        
        return user_data
    
    def _apply_windows_additional_config(self, user_data: ec2.UserData, config: Dict) -> None:
        """
        Windows用の追加設定を適用
        
        Args:
            user_data: 既存のUserDataオブジェクト
            config: 追加設定
        """
        # カスタムコマンドの追加
        if 'custom_commands' in config:
            user_data.add_commands("# カスタム設定")
            for command in config['custom_commands']:
                user_data.add_commands(command)
        
        # IIS設定（必要に応じて）
        if config.get('enable_iis', False):
            user_data.add_commands(
                "# IISの有効化",
                "Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole -All"
            )
        
        # 特定ポートの開放
        if 'open_ports' in config:
            user_data.add_commands("# ファイアウォールポート設定")
            for port in config['open_ports']:
                user_data.add_commands(
                    f"New-NetFirewallRule -DisplayName 'Open Port {port}' -Direction Inbound -Protocol TCP -LocalPort {port} -Action Allow"
                )
    
    def _apply_linux_additional_config(self, user_data: ec2.UserData, config: Dict) -> None:
        """
        Linux用の追加設定を適用
        
        Args:
            user_data: 既存のUserDataオブジェクト
            config: 追加設定
        """
        # カスタムコマンドの追加
        if 'custom_commands' in config:
            user_data.add_commands("# カスタム設定")
            for command in config['custom_commands']:
                user_data.add_commands(command)
        
        # Docker設定（必要に応じて）
        if config.get('enable_docker', False):
            user_data.add_commands(
                "# Dockerのインストール",
                "if command -v yum &> /dev/null; then",
                "    yum install -y docker",
                "    systemctl enable docker",
                "    systemctl start docker",
                "elif command -v apt-get &> /dev/null; then",
                "    apt-get install -y docker.io",
                "    systemctl enable docker",
                "    systemctl start docker",
                "fi"
            )
        
        # 特定パッケージのインストール
        if 'install_packages' in config:
            packages = ' '.join(config['install_packages'])
            user_data.add_commands(
                f"# 追加パッケージのインストール",
                f"if command -v yum &> /dev/null; then",
                f"    yum install -y {packages}",
                f"elif command -v apt-get &> /dev/null; then",
                f"    apt-get install -y {packages}",
                f"fi"
            )
    
    def get_default_windows_config(self) -> Dict:
        """
        Windows用のデフォルト設定を取得
        
        Returns:
            Dict: デフォルト設定
        """
        return {
            'enable_rdp': True,
            'enable_nla': True,
            'enable_windows_update': True,
            'enable_ssm': True
        }
    
    def get_default_linux_config(self) -> Dict:
        """
        Linux用のデフォルト設定を取得
        
        Returns:
            Dict: デフォルト設定
        """
        return {
            'update_system': True,
            'install_ssm': True,
            'disable_password_auth': True,
            'install_basic_tools': True
        }
    
    def get_user_data_info(self, ami_info: AMIInfo) -> Dict:
        """
        ユーザーデータの情報を取得
        
        Args:
            ami_info: AMI情報
            
        Returns:
            Dict: ユーザーデータ情報
        """
        if ami_info.is_windows():
            return {
                'os_type': 'Windows',
                'features': [
                    'リモートデスクトップ有効化',
                    'Windows ファイアウォール設定',
                    'SSM Agent 設定',
                    'セキュリティ強化',
                    'ログ記録'
                ],
                'default_ports': [3389],  # RDP
                'recommended_additional_config': {
                    'enable_iis': 'IIS Webサーバーを有効化',
                    'open_ports': '追加ポートの開放',
                    'custom_commands': 'カスタムPowerShellコマンド'
                }
            }
        else:
            return {
                'os_type': 'Linux',
                'features': [
                    'システムアップデート',
                    'SSM Agent インストール・設定',
                    '基本ツールインストール',
                    'SSH セキュリティ強化',
                    'ログ記録'
                ],
                'default_ports': [22],  # SSH
                'recommended_additional_config': {
                    'enable_docker': 'Docker環境のセットアップ',
                    'install_packages': '追加パッケージのインストール',
                    'custom_commands': 'カスタムシェルコマンド'
                }
            }
    
    def validate_additional_config(self, ami_info: AMIInfo, config: Dict) -> List[str]:
        """
        追加設定の妥当性を検証
        
        Args:
            ami_info: AMI情報
            config: 追加設定
            
        Returns:
            List[str]: 検証エラーメッセージのリスト（空の場合は問題なし）
        """
        errors = []
        
        if not isinstance(config, dict):
            errors.append("追加設定は辞書形式である必要があります。")
            return errors
        
        # Windows固有の設定チェック
        if ami_info.is_windows():
            windows_only_keys = ['enable_iis', 'enable_rdp', 'enable_nla']
            for key in config.keys():
                if key.startswith('enable_') and key not in windows_only_keys + ['enable_ssm']:
                    if key in ['enable_docker']:
                        errors.append(f"'{key}' はWindows環境ではサポートされていません。")
        
        # Linux固有の設定チェック
        elif ami_info.is_linux():
            linux_only_keys = ['enable_docker', 'install_packages', 'disable_password_auth']
            for key in config.keys():
                if key.startswith('enable_') and key not in linux_only_keys + ['enable_ssm']:
                    if key in ['enable_iis', 'enable_rdp', 'enable_nla']:
                        errors.append(f"'{key}' はLinux環境ではサポートされていません。")
        
        # 共通設定の検証
        if 'custom_commands' in config:
            if not isinstance(config['custom_commands'], list):
                errors.append("'custom_commands' はリスト形式である必要があります。")
            else:
                for i, command in enumerate(config['custom_commands']):
                    if not isinstance(command, str):
                        errors.append(f"カスタムコマンド{i+1}は文字列である必要があります。")
        
        if 'open_ports' in config:
            if not isinstance(config['open_ports'], list):
                errors.append("'open_ports' はリスト形式である必要があります。")
            else:
                for port in config['open_ports']:
                    if not isinstance(port, int) or port < 1 or port > 65535:
                        errors.append(f"無効なポート番号です: {port}")
        
        if 'install_packages' in config:
            if not isinstance(config['install_packages'], list):
                errors.append("'install_packages' はリスト形式である必要があります。")
            else:
                for package in config['install_packages']:
                    if not isinstance(package, str) or not package.strip():
                        errors.append(f"無効なパッケージ名です: {package}")
        
        return errors
    
    def get_supported_configurations(self, ami_info: AMIInfo) -> Dict:
        """
        サポートされる設定オプションを取得
        
        Args:
            ami_info: AMI情報
            
        Returns:
            Dict: サポートされる設定オプション
        """
        base_config = {
            'custom_commands': {
                'type': 'list[str]',
                'description': 'カスタムコマンドのリスト',
                'example': ['echo "Hello World"']
            }
        }
        
        if ami_info.is_windows():
            base_config.update({
                'enable_iis': {
                    'type': 'bool',
                    'description': 'IIS Webサーバーを有効化',
                    'default': False
                },
                'open_ports': {
                    'type': 'list[int]',
                    'description': 'ファイアウォールで開放するポート',
                    'example': [80, 443, 8080]
                }
            })
        else:
            base_config.update({
                'enable_docker': {
                    'type': 'bool',
                    'description': 'Docker環境をセットアップ',
                    'default': False
                },
                'install_packages': {
                    'type': 'list[str]',
                    'description': 'インストールする追加パッケージ',
                    'example': ['git', 'nodejs', 'python3']
                }
            })
        
        return base_config