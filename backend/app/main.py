from collections import Counter
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.aws.client import AWSConnectionError, caller_identity
from app.aws.discovery import discover_all
from app.security.engine import RULES, run
from app.security.scoring import calculate
from app.models import *
from app.schemas import *

app=FastAPI(title="CloudGuard CSPM API", version="1.0.0", description="Cloud security posture management API")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/healthz", tags=["Operations"])
def healthz():
    return {"status": "ok", "service": "cloudguard-api"}

@app.get("/readyz", tags=["Operations"])
def readyz(db: Session = Depends(get_db)):
    db.execute(select(func.now()))
    return {"status": "ready"}
@app.on_event("startup")
def startup(): Base.metadata.create_all(bind=engine)
def record(obj): return obj
@app.post("/api/auth/register", response_model=Token, tags=["Authentication"])
def register(payload:AuthRegister, db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==payload.email)): raise HTTPException(409,"Email already registered")
    user=User(email=payload.email,password_hash=hash_password(payload.password),full_name=payload.full_name); db.add(user); db.commit(); db.refresh(user)
    return Token(access_token=create_access_token(str(user.id)),user=user)
@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
def login(payload:AuthLogin, db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==payload.email))
    if not user or not verify_password(payload.password,user.password_hash): raise HTTPException(401,"Invalid email or password")
    return Token(access_token=create_access_token(str(user.id)),user=user)
@app.get("/api/auth/me", response_model=UserOut, tags=["Authentication"])
def me(user=Depends(get_current_user)): return user
@app.get("/api/aws-accounts", response_model=list[AccountOut], tags=["AWS Accounts"])
def accounts(user=Depends(get_current_user),db:Session=Depends(get_db)): return db.scalars(select(AWSAccount).where(AWSAccount.user_id==user.id)).all()
@app.post("/api/aws-accounts", response_model=AccountOut, tags=["AWS Accounts"])
def add_account(p:AccountCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=AWSAccount(user_id=user.id,**p.model_dump()); db.add(x); db.commit(); db.refresh(x); return x
@app.get("/api/aws-accounts/{id}",response_model=AccountOut,tags=["AWS Accounts"])
def account(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.scalar(select(AWSAccount).where(AWSAccount.id==id,AWSAccount.user_id==user.id));
    if not x: raise HTTPException(404,"Account not found")
    return x
@app.delete("/api/aws-accounts/{id}",status_code=204,tags=["AWS Accounts"])
def delete_account(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.scalar(select(AWSAccount).where(AWSAccount.id==id,AWSAccount.user_id==user.id));
    if not x: raise HTTPException(404,"Account not found")
    db.delete(x); db.commit()
@app.get("/api/findings",tags=["Findings"])
def findings(severity:Severity|None=None,status_:FindingStatus|None=Query(None,alias="status"),service:str|None=None,region:str|None=None,aws_account_id:int|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)):
    q=select(Finding).join(AWSAccount).where(AWSAccount.user_id==user.id)
    for col,val in [(Finding.severity,severity),(Finding.status,status_),(Finding.service,service),(Finding.region,region),(Finding.aws_account_id,aws_account_id)]:
        if val is not None:q=q.where(col==val)
    return db.scalars(q.order_by(Finding.detected_at.desc())).all()
@app.get("/api/findings/{id}",tags=["Findings"])
def finding(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.scalar(select(Finding).join(AWSAccount).where(Finding.id==id,AWSAccount.user_id==user.id));
    if not x: raise HTTPException(404,"Finding not found")
    return x
@app.patch("/api/findings/{id}",tags=["Findings"])
def update_finding(id:int,p:FindingUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=finding(id,user,db)
    if p.status:x.status=p.status; x.resolved_at=datetime.now(timezone.utc) if p.status==FindingStatus.RESOLVED else None
    db.commit(); db.refresh(x); return x
@app.get("/api/resources",tags=["Resources"])
def resources(resource_type:str|None=None,region:str|None=None,aws_account_id:int|None=None,user=Depends(get_current_user),db:Session=Depends(get_db)):
    q=select(Resource).join(AWSAccount).where(AWSAccount.user_id==user.id)
    for col,val in [(Resource.resource_type,resource_type),(Resource.region,region),(Resource.aws_account_id,aws_account_id)]:
        if val:q=q.where(col==val)
    return db.scalars(q).all()
@app.get("/api/resources/{id}",tags=["Resources"])
def resource(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.scalar(select(Resource).join(AWSAccount).where(Resource.id==id,AWSAccount.user_id==user.id));
    if not x:raise HTTPException(404,"Resource not found")
    return x
@app.get("/api/rules",tags=["Security Rules"])
def rules(user=Depends(get_current_user),db:Session=Depends(get_db)): return db.scalars(select(SecurityRule)).all()
@app.get("/api/rules/{id}",tags=["Security Rules"])
def rule(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.get(SecurityRule,id)
    if not x:raise HTTPException(404,"Rule not found")
    return x
@app.patch("/api/rules/{id}",tags=["Security Rules"])
def update_rule(id:int,p:RuleUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=rule(id,user,db); x.enabled=p.enabled; db.commit(); db.refresh(x); return x
@app.get("/api/dashboard",tags=["Dashboard"])
def dashboard(user=Depends(get_current_user),db:Session=Depends(get_db)):
    fs=list(db.scalars(select(Finding).join(AWSAccount).where(AWSAccount.user_id==user.id)).all()); rs=list(db.scalars(select(Resource).join(AWSAccount).where(AWSAccount.user_id==user.id)).all()); ss=list(db.scalars(select(Scan).join(AWSAccount).where(AWSAccount.user_id==user.id).order_by(Scan.id.desc()).limit(10)).all()); counts=Counter(x.severity.value for x in fs)
    return {"security_score":max(0,100-len(fs)*2),"critical":counts["CRITICAL"],"high":counts["HIGH"],"medium":counts["MEDIUM"],"low":counts["LOW"],"total_findings":len(fs),"resources":len(rs),"last_scan":ss[0].completed_at if ss else None,"findings_by_severity":dict(counts),"findings_by_service":dict(Counter(x.service for x in fs)),"recent_findings":fs[:5],"recent_scans":ss,"security_score_history":[]}
@app.post("/api/scans",tags=["Scans"])
def create_scan(p:ScanCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    if not db.scalar(select(AWSAccount).where(AWSAccount.id==p.aws_account_id,AWSAccount.user_id==user.id)):raise HTTPException(404,"Account not found")
    x=Scan(aws_account_id=p.aws_account_id,status=ScanStatus.COMPLETED,started_at=datetime.now(timezone.utc),completed_at=datetime.now(timezone.utc),resources_scanned=0,findings_created=0,security_score=100); db.add(x); db.commit(); db.refresh(x); return x
@app.get("/api/scans",tags=["Scans"])
def scans(user=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(Scan).join(AWSAccount).where(AWSAccount.user_id==user.id).order_by(Scan.id.desc())).all()
@app.get("/api/scans/{id}",tags=["Scans"])
def scan(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.scalar(select(Scan).join(AWSAccount).where(Scan.id==id,AWSAccount.user_id==user.id));
    if not x:raise HTTPException(404,"Scan not found")
    return x
@app.get("/api/remediation",tags=["Remediation"])
def remediations(user=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(Remediation).where(Remediation.requested_by==user.id)).all()
@app.post("/api/remediation",tags=["Remediation"])
def add_remediation(p:RemediationCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    finding=db.scalar(select(Finding).join(AWSAccount).where(Finding.id==p.finding_id,AWSAccount.user_id==user.id))
    if not finding: raise HTTPException(404,"Finding not found")
    x=Remediation(**p.model_dump(),requested_by=user.id);db.add(x);db.commit();db.refresh(x);return x
@app.patch("/api/remediation/{id}",tags=["Remediation"])
def update_remediation(id:int,p:RemediationUpdate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.get(Remediation,id)
    if not x or x.requested_by!=user.id:raise HTTPException(404,"Remediation not found")
    for k,v in p.model_dump(exclude_none=True).items():setattr(x,k,v)
    db.commit();db.refresh(x);return x
@app.get("/api/reports",tags=["Reports"])
def reports(user=Depends(get_current_user),db:Session=Depends(get_db)):return db.scalars(select(Report).join(AWSAccount).where(AWSAccount.user_id==user.id).order_by(Report.generated_at.desc())).all()
@app.post("/api/reports",tags=["Reports"])
def add_report(p:ReportCreate,user=Depends(get_current_user),db:Session=Depends(get_db)):
    account=db.scalar(select(AWSAccount).where(AWSAccount.id==p.aws_account_id,AWSAccount.user_id==user.id))
    if not account: raise HTTPException(404,"Account not found")
    x=Report(aws_account_id=account.id,title=p.title,security_score=100);db.add(x);db.commit();db.refresh(x);return x
@app.get("/api/reports/{id}",tags=["Reports"])
def report(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    x=db.scalar(select(Report).join(AWSAccount).where(Report.id==id,AWSAccount.user_id==user.id));
    if not x:raise HTTPException(404,"Report not found")
    return x

@app.post("/api/aws-accounts/{id}/connect", response_model=ConnectionOut, tags=["AWS Accounts"])
def connect(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    account=db.scalar(select(AWSAccount).where(AWSAccount.id==id,AWSAccount.user_id==user.id))
    if not account: raise HTTPException(404,"Account not found")
    try: identity=caller_identity(account)
    except AWSConnectionError as exc: account.status="error"; db.commit(); raise HTTPException(502,str(exc))
    if identity.get("Account") != account.aws_account_id: raise HTTPException(400,"Connected AWS account does not match the configured account ID")
    account.status="connected"; db.commit(); return ConnectionOut(connected=True,account_id=identity["Account"],region=account.region)

@app.post("/api/aws-accounts/{id}/scan", response_model=ScanSummary, tags=["Scans"])
def account_scan(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    account=db.scalar(select(AWSAccount).where(AWSAccount.id==id,AWSAccount.user_id==user.id))
    if not account: raise HTTPException(404,"Account not found")
    try: caller_identity(account)
    except AWSConnectionError as exc: raise HTTPException(502,str(exc))
    now=datetime.now(timezone.utc); scan=Scan(aws_account_id=id,status=ScanStatus.RUNNING,started_at=now); db.add(scan); db.flush(); discovered=discover_all(account)
    for r in discovered:
        existing=db.scalar(select(Resource).where(Resource.aws_account_id==id,Resource.resource_id==r["id"]))
        if existing: existing.name=r["name"]; existing.region=r["region"]; existing.resource_type=r["type"]; existing.metadata_json=r["metadata"]
        else: db.add(Resource(aws_account_id=id,resource_id=r["id"],name=r["name"],region=r["region"],resource_type=r["type"],metadata_json=r["metadata"]))
    enabled={x.rule_id for x in db.scalars(select(SecurityRule).where(SecurityRule.enabled==True)).all()} or {x[0] for x in RULES}; results=run(discovered,enabled); now=datetime.now(timezone.utc)
    for result in results:
        rule=db.scalar(select(SecurityRule).where(SecurityRule.rule_id==result.rule_id)); finding=db.scalar(select(Finding).where(Finding.aws_account_id==id,Finding.resource_id==result.resource_id,Finding.rule_id==rule.id,Finding.status!=FindingStatus.RESOLVED)) if rule else None
        if finding: finding.last_detected=now; finding.evidence=result.evidence; finding.status=FindingStatus.OPEN
        else: db.add(Finding(aws_account_id=id,rule_id=rule.id if rule else None,title=result.title,description=result.description,evidence=result.evidence,severity=result.severity,status=FindingStatus.OPEN,service=result.service,resource_id=result.resource_id,resource_type=result.resource_type,region=result.region,recommendation=result.recommendation,detected_at=now,last_detected=now))
    db.flush(); rows=list(db.scalars(select(Finding).where(Finding.aws_account_id==id,Finding.status==FindingStatus.OPEN)).all()); score=calculate(rows); scan.status=ScanStatus.COMPLETED; scan.completed_at=now; scan.resources_scanned=len(discovered); scan.findings_created=len(results); scan.security_score=score["security_score"]; account.last_scan_at=now; account.status="connected"; db.commit()
    return ScanSummary(scan_id=scan.id,**score,resources_scanned=len(discovered),findings_created=len(results),status=scan.status.value)

@app.get("/api/aws-accounts/{id}/resources", tags=["AWS Accounts"])
def account_resources(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)): return resources(aws_account_id=id,user=user,db=db)
@app.get("/api/aws-accounts/{id}/findings", tags=["AWS Accounts"])
def account_findings(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)): return findings(aws_account_id=id,user=user,db=db)
@app.get("/api/aws-accounts/{id}/security-score", tags=["AWS Accounts"])
def account_score(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    account=db.scalar(select(AWSAccount).where(AWSAccount.id==id,AWSAccount.user_id==user.id))
    if not account: raise HTTPException(404,"Account not found")
    rows=list(db.scalars(select(Finding).where(Finding.aws_account_id==account.id,Finding.status==FindingStatus.OPEN)).all()); return calculate(rows)
@app.get("/api/aws-accounts/{id}/scan-history", tags=["AWS Accounts"])
def account_history(id:int,user=Depends(get_current_user),db:Session=Depends(get_db)): return scans(user=user,db=db)
