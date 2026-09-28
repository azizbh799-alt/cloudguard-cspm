import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

class AWSConnectionError(RuntimeError):
    pass

def session_for(account):
    # Uses the standard boto3 chain: local env/profile, instance role, or Vercel OIDC runtime role.
    return boto3.Session(region_name=account.region)

def client(account, service):
    return session_for(account).client(service, config=Config(retries={"max_attempts": 3, "mode": "standard"}))

def caller_identity(account):
    try:
        return client(account, "sts").get_caller_identity()
    except (BotoCoreError, ClientError) as exc:
        raise AWSConnectionError("Unable to verify AWS credentials or permissions") from exc

def safe_call(fn, default):
    try:
        return fn()
    except (BotoCoreError, ClientError):
        return default

def region(account):
    return account.region

def normalize(value):
    if isinstance(value, dict): return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [normalize(v) for v in value]
    return value

__all__ = ["AWSConnectionError", "client", "caller_identity", "safe_call", "region", "normalize"]
