from collections import Counter
from app.models import Severity
WEIGHTS={Severity.CRITICAL:20,Severity.HIGH:10,Severity.MEDIUM:4,Severity.LOW:1}
def calculate(findings):
    counts=Counter(x.severity for x in findings)
    score=max(0,100-sum(counts[s]*w for s,w in WEIGHTS.items()))
    return {"security_score":score,"critical":counts[Severity.CRITICAL],"high":counts[Severity.HIGH],"medium":counts[Severity.MEDIUM],"low":counts[Severity.LOW]}
