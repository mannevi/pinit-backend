from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

from db.database import get_admin_db
from utils.auth_helpers import get_current_user, log_action
from utils.cloudinary_helper import upload_share_image_base64

router = APIRouter(tags=["Share Links"])

EXPIRY_MAP = {
    "1d":  timedelta(days=1),
    "7d":  timedelta(days=7),
    "30d": timedelta(days=30),
    "none": None,
}

class CreateShareLinkRequest(BaseModel):
    asset_id:          str
    permission:        str
    expires_in:        str
    require_approval:  bool = True
    full_image_base64: Optional[str] = None  # full-res image sent from mobile app

class DownloadRequestBody(BaseModel):
    recipient_name:  str
    recipient_email: str
    reason:          Optional[str] = None

class ApproveRequestBody(BaseModel):
    request_id: str


@router.post("")
async def create_share_link(
    data: CreateShareLinkRequest,
    request: Request,
    current_user=Depends(get_current_user)
):
    db = get_admin_db()
    asset = db.table("vault_images").select("asset_id") \
        .eq("asset_id", data.asset_id).eq("user_id", current_user["id"]).execute()
    if not asset.data:
        raise HTTPException(status_code=404, detail="Asset not found")

    expires_at = None
    delta = EXPIRY_MAP.get(data.expires_in)
    if delta:
        expires_at = (datetime.now(timezone.utc) + delta).isoformat()

    result = db.table("share_links").insert({
        "asset_id":         data.asset_id,
        "owner_id":         current_user["id"],
        "permission":       data.permission,
        "require_approval": data.require_approval,
        "expires_at":       expires_at,
    }).execute()

    link = result.data[0]
    log_action(current_user["id"], "share_link_created",
        {"asset_id": data.asset_id, "token": link["token"]}, str(request.client.host))

    # Upload full-resolution image to Cloudinary if provided
    share_image_url = None
    if data.full_image_base64:
        upload_result = upload_share_image_base64(data.full_image_base64, link["token"])
        if upload_result["success"]:
            share_image_url = upload_result["url"]

    share_url = f"https://pinit-mobile.vercel.app/share/image/{link['token']}"
    return {
        "id": link["id"], "token": link["token"], "url": share_url,
        "permission": link["permission"], "expires_at": link["expires_at"],
        "status": link["status"], "share_image_url": share_image_url,
    }


@router.get("")
async def list_share_links(current_user=Depends(get_current_user)):
    db = get_admin_db()
    result = db.table("share_links") \
        .select("*, download_requests(id, status, recipient_name, recipient_email, created_at)") \
        .eq("owner_id", current_user["id"]).order("created_at", desc=True).execute()
    links = result.data or []
    for link in links:
        link["share_url"] = f"https://pinit-mobile.vercel.app/share/image/{link['token']}"
        link["pending_requests"] = [r for r in (link.get("download_requests") or []) if r["status"] == "pending"]
    return {"links": links}


@router.delete("/{link_id}")
async def revoke_share_link(link_id: str, current_user=Depends(get_current_user)):
    db = get_admin_db()
    result = db.table("share_links").update({"status": "revoked"}) \
        .eq("id", link_id).eq("owner_id", current_user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"success": True}


@router.post("/{link_id}/approve")
async def approve_download_request(link_id: str, data: ApproveRequestBody, current_user=Depends(get_current_user)):
    db = get_admin_db()
    link = db.table("share_links").select("id, download_count") \
        .eq("id", link_id).eq("owner_id", current_user["id"]).execute()
    if not link.data:
        raise HTTPException(status_code=404, detail="Link not found")
    db.table("download_requests").update({
        "status": "approved", "approved_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", data.request_id).execute()
    db.table("share_links").update({
        "download_count": (link.data[0]["download_count"] or 0) + 1
    }).eq("id", link_id).execute()
    return {"success": True}


@router.get("/{link_id}/activity")
async def get_link_activity(link_id: str, current_user=Depends(get_current_user)):
    db = get_admin_db()
    link = db.table("share_links").select("id").eq("id", link_id).eq("owner_id", current_user["id"]).execute()
    if not link.data:
        raise HTTPException(status_code=404, detail="Not found")
    events   = db.table("share_events").select("*").eq("share_link_id", link_id).order("created_at", desc=True).execute()
    requests = db.table("download_requests").select("*").eq("share_link_id", link_id).order("created_at", desc=True).execute()
    return {"events": events.data or [], "requests": requests.data or []}


@router.get("/public/{token}")
async def get_share_link_public(token: str, request: Request):
    db = get_admin_db()
    result = db.table("share_links").select("*").eq("token", token).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Link not found")

    link = result.data[0]

    if link["status"] == "active" and link["expires_at"]:
        expires_at = datetime.fromisoformat(link["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            db.table("share_links").update({"status": "expired"}).eq("id", link["id"]).execute()
            link["status"] = "expired"

    if link["status"] == "active":
        db.table("share_events").insert({
            "share_link_id": link["id"], "event_type": "view",
            "ip_address": str(request.client.host), "user_agent": request.headers.get("user-agent", ""),
        }).execute()
        db.table("share_links").update({"view_count": (link["view_count"] or 0) + 1}).eq("id", link["id"]).execute()

    asset = {}
    if link.get("asset_id"):
        vault_result = db.table("vault_images").select(
            "asset_id, file_name, file_size, resolution, thumbnail_url, owner_name, owner_email, created_at"
        ).eq("asset_id", link["asset_id"]).execute()
        if vault_result.data:
            asset = vault_result.data[0]

    # Build the full-resolution share image URL from Cloudinary using the token
    share_image_url = None


    return {
        "status": link["status"], "permission": link["permission"],
        "require_approval": link["require_approval"], "expires_at": link["expires_at"],
        "asset": {
            "asset_id":       asset.get("asset_id"),
            "file_name":      asset.get("file_name"),
            "file_size":      asset.get("file_size"),
            "resolution":     asset.get("resolution"),
            "thumbnail_url":  asset.get("thumbnail_url"),
            "share_image_url": share_image_url,   # full-res image for display
            "owner_name":     asset.get("owner_name"),
            "registered":     asset.get("created_at"),
        }
    }


@router.post("/public/{token}/request-download")
async def request_download(token: str, data: DownloadRequestBody, request: Request):
    db = get_admin_db()
    link_result = db.table("share_links").select("id, status").eq("token", token).execute()
    if not link_result.data:
        raise HTTPException(status_code=404, detail="Link not found")
    link = link_result.data[0]
    if link["status"] != "active":
        raise HTTPException(status_code=410, detail="Link is no longer active")
    db.table("download_requests").insert({
        "share_link_id": link["id"], "recipient_name": data.recipient_name,
        "recipient_email": data.recipient_email, "reason": data.reason,
    }).execute()
    db.table("share_events").insert({
        "share_link_id": link["id"], "event_type": "request",
        "recipient_email": data.recipient_email, "ip_address": str(request.client.host),
    }).execute()
    return {"success": True, "message": "Request sent to owner for approval"}