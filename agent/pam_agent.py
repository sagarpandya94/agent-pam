"""
pam_agent.py — Claude-powered PAM agent.

Workflow:
  1. Receive a task + target credential_id
  2. Checkout credentials from vault (JIT)
  3. Execute task via SSH tools (policy-enforced)
  4. Scan all output for prompt injection
  5. Checkin credentials when done
  6. Return structured result
"""
import os
import json
import argparse
from dotenv import load_dotenv
load_dotenv()
from typing import Iterator, Optional
from anthropic import Anthropic
import re

from agent.tools.checkout_tool import checkout_credential, CheckoutError, CHECKOUT_TOOL
from agent.tools.ssh_tool import ssh_execute, SSH_TOOL
from agent.tools.checkin_tool import checkin_credential, CheckinError, CHECKIN_TOOL
from agent.guardrails.injection_detector import scan_output, format_injection_warning
from agent.prompts.system_prompt import SYSTEM_PROMPT
from audit.logger import emit

AGENT_ID = os.getenv("AGENT_ID", "pam-agent-001")

client = Anthropic()

# Active session state — set during checkout, cleared on checkin
_session: dict = {}


def _handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call from Claude and return the result as a string."""

    # ── checkout_credential ──────────────────────────────────────────────────
    if tool_name == "checkout_credential":
        try:
            result = checkout_credential(
                credential_id=tool_input["credential_id"],
                task_description=tool_input["task_description"],
            )
            # Store session state for subsequent ssh_execute calls
            _session.update({
                "token": result.token,
                "host": result.host,
                "port": result.port,
                "username": result.username,
                "password": result.password,
                "allowed_commands": result.allowed_commands,
                "expires_at": result.expires_at.isoformat(),
            })
            emit(
                event_type="session_checkout",
                agent_id=AGENT_ID,
                token=result.token,
                detail={
                    "credential_id": result.credential_id,
                    "task": tool_input["task_description"],
                    "allowed_commands": result.allowed_commands,
                    "expires_at": result.expires_at.isoformat(),
                },
            )
            return json.dumps({
                "status": "checked_out",
                "credential_id": result.credential_id,
                "host": result.host,
                "port": result.port,
                "username": result.username,
                "expires_at": result.expires_at.isoformat(),
                "allowed_commands": result.allowed_commands,
            })
        except CheckoutError as e:
            emit(event_type="agent_error", agent_id=AGENT_ID, detail={"error": str(e)})
            return json.dumps({"error": str(e)})

    # ── ssh_execute ──────────────────────────────────────────────────────────
    elif tool_name == "ssh_execute":
        if not _session.get("token"):
            return json.dumps({"error": "No active session. Call checkout_credential first."})

        command = tool_input["command"]
        result = ssh_execute(
            token=_session["token"],
            host=_session["host"],
            port=_session["port"],
            username=_session["username"],
            command=command,
            allowed_commands=_session.get("allowed_commands", []),
            password=_session.get("password"),
        )

        # Scan stdout for prompt injection
        if result.stdout:
            scan = scan_output(
                text=result.stdout,
                source=f"stdout of: {command}",
                token=_session["token"],
            )
            if scan.is_suspicious:
                return json.dumps({
                    "command": command,
                    "blocked_by_injection_detector": True,
                    "warning": format_injection_warning(scan),
                    "stdout": "[REDACTED — injection detected]",
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                })

        if result.blocked:
            return json.dumps({
                "command": command,
                "blocked": True,
                "reason": result.block_reason,
                "exit_code": result.exit_code,
            })

        return json.dumps({
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
        })

    # ── checkin_credential ───────────────────────────────────────────────────
    elif tool_name == "checkin_credential":
        token = _session.get("token")
        if not token:
            return json.dumps({"error": "No token to check in."})
        try:
            result = checkin_credential(token=token)
            _session.clear()
            return json.dumps(result)
        except CheckinError as e:
            return json.dumps({"error": str(e)})

    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_agent(
    task: str,
    credential_id: str,
    stream_callback: Optional[callable] = None,
) -> str:
    """
    Run the PAM agent for a given task.

    Args:
        task: Natural language task description
        credential_id: Which credential to use (e.g. "prod-ec2-001")
        stream_callback: Optional callable(text) for streaming output to UI

    Returns:
        Final agent response as a string
    """
    messages = [
        {
            "role": "user",
            "content": (
                f"Task: {task}\n"
                f"Target credential: {credential_id}\n\n"
                f"Please complete this task following PAM protocol: "
                f"checkout → execute → checkin."
            ),
        }
    ]

    tools = [CHECKOUT_TOOL, SSH_TOOL, CHECKIN_TOOL]
    final_response = ""

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Collect text from this turn
        for block in response.content:
            if block.type == "text" and block.text:
                final_response = block.text
                if stream_callback:
                    stream_callback(block.text)

        # If Claude is done, break
        if response.stop_reason == "end_turn":
            break

        # If Claude wants to use tools, handle them
        if response.stop_reason == "tool_use":
            # Add Claude's response to history
            messages.append({"role": "assistant", "content": response.content})

            # Process all tool calls in this turn
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if stream_callback:
                        safe_input = {
                            k: ("***redacted***" if k == "token" else v)
                            for k, v in block.input.items()
                        }
                        stream_callback(f"\n[Tool: {block.name}({json.dumps(safe_input)})]\n")

                    result_str = _handle_tool_call(block.name, block.input)

                    if stream_callback:
                        safe_result = re.sub(r'"token"\s*:\s*"[^"]{20,}"', '"token": "***redacted***"', result_str)
                        stream_callback(f"[Result: {safe_result[:200]}...]\n")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        break

    # Safety net — if agent somehow exits without checkin, force it
    if _session.get("token"):
        try:
            checkin_credential(_session["token"])
            emit(
                event_type="session_checkin",
                agent_id=AGENT_ID,
                token=_session["token"],
                detail={"forced": True, "reason": "safety_net_on_exit"},
            )
            _session.clear()
        except Exception:
            pass

    return final_response


# ── CLI entrypoint ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PAM Agent — Claude-powered privileged access agent")
    parser.add_argument("--task", required=True, help="Task to perform on the target machine")
    parser.add_argument("--credential", default="prod-ec2-001", help="Credential ID to use")
    args = parser.parse_args()

    print(f"\n[agent-pam] Starting agent for task: '{args.task}'")
    print(f"[agent-pam] Target credential: {args.credential}\n")
    print("─" * 60)

    def print_stream(text: str):
        print(text, end="", flush=True)

    result = run_agent(
        task=args.task,
        credential_id=args.credential,
        stream_callback=print_stream,
    )

    print("\n" + "─" * 60)
    print("\n[agent-pam] Task complete.\n")


if __name__ == "__main__":
    main()
