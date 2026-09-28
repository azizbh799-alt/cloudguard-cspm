from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import *
class AuthRegister(BaseModel): email: EmailStr; password: str=Field(min_length=8); full_name: str=Field(min_length=2,max_length=255)
class AuthLogin(BaseModel): email: EmailStr; password: str
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; email:str; full_name:str; role:str
class Token(BaseModel): access_token:str; token_type:str="bearer"; user:UserOut
class AccountCreate(BaseModel): account_name:str; aws_account_id:str=Field(pattern=r"^\d{12}$"); region:str
class AccountOut(AccountCreate): model_config=ConfigDict(from_attributes=True); id:int; user_id:int; status:str; created_at:datetime; last_scan_at:datetime|None=None
class FindingUpdate(BaseModel): status: FindingStatus|None=None
class RuleUpdate(BaseModel): enabled: bool
class ScanCreate(BaseModel): aws_account_id:int
class ConnectionOut(BaseModel): connected: bool; account_id: str; region: str
class ScanSummary(BaseModel): scan_id: int; security_score: int; critical: int; high: int; medium: int; low: int; resources_scanned: int; findings_created: int; status: str
class RemediationCreate(BaseModel): finding_id:int; notes:str|None=None
class RemediationUpdate(BaseModel): status: RemediationStatus; notes:str|None=None
class ReportCreate(BaseModel): aws_account_id:int; title:str= "Security posture report"
