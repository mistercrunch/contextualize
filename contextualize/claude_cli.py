#!/usr/bin/env python3
"""
Claude Code CLI interface abstraction
"""

import json
import subprocess
import uuid
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path


class ClaudeCLI:
    """Abstraction layer for Claude Code CLI interactions"""

    @staticmethod
    def start_session(
        prompt: str, session_id: str, background: bool = False, output_format: str = "text"
    ) -> subprocess.CompletedProcess:
        """Start a new Claude session with a specific ID"""
        cmd = [
            "claude",
            "--session-id",
            session_id,
            "--print",  # Exit after response
            "--output-format",
            output_format,
        ]

        if background:
            # Return Popen for background execution
            return subprocess.Popen(
                cmd + [prompt], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        else:
            # Return completed process for foreground
            return subprocess.run(cmd + [prompt], capture_output=True, text=True)

    @staticmethod
    def fork_session(
        original_session_id: str,
        prompt: str,
        output_format: str = "text",
        new_session_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Fork an existing session and execute a prompt

        Returns:
            Tuple of (new_session_id, output)
        """
        # Generate new session ID if not provided
        if not new_session_id:
            new_session_id = str(uuid.uuid4())

        # Note: Cannot use --session-id with --resume, Claude will generate one
        cmd = [
            "claude",
            "--resume",
            original_session_id,
            "--fork-session",
            "--print",
            "--output-format",
            output_format,
            prompt,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to fork session: {result.stderr}")

        # Try to extract session ID from JSON output if available
        if output_format == "json":
            try:
                data = json.loads(result.stdout)
                # Claude's JSON format includes session_id in metadata
                if isinstance(data, dict) and "session_id" in data:
                    new_session_id = data["session_id"]
                elif isinstance(data, dict) and "uuid" in data:
                    new_session_id = data["uuid"]
            except:
                # Keep the generated session ID if we can't extract it
                pass

        return new_session_id, result.stdout

    @staticmethod
    def resume_session(session_id: str) -> subprocess.CompletedProcess:
        """Resume an interactive session"""
        cmd = ["claude", "--session-id", session_id]
        return subprocess.run(cmd)

    @staticmethod
    def print_to_session(session_id: str, prompt: str, output_format: str = "text") -> str:
        """Send a prompt to a session and get response"""
        cmd = [
            "claude",
            "--session-id",
            session_id,
            "--print",
            "--output-format",
            output_format,
            prompt,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Failed to execute prompt: {result.stderr}")

        return result.stdout

    @staticmethod
    def parse_json_output(output: str) -> Dict[str, Any]:
        """Parse JSON output from Claude CLI

        Claude's JSON output includes metadata, extract the result
        """
        try:
            data = json.loads(output)
            # Claude returns {"type": "result", "result": "...", ...}
            if isinstance(data, dict) and "result" in data:
                return data["result"]
            return data
        except json.JSONDecodeError:
            # If not JSON, return as string
            return {"content": output}

    @staticmethod
    def get_session_logs(session_id: str, project_path: Path) -> Optional[List[Dict]]:
        """Read session logs from Claude's storage

        Sessions are stored in ~/.claude/projects/{encoded-path}/{session-id}.jsonl
        """
        import os
        from pathlib import Path

        # Encode project path for Claude's storage
        encoded_path = str(project_path).replace("/", "-")
        session_file = Path.home() / ".claude" / "projects" / encoded_path / f"{session_id}.jsonl"

        if not session_file.exists():
            return None

        logs = []
        with open(session_file) as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return logs

    @staticmethod
    def extract_session_messages(logs: List[Dict]) -> List[Dict]:
        """Extract user and assistant messages from session logs"""
        messages = []
        for entry in logs:
            if entry.get("type") in ["user", "assistant"]:
                messages.append(
                    {
                        "role": entry["type"],
                        "content": entry.get("message", {}).get("content", ""),
                        "timestamp": entry.get("timestamp"),
                    }
                )
        return messages
