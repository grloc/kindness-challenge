"""Optional billed remote run. API signatures checked against official SDK reference.
Not integration tested. Requires an existing Linux template with python3 and a writable /workspace.
"""
import argparse
from pathlib import Path
import time
import uuid

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--cleanup", choices=("delete", "pause"), default="delete")
    parser.add_argument("--accept-billed-compute", action="store_true")
    args = parser.parse_args()
    if not args.accept_billed_compute:
        parser.error("Remote compute is billed. Review README, then explicitly accept billed compute.")
    from sandbox_sdk import SandboxClient
    root = Path(__file__).resolve().parent
    client = SandboxClient()  # Reads GMI_SANDBOX_API_KEY; never paste it in this file.
    sandbox = None
    completed = False
    try:
        sandbox = client.sandboxes.create(
            template_id=args.template_id,
            timeout=600,
            metadata={"community": "clouders", "challenge": "kindness-resources-2026-11-09"},
            idempotency_key=str(uuid.uuid4()),
        )
        print("Sandbox ID for PRIVATE cleanup records:", sandbox.sandbox_id)
        sandbox.wait_until_running(timeout=300)
        sandbox.connect(timeout=300)
        # Fixed paths and filenames only. Upload no personal or secret data.
        sandbox.files.upload(str(root / "sample_resources.csv"), "/workspace/kindness_input.csv")
        sandbox.files.upload(str(root / "clean_resources.py"), "/workspace/kindness_clean.py")
        execution = sandbox.commands.run(
            "python3 /workspace/kindness_clean.py /workspace/kindness_input.csv /workspace/kindness_output.csv",
            wait=False, execution_timeout_seconds=60,
        )
        execution.wait(timeout=90, cancel_on_timeout=True)
        if execution.exit_code != 0:
            raise RuntimeError("Cleaning failed: " + str(execution.stderr))
        sandbox.files.download("/workspace/kindness_output.csv", destination=str(root / "downloaded_resources.csv"))
        if (root / "downloaded_resources.csv").read_bytes() != (root / "expected_resources.csv").read_bytes():
            raise RuntimeError("Downloaded output differs from expected output")
        print("Output verified: downloaded_resources.csv")
        completed = True
    finally:
        if sandbox is not None:
            # Errors always delete. Pause is an explicit option after a successful run only.
            try:
                if completed and args.cleanup == "pause":
                    sandbox.pause()
                    deadline = time.monotonic() + 60
                    while time.monotonic() < deadline:
                        sandbox.refresh()
                        if sandbox.state == "paused":
                            print("Pause confirmed. Retained files are not a permanent backup. Delete when done.")
                            break
                        time.sleep(2)
                    else:
                        print("Pause not confirmed; requesting deletion instead.")
                        sandbox.delete()
                else:
                    sandbox.delete()
                    print("Deletion requested. Confirm in Console.")
            except Exception:
                print("CLEANUP NOT CONFIRMED. Check this sandbox privately in Console immediately:", sandbox.sandbox_id)
                raise

if __name__ == "__main__":
    main()
