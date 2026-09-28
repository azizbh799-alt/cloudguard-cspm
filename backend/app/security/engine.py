from dataclasses import dataclass
from app.models import Severity

@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    title: str
    service: str
    severity: Severity
    description: str
    recommendation: str
    resource_id: str
    resource_type: str
    region: str
    evidence: dict

RULES=(
 ("RULE-IAM-001","IAM user without MFA","IAM",Severity.HIGH,"Enable MFA for this IAM user."),
 ("RULE-IAM-002","Overly broad IAM permissions","IAM",Severity.HIGH,"Replace wildcard permissions with least-privilege actions and resources."),
 ("RULE-S3-001","Public S3 bucket","S3",Severity.CRITICAL,"Enable S3 Block Public Access and review bucket policies."),
 ("RULE-S3-002","S3 bucket without encryption","S3",Severity.HIGH,"Enable default server-side encryption."),
 ("RULE-EC2-001","SSH open to the Internet","EC2",Severity.CRITICAL,"Restrict SSH ingress to trusted CIDR ranges."),
 ("RULE-EC2-002","Dangerous port exposed to the Internet","EC2",Severity.HIGH,"Restrict dangerous ports to trusted networks."),
 ("RULE-RDS-001","RDS publicly accessible","RDS",Severity.CRITICAL,"Disable public accessibility and use private subnets."),
 ("RULE-RDS-002","RDS encryption disabled","RDS",Severity.HIGH,"Enable storage encryption for the database."),
 ("RULE-KMS-001","KMS key rotation disabled","KMS",Severity.MEDIUM,"Enable automatic key rotation."),
)

def evaluate(resource):
    m=resource.get("metadata",{}); typ=resource.get("type",""); out=[]
    if typ=="iam_user" and not m.get("mfa_enabled"): out.append(("RULE-IAM-001",{"mfa_enabled":False}))
    if typ=="iam_policy" and (m.get("PolicyName") in ("AdministratorAccess","PowerUserAccess") or m.get("PermissionsBoundary") is None and m.get("DefaultVersionId")): out.append(("RULE-IAM-002",{"policy":m.get("PolicyName")}))
    if typ=="s3_bucket":
        block=m.get("public_access_block",{}); public=not block or not all(block.get(k,False) for k in ("BlockPublicAcls","BlockPublicPolicy","IgnorePublicAcls","RestrictPublicBuckets"))
        if public: out.append(("RULE-S3-001",{"public_access_block":block}))
        if not m.get("encrypted"): out.append(("RULE-S3-002",{"encrypted":False}))
    if typ=="ec2_security_group":
        for p in m.get("IpPermissions",[]):
            if any(r.get("CidrIp")=="0.0.0.0/0" for r in p.get("IpRanges",[])):
                out.append(("RULE-EC2-001",{"from_port":p.get("FromPort"),"to_port":p.get("ToPort")})) if p.get("FromPort")==22 or p.get("ToPort")==22 else out.append(("RULE-EC2-002",{"from_port":p.get("FromPort"),"to_port":p.get("ToPort")}))
    if typ=="rds_instance":
        if m.get("PubliclyAccessible"): out.append(("RULE-RDS-001",{"publicly_accessible":True}))
        if not m.get("StorageEncrypted"): out.append(("RULE-RDS-002",{"storage_encrypted":False}))
    if typ=="kms_key" and not m.get("rotation_enabled"): out.append(("RULE-KMS-001",{"rotation_enabled":False}))
    return out

def run(resources, enabled=None):
    catalog={x[0]:x for x in RULES}; enabled=enabled or set(catalog)
    results=[]
    for resource in resources:
        for rule_id,evidence in evaluate(resource):
            if rule_id not in enabled: continue
            _,title,service,severity,recommendation=catalog[rule_id]
            results.append(RuleResult(rule_id,title,service,severity,f"{title} detected for {resource['name']}",recommendation,resource["id"],resource["type"],resource["region"],evidence))
    return results
