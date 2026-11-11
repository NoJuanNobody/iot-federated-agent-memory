"""Minimal agent runner: execute a task against a thread's sandboxed files/.

The runner reuses ``DynamicAIGatewayRouter.dispatch_completion`` (OpenRouter)
and performs all workspace I/O through ``thread_fs`` helpers. It does not
add a new model client.

Entry point::

    python -m iot_federated_agent_memory.agent_runner \\
        --peer PEER --thread THREAD_ID --prompt "..."

Tests should pass a mock router so no paid API calls are made. The CLI will
call OpenRouter only when ``OPENROUTER_API_KEY`` is set (the existing router
returns a simulated reply when the key is missing).
"""

from __future__ import annotations

import argparse
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .ai_gateway import DynamicAIGatewayRouter
from .thread_fs import (
    ThreadFsError,
    ThreadQuotaError,
    charge_thread_quota,
    list_files,
    read_file,
    thread_dir,
    thread_exists,
    write_file,
)

SYSTEM_PROMPT = """You are a TinCan Mesh agent runner. You work only with the
current thread's files/ workspace through tools. Reply with a single JSON
object and nothing else, using one of these shapes:
{"tool":"list_files","args":{"subpath":""}}
{"tool":"read_file","args":{"path":"relative/path"}}
{"tool":"write_file","args":{"path":"relative/path","content":"..."}}
{"tool":"finish","args":{"result":"final answer for the user"}}
Do not invent paths outside the thread workspace. After you have enough
information, call finish.
"""


@dataclass
class AgentTask:
    """A single agentic job scoped to one peer thread."""

    task_id: str
    peer_id: str
    thread_id: str
    prompt: str
    status: str = "pending"  # pending | running | completed | failed
    model_alias: str = "gemini-brain"
    max_steps: int = 6
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        peer_id: str,
        thread_id: str,
        prompt: str,
        *,
        model_alias: str = "gemini-brain",
        max_steps: int = 6,
        task_id: Optional[str] = None,
    ) -> "AgentTask":
        return cls(
            task_id=task_id or uuid.uuid4().hex,
            peer_id=peer_id,
            thread_id=thread_id,
            prompt=prompt,
            model_alias=model_alias,
            max_steps=max_steps,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _parse_tool_payload(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"tool": "finish", "args": {"result": content}}
    if isinstance(data, dict) and "tool" in data:
        return data
    return {"tool": "finish", "args": {"result": content}}


class AgentRunner:
    """Run an AgentTask, calling tools against thread_fs between model steps."""

    def __init__(
        self,
        router: Optional[DynamicAIGatewayRouter] = None,
        *,
        root: Optional[Any] = None,
        registry: Optional[Any] = None,
        billing_peer_id: Optional[str] = None,
    ) -> None:
        self.router = router or DynamicAIGatewayRouter()
        self.root = root
        self.registry = registry
        self.billing_peer_id = billing_peer_id

    def workspace_dir(self, task: AgentTask):
        return thread_dir(task.peer_id, task.thread_id, root=self.root) / "files"

    def _tool_list(self, task: AgentTask, args: Dict[str, Any]) -> Any:
        return list_files(
            task.peer_id,
            task.thread_id,
            subpath=str(args.get("subpath") or ""),
            root=self.root,
        )

    def _tool_read(self, task: AgentTask, args: Dict[str, Any]) -> Any:
        path = args.get("path") or args.get("relpath")
        if not path:
            raise ThreadFsError("read_file requires path")
        return {"path": path, "content": read_file(task.peer_id, task.thread_id, path, root=self.root)}

    def _tool_write(self, task: AgentTask, args: Dict[str, Any]) -> Any:
        path = args.get("path") or args.get("relpath")
        if not path:
            raise ThreadFsError("write_file requires path")
        content = args.get("content")
        if content is None:
            raise ThreadFsError("write_file requires content")
        billing_peer = self.billing_peer_id or task.peer_id
        registry = self.registry

        def _bill(plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return charge_thread_quota(registry, billing_peer, plan)

        write_file(
            task.peer_id,
            task.thread_id,
            path,
            content,
            root=self.root,
            billing=_bill if registry is not None else None,
        )
        return {"path": path, "status": "written"}

    def execute_tool(self, task: AgentTask, name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        args = args or {}
        if name == "list_files":
            return self._tool_list(task, args)
        if name == "read_file":
            return self._tool_read(task, args)
        if name == "write_file":
            return self._tool_write(task, args)
        raise ThreadFsError(f"unknown tool: {name}")

    def run(self, task: AgentTask) -> AgentTask:
        """Execute the runner loop until finish, failure, or max_steps."""
        task.status = "running"
        if not thread_exists(task.peer_id, task.thread_id, root=self.root):
            task.status = "failed"
            task.error = "Thread not found"
            return task

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task.prompt},
        ]

        try:
            for step_no in range(1, task.max_steps + 1):
                completion = self.router.dispatch_completion(
                    alias=task.model_alias,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=1024,
                )
                content = (
                    completion.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                parsed = _parse_tool_payload(content)
                tool = str(parsed.get("tool") or "")
                args = parsed.get("args") or {}
                record: Dict[str, Any] = {"step": step_no, "tool": tool, "args": args}
                if tool == "finish":
                    task.result = str((args or {}).get("result") or content)
                    task.status = "completed"
                    record["result"] = task.result
                    task.steps.append(record)
                    return task
                try:
                    output = self.execute_tool(task, tool, args if isinstance(args, dict) else {})
                    record["output"] = output
                except (ThreadFsError, ThreadQuotaError) as exc:
                    record["error"] = str(exc)
                    output = {"error": str(exc)}
                task.steps.append(record)
                messages.append({"role": "assistant", "content": content})
                messages.append(
                    {
                        "role": "user",
                        "content": "Tool result:\n" + json.dumps(output, default=str),
                    }
                )
            task.status = "failed"
            task.error = f"max_steps ({task.max_steps}) exceeded without finish"
            return task
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            return task


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a TinCan agent task against a thread workspace")
    parser.add_argument("--peer", required=True, help="Peer id that owns the thread")
    parser.add_argument("--thread", required=True, help="Server-minted thread id")
    parser.add_argument("--prompt", required=True, help="Task prompt")
    parser.add_argument("--model", default="gemini-brain", help="Router model alias")
    parser.add_argument("--max-steps", type=int, default=6)
    args = parser.parse_args(argv)
    task = AgentTask.create(
        peer_id=args.peer,
        thread_id=args.thread,
        prompt=args.prompt,
        model_alias=args.model,
        max_steps=args.max_steps,
    )
    result = AgentRunner().run(task)
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
