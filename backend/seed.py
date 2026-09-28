from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import User, AWSAccount, SecurityRule, Resource, Finding, Severity, FindingStatus
Base.metadata.create_all(engine)
db=SessionLocal()
user=db.query(User).filter_by(email="admin@cloudguard.local").first() or User(email="admin@cloudguard.local",password_hash=hash_password("password"),full_name="CloudGuard Admin",role="admin")
db.add(user); db.flush()
account=db.query(AWSAccount).filter_by(aws_account_id="123456789012").first() or AWSAccount(user_id=user.id,account_name="Production AWS",aws_account_id="123456789012",region="eu-west-1")
db.add(account); db.flush()
rules=[("RULE-IAM-001","IAM user without MFA","IAM","HIGH"),("RULE-S3-001","S3 bucket publicly accessible","S3","CRITICAL"),("RULE-S3-002","S3 bucket without encryption","S3","HIGH"),("RULE-EC2-001","SSH exposed to 0.0.0.0/0","EC2","CRITICAL"),("RULE-RDS-001","RDS instance publicly accessible","RDS","CRITICAL"),("RULE-RDS-002","RDS encryption disabled","RDS","HIGH"),("RULE-IAM-002","Excessive IAM permissions","IAM","MEDIUM"),("RULE-KMS-001","Sensitive resource without KMS encryption","KMS","MEDIUM")]
for rid,name,service,severity in rules:
 if not db.query(SecurityRule).filter_by(rule_id=rid).first(): db.add(SecurityRule(rule_id=rid,name=name,description=name,service=service,severity=Severity[severity],recommendation="Review and remediate this configuration."))
db.flush()
for i in range(35): db.add(Resource(aws_account_id=account.id,resource_type="S3" if i%3==0 else "EC2",resource_id=f"resource-{i+1}",name=f"cloudguard-resource-{i+1}",region="eu-west-1"))
db.flush()
for i in range(18): db.add(Finding(aws_account_id=account.id,title="Security configuration requires attention",description="Simulated finding for the demo environment.",severity=[Severity.CRITICAL,Severity.HIGH,Severity.MEDIUM,Severity.LOW][i%4],status=FindingStatus.OPEN,service=["S3","IAM","EC2","RDS"][i%4],resource_id=f"resource-{i+1}",resource_type="AWS resource",region="eu-west-1",recommendation="Review the affected resource and apply the recommended control."))
db.commit(); db.close(); print("Seeded CloudGuard demo data")
