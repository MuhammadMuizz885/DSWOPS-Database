"""
DocFlow SaaS — Auth & Org API R8
New: /api/register (org self-signup), org_id on all tokens,
     username unique per org (not globally)
"""
import hashlib, secrets, re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.database import User, Organization, UploadRecord, AuditLog, SystemSetting

router = APIRouter()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def slugify(name):
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s)
    return s[:60]

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.headers.get("X-Auth-Token") or request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = db.query(User).filter(User.token == token, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user

# ─────────────────────────────────────────────
# REGISTER (org self-signup)
# ─────────────────────────────────────────────
@router.post("/register")
def register(data: dict, db: Session = Depends(get_db)):
    org_name     = data.get("org_name", "").strip()
    custom_slug  = data.get("slug", "").strip()          # ← from frontend
    admin_user   = data.get("admin_username", "").strip() # ← was "username"
    admin_pass   = data.get("admin_password", "")         # ← was "password"
    display_name = data.get("admin_display_name", "").strip() # ← was "display_name"

    if not org_name or not admin_user or not admin_pass:
        raise HTTPException(status_code=400, detail="org_name, admin_username and admin_password required")
    if len(admin_pass) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # use custom slug if provided, else auto-generate
    base_slug = custom_slug if custom_slug else slugify(org_name)
    if not base_slug:
        raise HTTPException(status_code=400, detail="Could not generate a valid office ID")

    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"; counter += 1


    org = Organization(name=org_name, slug=slug, plan="free", is_active=True)
    db.add(org)
    db.flush()

    # username unique within org
    existing = db.query(User).filter(User.org_id == org.id, User.username == admin_user).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        org_id=org.id,
        username=admin_user,
        password_hash=hash_password(admin_pass),
        role="admin",
        display_name=display_name or admin_user,
        token=secrets.token_hex(32),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)

    return {
        "token": user.token,
        "role": user.role,
        "display_name": user.display_name,
        "user_id": user.id,
        "org_id": org.id,
        "org_name": org.name,
        "org_slug": org.slug,
        "plan": org.plan,
    }

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
@router.post("/auth/login")
def login(data: dict, db: Session = Depends(get_db)):
    username = data.get("username", "").strip()
    password = data.get("password", "")
    org_slug = data.get("org_slug", "").strip()   # optional — narrows search

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")

    query = db.query(User).filter(User.username == username, User.is_active == True)
    if org_slug:
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if org:
            query = query.filter(User.org_id == org.id)

    user = query.first()
    if not user or user.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(32)
    user.token = token
    db.commit()

    org = db.query(Organization).filter(Organization.id == user.org_id).first() if user.org_id else None

    return {
        "token": token,
        "role": user.role,
        "display_name": user.display_name or user.username,
        "user_id": user.id,
        "org_id": user.org_id,
        "org_name": org.name if org else "Platform",
        "org_slug": org.slug if org else None,
        "plan": org.plan if org else None,
    }

# ─────────────────────────────────────────────
# LOGOUT / ME
# ─────────────────────────────────────────────
@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.token = None
    db.commit()
    return {"message": "Logged out"}

@router.get("/auth/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first() if current_user.org_id else None
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "display_name": current_user.display_name or current_user.username,
        "org_id": current_user.org_id,
        "org_name": org.name if org else "Platform",
        "org_slug": org.slug if org else None,
        "plan": org.plan if org else None,
    }

# ─────────────────────────────────────────────
# ADMIN — USER MANAGEMENT (org-scoped)
# ─────────────────────────────────────────────
@router.get("/admin/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.org_id == admin.org_id).order_by(User.created_at.desc()).all()
    return [{"id":u.id,"username":u.username,"role":u.role,"display_name":u.display_name,"is_active":u.is_active,"created_at":u.created_at.isoformat() if u.created_at else None} for u in users]

@router.post("/admin/users")
def create_user(data: dict, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    username = data.get("username","").strip()
    password = data.get("password","")
    role     = data.get("role","officer")
    display_name = data.get("display_name","").strip()
    if not username or not password or not role:
        raise HTTPException(status_code=400, detail="username, password and role required")
    existing = db.query(User).filter(User.org_id == admin.org_id, User.username == username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists in this org")
    user = User(org_id=admin.org_id, username=username, password_hash=hash_password(password),
                role=role, display_name=display_name or username, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id":user.id,"username":user.username,"role":user.role}

@router.put("/admin/users/{user_id}")
def edit_user(user_id: int, data: dict, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.org_id == admin.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "display_name" in data: user.display_name = data["display_name"]
    if "role"         in data: user.role = data["role"]
    if "is_active"    in data: user.is_active = bool(data["is_active"])
    if "password"     in data and data["password"]: user.password_hash = hash_password(data["password"])
    db.commit()
    return {"message":"User updated"}

@router.delete("/admin/users/{user_id}")
def delete_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id, User.org_id == admin.org_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message":"User deleted"}

# ─────────────────────────────────────────────
# ADMIN — STATS (org-scoped)
# ─────────────────────────────────────────────
@router.get("/admin/stats")
def admin_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    org_id = admin.org_id
    total     = db.query(UploadRecord).filter(UploadRecord.org_id == org_id).count()
    completed = db.query(UploadRecord).filter(UploadRecord.org_id == org_id, UploadRecord.status=="completed").count()
    failed    = db.query(UploadRecord).filter(UploadRecord.org_id == org_id, UploadRecord.status=="failed").count()
    letters   = db.query(UploadRecord).filter(UploadRecord.org_id == org_id, UploadRecord.document_kind=="letter").count()
    orders    = db.query(UploadRecord).filter(UploadRecord.org_id == org_id, UploadRecord.document_kind=="office_order").count()
    total_users  = db.query(User).filter(User.org_id == org_id).count()
    active_users = db.query(User).filter(User.org_id == org_id, User.is_active==True).count()
    success_rate = round(completed/total*100, 1) if total > 0 else 0
    logs = db.query(AuditLog).filter(AuditLog.org_id == org_id).order_by(AuditLog.timestamp.desc()).limit(20).all()
    return {
        "total":total,"completed":completed,"failed":failed,"letters":letters,
        "office_orders":orders,"success_rate":success_rate,
        "total_users":total_users,"active_users":active_users,
        "recent_activity":[{"action":l.action,"role":l.role,"filename":l.filename,"timestamp":l.timestamp.isoformat() if l.timestamp else None} for l in logs],
    }

# ─────────────────────────────────────────────
# ADMIN — ALL RECORDS (org-scoped)
# ─────────────────────────────────────────────
@router.get("/admin/records")
def admin_all_records(page:int=1, limit:int=25, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    query = db.query(UploadRecord).filter(UploadRecord.org_id == admin.org_id)
    total = query.count()
    records = query.order_by(UploadRecord.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {
        "total":total,"page":page,"pages":max(1,(total+limit-1)//limit),
        "records":[{"id":r.id,"filename":r.original_filename,"document_kind":r.document_kind,
                    "direction":r.direction,"role":r.role,"status":r.status,
                    "created_at":r.created_at.isoformat() if r.created_at else None} for r in records],
    }

# ─────────────────────────────────────────────
# SUPERADMIN — ALL ORGS
# ─────────────────────────────────────────────
@router.get("/superadmin/orgs")
def list_orgs(sa: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    orgs = db.query(Organization).order_by(Organization.created_at.desc()).all()
    return [{"id":o.id,"name":o.name,"slug":o.slug,"plan":o.plan,"is_active":o.is_active,
             "created_at":o.created_at.isoformat() if o.created_at else None,
             "user_count":db.query(User).filter(User.org_id==o.id).count()} for o in orgs]

@router.put("/superadmin/orgs/{org_id}")
def update_org(org_id:int, data:dict, sa: User = Depends(require_superadmin), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org: raise HTTPException(status_code=404, detail="Org not found")
    if "plan"      in data: org.plan = data["plan"]
    if "is_active" in data: org.is_active = bool(data["is_active"])
    db.commit()
    return {"message":"Updated"}

# ─────────────────────────────────────────────
# ROLES METADATA
# ─────────────────────────────────────────────
@router.get("/roles")
def get_roles():
    return {
        "roles": ["admin","manager","officer","viewer"],
        "office_order_roles": ["admin","manager","officer"],
        "letter_roles": ["admin","manager","officer","viewer"],
    }