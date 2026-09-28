from app.aws.client import client, normalize, safe_call

def discover_iam(account):
    iam = client(account, "iam")
    users = safe_call(lambda: iam.list_users().get("Users", []), [])
    roles = safe_call(lambda: iam.list_roles().get("Roles", []), [])
    groups = safe_call(lambda: iam.list_groups().get("Groups", []), [])
    policies = safe_call(lambda: iam.list_policies(Scope="Local").get("Policies", []), [])
    result = []
    for user in users:
        name = user["UserName"]
        mfa = safe_call(lambda: iam.list_mfa_devices(UserName=name).get("MFADevices", []), [])
        result.append({"type":"iam_user", "id":user["Arn"], "name":name, "region":"global", "metadata":{"mfa_enabled":bool(mfa),"arn":user["Arn"]}})
    result += [{"type":"iam_role", "id":x["Arn"], "name":x["RoleName"], "region":"global", "metadata":normalize(x)} for x in roles]
    result += [{"type":"iam_group", "id":x["Arn"], "name":x["GroupName"], "region":"global", "metadata":normalize(x)} for x in groups]
    result += [{"type":"iam_policy", "id":x["Arn"], "name":x["PolicyName"], "region":"global", "metadata":normalize(x)} for x in policies]
    return result

def discover_s3(account):
    s3=client(account,"s3"); result=[]
    for bucket in safe_call(lambda:s3.list_buckets().get("Buckets",[]),[]):
        name=bucket["Name"]
        public=safe_call(lambda:s3.get_public_access_block(Bucket=name),{})
        encryption=safe_call(lambda:s3.get_bucket_encryption(Bucket=name),{})
        region=safe_call(lambda:s3.get_bucket_location(Bucket=name).get("LocationConstraint") or "us-east-1", "unknown")
        result.append({"type":"s3_bucket","id":name,"name":name,"region":region,"metadata":{"public_access_block":normalize(public.get("PublicAccessBlockConfiguration",{})),"encrypted":bool(encryption.get("ServerSideEncryptionConfiguration"))}})
    return result

def discover_ec2(account):
    ec2=client(account,"ec2"); result=[]
    for page in ec2.get_paginator("describe_instances").paginate():
        for res in page.get("Reservations",[]):
            for x in res.get("Instances",[]): result.append({"type":"ec2_instance","id":x["InstanceId"],"name":x["InstanceId"],"region":account.region,"metadata":normalize(x)})
    for page in ec2.get_paginator("describe_security_groups").paginate():
        for x in page.get("SecurityGroups",[]): result.append({"type":"ec2_security_group","id":x["GroupId"],"name":x.get("GroupName",x["GroupId"]),"region":account.region,"metadata":normalize(x)})
    return result

def discover_vpc(account):
    ec2=client(account,"ec2"); result=[]
    for key, typ, id_key, name_key in [("Vpcs","vpc","VpcId","VpcId"),("Subnets","subnet","SubnetId","SubnetId"),("RouteTables","route_table","RouteTableId","RouteTableId"),("InternetGateways","internet_gateway","InternetGatewayId","InternetGatewayId")]:
        method=getattr(ec2,"describe_"+({"Vpcs":"vpcs","Subnets":"subnets","RouteTables":"route_tables","InternetGateways":"internet_gateways"}[key]))
        for x in safe_call(lambda m=method,k=key:m().get(k,[]),[]): result.append({"type":typ,"id":x[id_key],"name":x.get(name_key,x[id_key]),"region":account.region,"metadata":normalize(x)})
    return result

def discover_rds(account):
    rds=client(account,"rds"); return [{"type":"rds_instance","id":x["DBInstanceArn"],"name":x["DBInstanceIdentifier"],"region":account.region,"metadata":normalize(x)} for x in safe_call(lambda:rds.describe_db_instances().get("DBInstances",[]),[])]

def discover_kms(account):
    kms=client(account,"kms"); result=[]
    for x in safe_call(lambda:kms.list_keys().get("Keys",[]),[]):
        key_id=x["KeyId"]; meta=safe_call(lambda:kms.describe_key(KeyId=key_id).get("KeyMetadata",{}),{}); rotation=safe_call(lambda:kms.get_key_rotation_status(KeyId=key_id).get("KeyRotationEnabled",False),False)
        result.append({"type":"kms_key","id":key_id,"name":meta.get("Arn",key_id),"region":account.region,"metadata":{**normalize(meta),"rotation_enabled":rotation}})
    return result

DISCOVERY=(discover_iam,discover_s3,discover_ec2,discover_vpc,discover_rds,discover_kms)
def discover_all(account):
    resources=[]
    for fn in DISCOVERY:
        try: resources.extend(fn(account))
        except Exception: continue
    return resources
