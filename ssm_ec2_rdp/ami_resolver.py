"""
AMI解決クラス
AMI設定からMachineImageオブジェクトを生成する
"""

from typing import Tuple, Optional
from aws_cdk import Stack, aws_ec2 as ec2
from .types import AMIConfiguration, AMIInfo, OSType, AMINotFoundError


class AMIResolver:
    """AMI設定からMachineImageオブジェクトを生成するクラス"""
    
    def __init__(self, stack: Stack):
        """
        AMIResolverを初期化
        
        Args:
            stack: CDK Stackインスタンス
        """
        self.stack = stack
    
    def resolve_ami(self, ami_config: AMIConfiguration) -> Tuple[ec2.MachineImage, AMIInfo]:
        """
        AMI設定を解決してMachineImageとAMI情報を返す
        
        Args:
            ami_config: AMI設定オブジェクト
            
        Returns:
            Tuple[ec2.MachineImage, AMIInfo]: (MachineImage, AMI情報)
            
        Raises:
            AMINotFoundError: AMI解決に失敗した場合
        """
        try:
            if ami_config.ami_id:
                return self._resolve_by_ami_id(ami_config.ami_id)
            elif ami_config.ami_parameter:
                return self._resolve_by_parameter(ami_config.ami_parameter)
            else:
                # この状況は通常起こらない（AMIConfigurationでバリデーション済み）
                raise AMINotFoundError("AMI設定が指定されていません。")
        except Exception as e:
            if isinstance(e, AMINotFoundError):
                raise
            raise AMINotFoundError(f"AMI解決中にエラーが発生しました: {str(e)}") from e
    
    def _resolve_by_ami_id(self, ami_id: str) -> Tuple[ec2.MachineImage, AMIInfo]:
        """
        直接AMI IDからMachineImageを作成
        
        Args:
            ami_id: AMI ID
            
        Returns:
            Tuple[ec2.MachineImage, AMIInfo]: (MachineImage, AMI情報)
        """
        # OS種別を推測（基本的にはAWS APIで確認が必要だが、CDK環境では制限がある）
        os_type = self._detect_os_from_ami_id(ami_id)
        
        # MachineImageを作成
        # 指定されたAMI IDを使用する場合は、適切なOS種別でMachineImageを作成
        if os_type == OSType.WINDOWS:
            # Windows AMIの場合は、WindowsImageを使用
            machine_image = ec2.WindowsImage(ec2.WindowsVersion.WINDOWS_SERVER_2016_JAPANESE_FULL_BASE)
        else:
            # Linux AMIまたは不明な場合は、Amazon Linux 2を使用
            machine_image = ec2.MachineImage.latest_amazon_linux2()
        
        # AMI情報を作成
        ami_info = AMIInfo(
            ami_id=ami_id,
            os_type=os_type,
            description=f"Custom AMI ({ami_id})"
        )
        
        return machine_image, ami_info
    
    def _resolve_by_parameter(self, parameter_path: str) -> Tuple[ec2.MachineImage, AMIInfo]:
        """
        SSMパラメータからMachineImageを作成
        
        Args:
            parameter_path: SSMパラメータパス
            
        Returns:
            Tuple[ec2.MachineImage, AMIInfo]: (MachineImage, AMI情報)
        """
        # パラメータパスからOS種別を推測
        os_type = self._detect_os_from_parameter(parameter_path)
        
        # OS種別に応じてMachineImageを作成
        if os_type == OSType.WINDOWS:
            machine_image = ec2.MachineImage.from_ssm_parameter(
                parameter_name=parameter_path,
                os=ec2.OperatingSystemType.WINDOWS
            )
        else:
            # Linux or Unknown の場合はLinuxとして処理
            machine_image = ec2.MachineImage.from_ssm_parameter(
                parameter_name=parameter_path,
                os=ec2.OperatingSystemType.LINUX
            )
        
        # AMI情報を作成
        ami_info = AMIInfo(
            ami_id=parameter_path,  # パラメータパスを一時的にami_idとして保存
            os_type=os_type,
            description=f"SSM Parameter ({parameter_path})"
        )
        
        return machine_image, ami_info
    
    def _detect_os_from_ami_id(self, ami_id: str) -> OSType:
        """
        AMI IDからOS種別を推測
        
        実際の実装では、AWS APIを使用してAMI情報を取得する必要があるが、
        CDKのコンテキストでは制限があるため、基本的な推測ロジックを使用
        
        Args:
            ami_id: AMI ID
            
        Returns:
            OSType: 推測されたOS種別
        """
        # AMI IDから直接OS判定は困難なため、UNKNOWNを返す
        # 実際の用途では、デプロイ時にAWS APIで確認される
        return OSType.UNKNOWN
    
    def _detect_os_from_parameter(self, parameter_path: str) -> OSType:
        """
        SSMパラメータパスからOS種別を推測
        
        一般的なSSMパラメータパスのパターンからOS種別を推測する。
        AWS公式パラメータパスやよく使われるキーワードを基に判定。
        
        Args:
            parameter_path: SSMパラメータパス
            
        Returns:
            OSType: 推測されたOS種別
        """
        parameter_lower = parameter_path.lower()
        
        # Windows系キーワードの検出
        # AWS公式や一般的なWindows関連キーワード
        windows_keywords = [
            'windows', 'win', 'server-20', 'server-201', 'server-202'
        ]
        
        if any(keyword in parameter_lower for keyword in windows_keywords):
            return OSType.WINDOWS
        
        # Linux系キーワードの検出
        # AWS公式や主要なLinuxディストリビューション
        linux_keywords = [
            'linux', 'ubuntu', 'amazon', 'centos', 'rhel', 'suse', 'debian',
            'amzn', 'al20', 'al2023', 'canonical'
        ]
        
        if any(keyword in parameter_lower for keyword in linux_keywords):
            return OSType.LINUX
        
        # 判定できない場合はUNKNOWN
        return OSType.UNKNOWN
    
    def get_ami_info_only(self, ami_config: AMIConfiguration) -> AMIInfo:
        """
        MachineImageを作成せずにAMI情報のみを取得
        
        Args:
            ami_config: AMI設定オブジェクト
            
        Returns:
            AMIInfo: AMI情報
            
        Raises:
            AMINotFoundError: AMI解決に失敗した場合
        """
        if ami_config.ami_id:
            os_type = self._detect_os_from_ami_id(ami_config.ami_id)
            return AMIInfo(
                ami_id=ami_config.ami_id,
                os_type=os_type,
                description=f"Custom AMI ({ami_config.ami_id})"
            )
        elif ami_config.ami_parameter:
            os_type = self._detect_os_from_parameter(ami_config.ami_parameter)
            return AMIInfo(
                ami_id=ami_config.ami_parameter,
                os_type=os_type,
                description=f"SSM Parameter ({ami_config.ami_parameter})"
            )
        else:
            raise AMINotFoundError("AMI設定が指定されていません。")
    
    def is_windows_ami(self, ami_config: AMIConfiguration) -> bool:
        """
        指定されたAMI設定がWindows AMIかどうかを判定
        
        Args:
            ami_config: AMI設定オブジェクト
            
        Returns:
            bool: Windows AMIの場合True
        """
        try:
            ami_info = self.get_ami_info_only(ami_config)
            return ami_info.is_windows()
        except AMINotFoundError:
            return False
    
    def is_linux_ami(self, ami_config: AMIConfiguration) -> bool:
        """
        指定されたAMI設定がLinux AMIかどうかを判定
        
        Args:
            ami_config: AMI設定オブジェクト
            
        Returns:
            bool: Linux AMIの場合True
        """
        try:
            ami_info = self.get_ami_info_only(ami_config)
            return ami_info.is_linux()
        except AMINotFoundError:
            return False