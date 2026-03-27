import json
import os
import uuid
import hashlib
import hmac
import time
import boto3
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'timetracker-prod')
S3_BUCKET = os.environ.get('S3_BUCKET', 'timetracker-files-prod-goutham')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')
REGION = os.environ.get('REGION', 'eu-west-1')
JWT_SECRET = os.environ.get('JWT_SECRET', 'timetracker-secret-2026')

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE)
sns = boto3.client('sns', region_name=REGION)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body, default=str)
    }


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def to_decimal(val):
    """Convert floats/ints to Decimal for DynamoDB."""
    if isinstance(val, float):
        return Decimal(str(val))
    if isinstance(val, int) and not isinstance(val, bool):
        return Decimal(str(val))
    if isinstance(val, dict):
        return {k: to_decimal(v) for k, v in val.items()}
    if isinstance(val, list):
        return [to_decimal(i) for i in val]
    return val


# ---------------------------------------------------------------------------
# JWT helpers (HMAC-SHA256, no external library)
# ---------------------------------------------------------------------------

def base64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def base64url_decode(s: str) -> bytes:
    import base64
    s += '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def create_token(payload: dict) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    payload['exp'] = int(time.time()) + 86400  # 24 h
    segments = [
        base64url_encode(json.dumps(header).encode()),
        base64url_encode(json.dumps(payload, default=str).encode())
    ]
    signing_input = '.'.join(segments).encode()
    signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    segments.append(base64url_encode(signature))
    return '.'.join(segments)


def verify_token(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        signing_input = f'{parts[0]}.{parts[1]}'.encode()
        signature = hmac.new(JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
        if base64url_encode(signature) != parts[2]:
            return None
        payload = json.loads(base64url_decode(parts[1]))
        if payload.get('exp', 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_user_from_event(event):
    """Extract and verify JWT from Authorization header."""
    headers = event.get('headers', {}) or {}
    auth = headers.get('Authorization') or headers.get('authorization') or ''
    if auth.startswith('Bearer '):
        token = auth[7:]
    else:
        token = auth
    if not token:
        return None
    return verify_token(token)


# ---------------------------------------------------------------------------
# Password hashing (PBKDF2 + salt)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> tuple:
    salt = os.urandom(32).hex()
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hashed


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

# ---- Auth ----

def handle_register(body):
    username = body.get('username', '').strip()
    email = body.get('email', '').strip()
    password = body.get('password', '')
    if not username or not email or not password:
        return response(400, {'error': 'username, email and password required'})

    # Check existing user
    result = table.scan(
        FilterExpression=Attr('entityType').eq('user') & (Attr('email').eq(email) | Attr('username').eq(username))
    )
    if result.get('Items'):
        return response(409, {'error': 'User already exists'})

    hashed, salt = hash_password(password)
    user_id = str(uuid.uuid4())
    item = {
        'id': user_id,
        'entityType': 'user',
        'username': username,
        'email': email,
        'password': hashed,
        'salt': salt,
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    table.put_item(Item=to_decimal(item))
    token = create_token({'userId': user_id, 'email': email, 'username': username})
    return response(201, {'token': token, 'userId': user_id, 'username': username})


def handle_login(body):
    email = body.get('email', '').strip()
    password = body.get('password', '')
    if not email or not password:
        return response(400, {'error': 'email and password required'})

    result = table.scan(
        FilterExpression=Attr('entityType').eq('user') & Attr('email').eq(email)
    )
    items = result.get('Items', [])
    if not items:
        return response(401, {'error': 'Invalid credentials'})
    user = items[0]
    if not verify_password(password, user['password'], user['salt']):
        return response(401, {'error': 'Invalid credentials'})
    token = create_token({'userId': user['id'], 'email': user['email'], 'username': user['username']})
    return response(200, {'token': token, 'userId': user['id'], 'username': user['username']})


# ---- Clients ----

def handle_get_clients(user_id):
    result = table.scan(
        FilterExpression=Attr('entityType').eq('client') & Attr('userId').eq(user_id)
    )
    return response(200, result.get('Items', []))


def handle_create_client(user_id, body):
    name = body.get('name', '').strip()
    if not name:
        return response(400, {'error': 'name is required'})
    client_id = str(uuid.uuid4())
    item = {
        'id': client_id,
        'entityType': 'client',
        'userId': user_id,
        'name': name,
        'email': body.get('email', ''),
        'company': body.get('company', ''),
        'phone': body.get('phone', ''),
        'address': body.get('address', ''),
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    table.put_item(Item=to_decimal(item))
    return response(201, item)


def handle_update_client(user_id, client_id, body):
    result = table.get_item(Key={'id': client_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'client':
        return response(404, {'error': 'Client not found'})
    for field in ['name', 'email', 'company', 'phone', 'address']:
        if field in body:
            item[field] = body[field]
    item['updatedAt'] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=to_decimal(item))
    return response(200, item)


def handle_delete_client(user_id, client_id):
    result = table.get_item(Key={'id': client_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'client':
        return response(404, {'error': 'Client not found'})
    table.delete_item(Key={'id': client_id})
    return response(200, {'message': 'Client deleted'})


# ---- Projects ----

def handle_get_projects(user_id):
    result = table.scan(
        FilterExpression=Attr('entityType').eq('project') & Attr('userId').eq(user_id)
    )
    return response(200, result.get('Items', []))


def handle_create_project(user_id, body):
    name = body.get('name', '').strip()
    if not name:
        return response(400, {'error': 'name is required'})
    status = body.get('status', 'active')
    if status not in ('active', 'completed', 'paused'):
        return response(400, {'error': 'status must be active, completed, or paused'})
    project_id = str(uuid.uuid4())
    item = {
        'id': project_id,
        'entityType': 'project',
        'userId': user_id,
        'name': name,
        'description': body.get('description', ''),
        'clientId': body.get('clientId', ''),
        'hourlyRate': body.get('hourlyRate', 0),
        'status': status,
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    table.put_item(Item=to_decimal(item))
    return response(201, item)


def handle_get_project(user_id, project_id):
    result = table.get_item(Key={'id': project_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})
    return response(200, item)


def handle_update_project(user_id, project_id, body):
    result = table.get_item(Key={'id': project_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})
    for field in ['name', 'description', 'clientId', 'hourlyRate', 'status']:
        if field in body:
            item[field] = body[field]
    if 'status' in body and body['status'] not in ('active', 'completed', 'paused'):
        return response(400, {'error': 'status must be active, completed, or paused'})
    item['updatedAt'] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=to_decimal(item))
    return response(200, item)


def handle_delete_project(user_id, project_id):
    result = table.get_item(Key={'id': project_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})
    table.delete_item(Key={'id': project_id})
    return response(200, {'message': 'Project deleted'})


# ---- Time Logs ----

def handle_get_timelogs(user_id, project_id):
    # Verify project ownership
    proj = table.get_item(Key={'id': project_id}).get('Item')
    if not proj or proj.get('userId') != user_id or proj.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})
    result = table.scan(
        FilterExpression=Attr('entityType').eq('timelog') & Attr('projectId').eq(project_id) & Attr('userId').eq(user_id)
    )
    return response(200, result.get('Items', []))


def handle_create_timelog(user_id, project_id, body):
    proj = table.get_item(Key={'id': project_id}).get('Item')
    if not proj or proj.get('userId') != user_id or proj.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})

    start_time = body.get('startTime', '')
    end_time = body.get('endTime', '')
    if not start_time or not end_time:
        return response(400, {'error': 'startTime and endTime are required'})

    # Calculate duration in hours
    try:
        st = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        et = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration_hours = round((et - st).total_seconds() / 3600, 2)
    except Exception:
        return response(400, {'error': 'Invalid date format'})

    log_id = str(uuid.uuid4())
    item = {
        'id': log_id,
        'entityType': 'timelog',
        'userId': user_id,
        'projectId': project_id,
        'description': body.get('description', ''),
        'startTime': start_time,
        'endTime': end_time,
        'duration': duration_hours,
        'billable': body.get('billable', True),
        'createdAt': datetime.now(timezone.utc).isoformat()
    }
    table.put_item(Item=to_decimal(item))
    return response(201, item)


def handle_update_timelog(user_id, log_id, body):
    result = table.get_item(Key={'id': log_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'timelog':
        return response(404, {'error': 'Time log not found'})
    for field in ['description', 'startTime', 'endTime', 'billable']:
        if field in body:
            item[field] = body[field]
    # Recalculate duration if times changed
    if 'startTime' in body or 'endTime' in body:
        try:
            st = datetime.fromisoformat(item['startTime'].replace('Z', '+00:00'))
            et = datetime.fromisoformat(item['endTime'].replace('Z', '+00:00'))
            item['duration'] = round((et - st).total_seconds() / 3600, 2)
        except Exception:
            pass
    item['updatedAt'] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=to_decimal(item))
    return response(200, item)


def handle_delete_timelog(user_id, log_id):
    result = table.get_item(Key={'id': log_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'timelog':
        return response(404, {'error': 'Time log not found'})
    table.delete_item(Key={'id': log_id})
    return response(200, {'message': 'Time log deleted'})


# ---- Timer ----

def handle_timer_start(user_id, body):
    project_id = body.get('projectId', '')
    if not project_id:
        return response(400, {'error': 'projectId is required'})
    proj = table.get_item(Key={'id': project_id}).get('Item')
    if not proj or proj.get('userId') != user_id or proj.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})

    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        'id': log_id,
        'entityType': 'timelog',
        'userId': user_id,
        'projectId': project_id,
        'description': body.get('description', ''),
        'startTime': now,
        'endTime': None,
        'duration': 0,
        'billable': True,
        'running': True,
        'createdAt': now
    }
    table.put_item(Item=to_decimal(item))
    return response(201, item)


def handle_timer_stop(user_id, log_id):
    result = table.get_item(Key={'id': log_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'timelog':
        return response(404, {'error': 'Timer not found'})
    if not item.get('running'):
        return response(400, {'error': 'Timer is not running'})

    now = datetime.now(timezone.utc)
    item['endTime'] = now.isoformat()
    item['running'] = False
    try:
        st = datetime.fromisoformat(item['startTime'].replace('Z', '+00:00'))
        item['duration'] = round((now - st).total_seconds() / 3600, 2)
    except Exception:
        item['duration'] = 0
    item['updatedAt'] = now.isoformat()
    table.put_item(Item=to_decimal(item))
    return response(200, item)


# ---- Invoices ----

def handle_get_invoices(user_id):
    result = table.scan(
        FilterExpression=Attr('entityType').eq('invoice') & Attr('userId').eq(user_id)
    )
    return response(200, result.get('Items', []))


def handle_create_invoice(user_id, project_id):
    proj = table.get_item(Key={'id': project_id}).get('Item')
    if not proj or proj.get('userId') != user_id or proj.get('entityType') != 'project':
        return response(404, {'error': 'Project not found'})

    # Get billable time logs
    logs_result = table.scan(
        FilterExpression=Attr('entityType').eq('timelog') & Attr('projectId').eq(project_id)
            & Attr('userId').eq(user_id) & Attr('billable').eq(True)
    )
    logs = logs_result.get('Items', [])

    hourly_rate = float(proj.get('hourlyRate', 0))
    line_items = []
    total_hours = 0

    for log in logs:
        duration = float(log.get('duration', 0))
        total_hours += duration
        line_items.append({
            'description': log.get('description', ''),
            'hours': duration,
            'rate': hourly_rate,
            'amount': round(duration * hourly_rate, 2)
        })

    subtotal = round(total_hours * hourly_rate, 2)
    tax_rate = 0.1  # 10%
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    invoice_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    invoice = {
        'id': invoice_id,
        'entityType': 'invoice',
        'userId': user_id,
        'projectId': project_id,
        'projectName': proj.get('name', ''),
        'clientId': proj.get('clientId', ''),
        'lineItems': line_items,
        'totalHours': round(total_hours, 2),
        'subtotal': subtotal,
        'taxRate': tax_rate,
        'tax': tax,
        'total': total,
        'status': 'pending',
        'createdAt': now
    }
    table.put_item(Item=to_decimal(invoice))

    # Publish SNS notification
    if SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='New Invoice Generated',
                Message=f'Invoice {invoice_id} generated for project "{proj.get("name", "")}". Total: ${total:.2f}'
            )
        except Exception as e:
            print(f'SNS publish error: {e}')

    return response(201, invoice)


def handle_get_invoice(user_id, invoice_id):
    result = table.get_item(Key={'id': invoice_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'invoice':
        return response(404, {'error': 'Invoice not found'})
    return response(200, item)


def handle_delete_invoice(user_id, invoice_id):
    result = table.get_item(Key={'id': invoice_id})
    item = result.get('Item')
    if not item or item.get('userId') != user_id or item.get('entityType') != 'invoice':
        return response(404, {'error': 'Invoice not found'})
    table.delete_item(Key={'id': invoice_id})
    return response(200, {'message': 'Invoice deleted'})


# ---- Dashboard ----

def handle_dashboard(user_id):
    # Clients
    clients = table.scan(
        FilterExpression=Attr('entityType').eq('client') & Attr('userId').eq(user_id)
    ).get('Items', [])

    # Projects
    projects = table.scan(
        FilterExpression=Attr('entityType').eq('project') & Attr('userId').eq(user_id)
    ).get('Items', [])

    # Time logs
    all_logs = table.scan(
        FilterExpression=Attr('entityType').eq('timelog') & Attr('userId').eq(user_id)
    ).get('Items', [])

    # Hours this week
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    hours_this_week = 0
    for log in all_logs:
        try:
            created = datetime.fromisoformat(log.get('createdAt', '').replace('Z', '+00:00'))
            if created >= week_start:
                hours_this_week += float(log.get('duration', 0))
        except Exception:
            pass

    # Total earnings (from invoices)
    invoices = table.scan(
        FilterExpression=Attr('entityType').eq('invoice') & Attr('userId').eq(user_id)
    ).get('Items', [])
    total_earnings = sum(float(inv.get('total', 0)) for inv in invoices)

    # Active timers
    active_timers = [log for log in all_logs if log.get('running')]

    # Recent time logs (last 5)
    sorted_logs = sorted(all_logs, key=lambda x: x.get('createdAt', ''), reverse=True)
    recent_logs = sorted_logs[:5]

    return response(200, {
        'totalClients': len(clients),
        'totalProjects': len(projects),
        'totalHoursThisWeek': round(hours_this_week, 2),
        'totalEarnings': round(total_earnings, 2),
        'activeTimers': active_timers,
        'recentTimeLogs': recent_logs
    })


# ---- Notifications (PUBLIC) ----

def handle_subscribe(body):
    email = body.get('email', '').strip()
    if not email:
        return response(400, {'error': 'email is required'})
    if not SNS_TOPIC_ARN:
        return response(500, {'error': 'SNS topic not configured'})
    try:
        sns.subscribe(
            TopicArn=SNS_TOPIC_ARN,
            Protocol='email',
            Endpoint=email
        )
        return response(200, {'message': f'Subscription confirmation sent to {email}'})
    except Exception as e:
        return response(500, {'error': str(e)})


def handle_subscribers():
    if not SNS_TOPIC_ARN:
        return response(500, {'error': 'SNS topic not configured'})
    try:
        result = sns.list_subscriptions_by_topic(TopicArn=SNS_TOPIC_ARN)
        subs = result.get('Subscriptions', [])
        confirmed = [s for s in subs if s.get('SubscriptionArn') not in ('PendingConfirmation', 'Deleted')]
        return response(200, {'count': len(confirmed), 'total': len(subs)})
    except Exception as e:
        return response(500, {'error': str(e)})


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_params = event.get('pathParameters') or {}

        # CORS preflight
        if http_method == 'OPTIONS':
            return response(200, {'message': 'OK'})

        # Parse body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except Exception:
                body = {}

        # ---- Public routes (before auth) ----
        if path == '/subscribe' and http_method == 'POST':
            return handle_subscribe(body)
        if path == '/subscribers' and http_method == 'GET':
            return handle_subscribers()

        # ---- Auth routes ----
        if path == '/auth/register' and http_method == 'POST':
            return handle_register(body)
        if path == '/auth/login' and http_method == 'POST':
            return handle_login(body)

        # ---- Protected routes — require JWT ----
        user = get_user_from_event(event)
        if not user:
            return response(401, {'error': 'Unauthorized'})
        user_id = user['userId']

        # -- Clients --
        if path == '/clients' and http_method == 'GET':
            return handle_get_clients(user_id)
        if path == '/clients' and http_method == 'POST':
            return handle_create_client(user_id, body)
        if path.startswith('/clients/') and http_method == 'PUT':
            cid = path.split('/')[2]
            return handle_update_client(user_id, cid, body)
        if path.startswith('/clients/') and http_method == 'DELETE':
            cid = path.split('/')[2]
            return handle_delete_client(user_id, cid)

        # -- Projects --
        if path == '/projects' and http_method == 'GET':
            return handle_get_projects(user_id)
        if path == '/projects' and http_method == 'POST':
            return handle_create_project(user_id, body)

        # -- Invoices (must check before generic /projects/{id} routes) --
        if path == '/invoices' and http_method == 'GET':
            return handle_get_invoices(user_id)
        # /invoices/{id}
        if path.startswith('/invoices/') and http_method == 'GET':
            inv_id = path.split('/')[2]
            return handle_get_invoice(user_id, inv_id)
        if path.startswith('/invoices/') and http_method == 'DELETE':
            inv_id = path.split('/')[2]
            return handle_delete_invoice(user_id, inv_id)

        # -- Timer --
        if path == '/timer/start' and http_method == 'POST':
            return handle_timer_start(user_id, body)
        if path.startswith('/timer/stop/') and http_method == 'POST':
            log_id = path.split('/')[3]
            return handle_timer_stop(user_id, log_id)

        # -- Time logs (standalone) --
        if path.startswith('/timelogs/') and http_method == 'PUT':
            log_id = path.split('/')[2]
            return handle_update_timelog(user_id, log_id, body)
        if path.startswith('/timelogs/') and http_method == 'DELETE':
            log_id = path.split('/')[2]
            return handle_delete_timelog(user_id, log_id)

        # -- Dashboard --
        if path == '/dashboard' and http_method == 'GET':
            return handle_dashboard(user_id)

        # -- Project sub-routes: /projects/{id}/timelogs, /projects/{id}/invoice --
        parts = path.strip('/').split('/')
        if len(parts) == 3 and parts[0] == 'projects':
            pid = parts[1]
            sub = parts[2]
            if sub == 'timelogs' and http_method == 'GET':
                return handle_get_timelogs(user_id, pid)
            if sub == 'timelogs' and http_method == 'POST':
                return handle_create_timelog(user_id, pid, body)
            if sub == 'invoice' and http_method == 'POST':
                return handle_create_invoice(user_id, pid)

        # -- /projects/{id} GET/PUT/DELETE --
        if len(parts) == 2 and parts[0] == 'projects':
            pid = parts[1]
            if http_method == 'GET':
                return handle_get_project(user_id, pid)
            if http_method == 'PUT':
                return handle_update_project(user_id, pid, body)
            if http_method == 'DELETE':
                return handle_delete_project(user_id, pid)

        return response(404, {'error': 'Route not found'})

    except Exception as e:
        print(f'Unhandled error: {e}')
        return response(500, {'error': 'Internal server error', 'message': str(e)})
