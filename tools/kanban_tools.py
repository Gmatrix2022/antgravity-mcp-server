import os
import sqlite3
import time
import uuid
import json
from typing import Optional, List, Dict, Any

DB_PATH = r"D:\Obsidian\sync\kanban.db"
TIMEOUT = 30.0

def _get_connection() -> sqlite3.Connection:
    """Returns a sqlite3 connection with standard row factory and high timeout for concurrency."""
    conn = sqlite3.connect(DB_PATH, timeout=TIMEOUT)
    conn.row_factory = sqlite3.Row
    return conn

async def ag_kanban_create(
    title: str,
    body: str,
    assignee: str = "antgravity",
    parents: Optional[List[str]] = None,
    priority: int = 0
) -> str:
    """
    Creates a new task card on the shared Kanban board.
    
    Inserts into the 'tasks' table and sets up parent-child dependencies in 'task_links'.
    """
    conn = None
    try:
        task_id = str(uuid.uuid4())
        created_at = int(time.time())
        parents_list = parents if parents is not None else []
        
        conn = _get_connection()
        # Use BEGIN IMMEDIATE to lock the database for write operations
        conn.execute("BEGIN IMMEDIATE")
        
        # Insert main task card
        conn.execute(
            """
            INSERT INTO tasks (
                id, title, body, assignee, status, priority, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, title, body, assignee, "pending", priority, "antgravity", created_at)
        )
        
        # Insert parent-child dependency links
        for parent_id in parents_list:
            conn.execute(
                "INSERT INTO task_links (parent_id, child_id) VALUES (?, ?)",
                (parent_id, task_id)
            )
            
        conn.commit()
        return json.dumps({"ok": True, "task_id": task_id}, ensure_ascii=False)
        
    except Exception as e:
        if conn:
            conn.rollback()
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()

async def ag_kanban_update(
    task_id: str,
    status: Optional[str] = None,
    result: Optional[str] = None
) -> str:
    """
    Updates the status or results column of a specific task card.
    """
    conn = None
    try:
        conn = _get_connection()
        conn.execute("BEGIN IMMEDIATE")
        
        # Check if task exists
        row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            conn.rollback()
            return json.dumps({"ok": False, "error": f"Task {task_id} not found"}, ensure_ascii=False)
            
        fields = []
        params = []
        if status is not None:
            fields.append("status = ?")
            params.append(status)
            if status == "running":
                fields.append("started_at = ?")
                params.append(int(time.time()))
                
        if result is not None:
            fields.append("result = ?")
            params.append(result)
            
        if not fields:
            conn.rollback()
            return json.dumps({"ok": True, "message": "No changes made"}, ensure_ascii=False)
            
        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, tuple(params))
        
        conn.commit()
        return json.dumps({"ok": True, "task_id": task_id}, ensure_ascii=False)
        
    except Exception as e:
        if conn:
            conn.rollback()
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()

async def ag_kanban_comment(
    task_id: str,
    body: str,
    author: str = "antgravity"
) -> str:
    """
    Appends a discussion comment to a task's activity log.
    """
    conn = None
    try:
        comment_id = str(uuid.uuid4())
        created_at = int(time.time())
        
        conn = _get_connection()
        conn.execute("BEGIN IMMEDIATE")
        
        # Verify task exists
        row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            conn.rollback()
            return json.dumps({"ok": False, "error": f"Task {task_id} not found"}, ensure_ascii=False)
            
        conn.execute(
            "INSERT INTO task_comments (id, task_id, author, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (comment_id, task_id, author, body, created_at)
        )
        
        conn.commit()
        return json.dumps({"ok": True, "comment_id": comment_id}, ensure_ascii=False)
        
    except Exception as e:
        if conn:
            conn.rollback()
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()

async def ag_kanban_complete(
    task_id: str,
    summary: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Closes a task card, marks status to 'completed', registers epoch completion timestamp,
    and appends a formal completion log comment.
    """
    conn = None
    try:
        completed_at = int(time.time())
        meta_dict = metadata if metadata is not None else {}
        
        result_payload = {
            "summary": summary,
            "metadata": meta_dict,
            "completed_at": completed_at
        }
        result_str = json.dumps(result_payload, ensure_ascii=False)
        
        conn = _get_connection()
        conn.execute("BEGIN IMMEDIATE")
        
        # Verify task exists
        row = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            conn.rollback()
            return json.dumps({"ok": False, "error": f"Task {task_id} not found"}, ensure_ascii=False)
            
        # Update tasks columns
        conn.execute(
            "UPDATE tasks SET status = ?, completed_at = ?, result = ? WHERE id = ?",
            ("completed", completed_at, result_str, task_id)
        )
        
        # Append closure comment
        comment_id = str(uuid.uuid4())
        comment_body = f"【任务完成归档】\n成果摘要：{summary}\n元数据快照：{json.dumps(meta_dict, ensure_ascii=False)}"
        conn.execute(
            "INSERT INTO task_comments (id, task_id, author, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (comment_id, task_id, "antgravity", comment_body, completed_at)
        )
        
        conn.commit()
        return json.dumps({"ok": True, "task_id": task_id}, ensure_ascii=False)
        
    except Exception as e:
        if conn:
            conn.rollback()
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()

async def ag_kanban_list(
    assignee: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    Lists task cards with optional status and assignee filtering.
    """
    conn = None
    try:
        conn = _get_connection()
        
        query = "SELECT * FROM tasks"
        params = []
        conditions = []
        
        if assignee is not None:
            conditions.append("assignee = ?")
            params.append(assignee)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
            
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
            
        query += " ORDER BY priority DESC, created_at ASC"
        
        cursor = conn.execute(query, tuple(params))
        tasks = [dict(row) for row in cursor.fetchall()]
        
        # Fetch relationships to return parent/child lists
        links_cursor = conn.execute("SELECT parent_id, child_id FROM task_links")
        links = links_cursor.fetchall()
        
        children_map = {}
        parent_map = {}
        for pid, cid in links:
            children_map.setdefault(pid, []).append(cid)
            parent_map.setdefault(cid, []).append(pid)
            
        for t in tasks:
            tid = t["id"]
            t["children"] = children_map.get(tid, [])
            t["parents"] = parent_map.get(tid, [])
            
        return json.dumps(tasks, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()

async def ag_kanban_get(task_id: str) -> str:
    """
    Retrieves complete details of a specific task card, including its full discussion history
    and dependency graphs.
    """
    conn = None
    try:
        conn = _get_connection()
        
        # Fetch main task
        task_row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task_row:
            return json.dumps({"ok": False, "error": f"Task {task_id} not found"}, ensure_ascii=False)
            
        task = dict(task_row)
        
        # Fetch parents & children links
        parents_rows = conn.execute("SELECT parent_id FROM task_links WHERE child_id = ?", (task_id,)).fetchall()
        children_rows = conn.execute("SELECT child_id FROM task_links WHERE parent_id = ?", (task_id,)).fetchall()
        
        task["parents"] = [r["parent_id"] for r in parents_rows]
        task["children"] = [r["child_id"] for r in children_rows]
        
        # Fetch discussion comments
        comments_rows = conn.execute(
            "SELECT author, body, created_at FROM task_comments WHERE task_id = ? ORDER BY created_at ASC",
            (task_id,)
        )
        task["comments"] = [dict(r) for r in comments_rows.fetchall()]
        
        return json.dumps({"ok": True, "task": task}, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()
