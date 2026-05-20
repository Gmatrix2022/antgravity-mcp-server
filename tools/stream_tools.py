import os
import json
import time
import glob
from pathlib import Path
from typing import Literal, Optional, Dict, Any

def _get_next_step_id(steps_dir: Path) -> str:
    """Finds the largest step ID in steps_dir and returns the next ID as a zero-padded string."""
    try:
        files = steps_dir.glob("*.json")
        step_ids = []
        for f in files:
            # Format: <timestamp>-<step_id>-<type>.json
            parts = f.stem.split("-")
            if len(parts) >= 2:
                try:
                    step_ids.append(int(parts[1]))
                except ValueError:
                    continue
        if step_ids:
            return f"{max(step_ids) + 1:03d}"
    except Exception:
        pass
    return "001"

async def ag_record_step(
    type: Literal["thought", "tool_call", "tool_result", "pending_approve", "done", "error"],
    content: str,
    step_id: Optional[str] = None,
    workdir: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Records an agent step (thought, tool call, tool result, pending approval, etc.) to the local status stream.
    
    If <workdir>/.hermes-stream/ does not exist, it will be automatically created.
    """
    try:
        if not workdir:
            workdir = os.getcwd()
            
        base_dir = Path(workdir) / ".hermes-stream"
        steps_dir = base_dir / "steps"
        steps_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure steps directory exists
        if not step_id:
            step_id = _get_next_step_id(steps_dir)
            
        timestamp = int(time.time())
        meta_dict = meta if meta is not None else {}
        
        # Structure the step data
        step_data = {
            "task_id": meta_dict.get("task_id", ""),
            "step_id": step_id,
            "type": type,
            "content": content,
            "timestamp": timestamp,
            "meta": meta_dict,
            "is_pending": (type == "pending_approve")
        }
        
        # 1. Save append-only step file
        step_filename = f"{timestamp}-{step_id}-{type}.json"
        step_file_path = steps_dir / step_filename
        with open(step_file_path, "w", encoding="utf-8") as f:
            json.dump(step_data, f, ensure_ascii=False, indent=2)
            
        # 2. Update current.json
        current_file_path = base_dir / "current.json"
        with open(current_file_path, "w", encoding="utf-8") as f:
            json.dump(step_data, f, ensure_ascii=False, indent=2)
            
        # 3. Periodically update tree.json (mock implementation or simple dump)
        # We can dump a simple non-recursive top-level tree to avoid overhead
        try:
            tree_file = base_dir / "tree.json"
            items = []
            for p in Path(workdir).iterdir():
                if p.name.startswith("."):
                    continue
                items.append({
                    "name": p.name,
                    "type": "dir" if p.is_dir() else "file",
                    "mtime": int(p.stat().st_mtime),
                    "size": p.stat().st_size if p.is_file() else 0
                })
            with open(tree_file, "w", encoding="utf-8") as f:
                json.dump({"path": workdir, "children": items}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
            
        return json.dumps({
            "ok": True,
            "file": str(step_file_path),
            "step_id": step_id,
            "timestamp": timestamp
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)

async def ag_get_current_status(workdir: str) -> str:
    """
    Reads the latest step details from current.json.
    """
    try:
        current_path = Path(workdir) / ".hermes-stream" / "current.json"
        if not current_path.is_file():
            return json.dumps({"status": "no_active_task"}, ensure_ascii=False)
            
        with open(current_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)

async def ag_get_step_history(
    workdir: str,
    limit: int = 50,
    since_ts: Optional[int] = None
) -> str:
    """
    Retrieves chronological step history. Returns the latest limit steps, sorted by timestamp descending.
    """
    try:
        steps_dir = Path(workdir) / ".hermes-stream" / "steps"
        if not steps_dir.is_dir():
            return json.dumps([], ensure_ascii=False)
            
        files = sorted(steps_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        history = []
        
        for f in files:
            if len(history) >= limit:
                break
            try:
                with open(f, "r", encoding="utf-8") as file_handle:
                    step_data = json.load(file_handle)
                if since_ts and step_data.get("timestamp", 0) < since_ts:
                    continue
                history.append(step_data)
            except Exception:
                continue
                
        return json.dumps(history, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

async def ag_accept_action(
    workdir: str,
    action: Literal["approve", "reject", "run", "accept_all"],
    step_id: str,
    comment: Optional[str] = None,
) -> str:
    """
    Writes a user action command JSON file to the actions directory under .hermes-stream/.
    """
    try:
        actions_dir = Path(workdir) / ".hermes-stream" / "actions"
        actions_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        action_data = {
            "action": action,
            "step_id": step_id,
            "comment": comment,
            "timestamp": timestamp
        }
        
        action_filename = f"{timestamp}-{action}.json"
        action_path = actions_dir / action_filename
        with open(action_path, "w", encoding="utf-8") as f:
            json.dump(action_data, f, ensure_ascii=False, indent=2)
            
        return json.dumps({
            "ok": True,
            "file": str(action_path),
            "step_id": step_id,
            "action": action
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
