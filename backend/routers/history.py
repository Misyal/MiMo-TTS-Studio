from fastapi import APIRouter, HTTPException
from backend.database import get_db

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
async def list_history(page: int = 1, size: int = 20, model_type: str = "", search: str = ""):
    db = await get_db()
    try:
        where_clauses = []
        params = []
        if model_type:
            where_clauses.append("model_type = ?")
            params.append(model_type)
        if search:
            where_clauses.append("text_content LIKE ?")
            params.append(f"%{search}%")
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cursor = await db.execute(f"SELECT COUNT(*) as total FROM history{where_sql}", params)
        row = await cursor.fetchone()
        total = row["total"]

        offset = (page - 1) * size
        cursor = await db.execute(
            f"SELECT * FROM history{where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [size, offset],
        )
        rows = await cursor.fetchall()
        records = [dict(r) for r in rows]
        return {"records": records, "total": total, "page": page, "size": size}
    finally:
        await db.close()


@router.get("/history/{record_id}")
async def get_history(record_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM history WHERE id = ?", (record_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="记录不存在")
        return dict(row)
    finally:
        await db.close()


@router.delete("/history/{record_id}")
async def delete_history(record_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM history WHERE id = ?", (record_id,))
        await db.commit()
        return {"message": "删除成功"}
    finally:
        await db.close()


@router.delete("/history")
async def clear_history():
    db = await get_db()
    try:
        await db.execute("DELETE FROM history")
        await db.commit()
        return {"message": "已清空所有历史记录"}
    finally:
        await db.close()


@router.put("/history/{record_id}/favorite")
async def toggle_favorite(record_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT is_favorite FROM history WHERE id = ?", (record_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="记录不存在")
        new_val = 0 if row["is_favorite"] else 1
        await db.execute("UPDATE history SET is_favorite = ? WHERE id = ?", (new_val, record_id))
        await db.commit()
        return {"is_favorite": bool(new_val)}
    finally:
        await db.close()
