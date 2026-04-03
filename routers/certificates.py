from fastapi import APIRouter, HTTPException, Depends
from db.database import get_admin_db
from utils.auth_helpers import get_current_user, log_action

router = APIRouter(tags=["Certificates"])


@router.post("/save")
async def save_certificate(data: dict, current_user=Depends(get_current_user)):
    db = get_admin_db()
    try:
        existing = db.table("certificates") \
            .select("id") \
            .eq("certificate_id", data.get("certificate_id", "")) \
            .execute()

        if existing.data:
            return {"message": "Certificate already exists", "id": existing.data[0]["id"]}

        result = db.table("certificates").insert({
            "user_id"       : current_user["id"],
            "certificate_id": data.get("certificate_id"),
            "asset_id"      : data.get("asset_id"),
            "confidence"    : data.get("confidence"),
            "status"        : data.get("status"),
            "analysis_data" : data.get("analysis_data", {}),
            "image_preview" : data.get("image_preview"),
        }).execute()

        log_action(current_user["id"], "certificate_saved",
                   {"certificate_id": data.get("certificate_id")})
        return {"message": "Certificate saved", "data": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_certificates(current_user=Depends(get_current_user)):
    db = get_admin_db()
    result = db.table("certificates") \
        .select("*") \
        .eq("user_id", current_user["id"]) \
        .order("created_at", desc=True) \
        .execute()
    return {"certificates": result.data or []}


@router.delete("/{certificate_id}")
async def delete_certificate(certificate_id: str, current_user=Depends(get_current_user)):
    db = get_admin_db()
    db.table("certificates") \
        .delete() \
        .eq("certificate_id", certificate_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    return {"message": "Certificate deleted"}


# ── Save shared certificate data (so public link works for anyone) ────────────
@router.post("/share")
async def share_certificate(data: dict, current_user=Depends(get_current_user)):
    db = get_admin_db()
    try:
        certificate_id = data.get("certificateId") or data.get("certificate_id")
        if not certificate_id:
            raise HTTPException(status_code=400, detail="certificateId is required")

        # Check if already shared
        existing = db.table("shared_certificates") \
            .select("id") \
            .eq("certificate_id", certificate_id) \
            .execute()

        if existing.data:
            return {"message": "Already shared", "id": existing.data[0]["id"]}

        result = db.table("shared_certificates").insert({
            "certificate_id"    : certificate_id,
            "asset_id"          : data.get("assetId"),
            "user_id"           : current_user["id"],
            "owner_email"       : data.get("ownerEmail") or current_user.get("email"),
            "confidence"        : data.get("confidence"),
             "status"            : "Verified",
            "date_created"      : data.get("dateCreated"),
            "ownership_data"    : data.get("ownershipAtCreation", {}),
            "technical_details" : data.get("technicalDetails", {}),
            "image_preview"     : data.get("imagePreview"),
        }).execute()

        return {"message": "Certificate shared", "data": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Public endpoint — no login required — for viewing shared certificates ─────
@router.get("/public/{certificate_id}")
async def get_public_certificate(certificate_id: str):
    db = get_admin_db()
    try:
        result = db.table("shared_certificates") \
            .select("*") \
            .eq("certificate_id", certificate_id) \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Certificate not found")

        row = result.data[0]
        return {
            "certificateId"      : row["certificate_id"],
            "assetId"            : row["asset_id"],
            "userId"             : row["user_id"],
            "ownerEmail"         : row["owner_email"],
            "confidence"         : row["confidence"],
            "status"             : row["status"],
            "dateCreated"        : row["date_created"],
            "ownershipAtCreation": row["ownership_data"],
            "technicalDetails"   : row["technical_details"],
            "imagePreview"       : row["image_preview"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))