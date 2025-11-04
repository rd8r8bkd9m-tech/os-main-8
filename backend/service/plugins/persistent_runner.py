"""Mock persistent runner for local inference.

Simulates a long-running inference server communicating via Unix socket.
Useful for testing scheduler routing and persistence semantics.
"""
from __future__ import annotations

import asyncio
import json
import logging
import socket
import os
from typing import Any, Dict, Optional

__all__ = ["MockPersistentRunner", "run_mock_runner"]

LOGGER = logging.getLogger("kolibri.mock_runner")


class MockPersistentRunner:
    """Simulated persistent inference runner.
    
    Listens on a Unix socket, accepts simple JSON-RPC style requests,
    and streams simulated inference tokens.
    """

    def __init__(self, socket_path: str = "/tmp/kolibri_runner.sock"):
        self.socket_path = socket_path
        self.running = False
        self.request_count = 0

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a single client connection."""
        client_addr = writer.get_extra_info("peername", "unknown")
        LOGGER.info(f"Client connected: {client_addr}")

        try:
            while self.running:
                try:
                    # Read up to 4KB per request
                    data = await asyncio.wait_for(reader.readexactly(1), timeout=5.0)
                except asyncio.TimeoutError:
                    break
                except asyncio.IncompleteReadError:
                    break

                # Collect a full line (JSON request)
                buffer = data
                while not buffer.endswith(b"\n"):
                    try:
                        chunk = await asyncio.wait_for(reader.readexactly(1), timeout=5.0)
                        buffer += chunk
                    except asyncio.TimeoutError:
                        break
                    except asyncio.IncompleteReadError:
                        break

                request_text = buffer.decode("utf-8", errors="ignore").strip()
                if not request_text:
                    continue

                try:
                    request = json.loads(request_text)
                except json.JSONDecodeError:
                    response = {"error": "Invalid JSON"}
                    writer.write(json.dumps(response).encode("utf-8") + b"\n")
                    await writer.drain()
                    continue

                # Handle request
                method = request.get("method", "unknown")
                params = request.get("params", {})

                if method == "healthz":
                    response = {"status": "ready", "requests_processed": self.request_count}
                elif method == "infer":
                    self.request_count += 1
                    prompt = params.get("prompt", "")
                    response = await self._simulate_inference(prompt, writer)
                    if response is None:
                        # Streaming response already sent
                        continue
                else:
                    response = {"error": f"Unknown method: {method}"}

                writer.write(json.dumps(response).encode("utf-8") + b"\n")
                await writer.drain()

        except Exception as e:
            LOGGER.exception(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            LOGGER.info(f"Client disconnected: {client_addr}")

    async def _simulate_inference(self, prompt: str, writer: asyncio.StreamWriter) -> Optional[Dict[str, Any]]:
        """Simulate streaming inference tokens.
        
        Returns None if streaming was handled, otherwise returns response dict.
        """
        # Simple simulation: repeat first few words and add generated text
        tokens = [
            "Kolibri",
            "AI",
            "Edge",
            "is",
            "a",
            "local-first",
            "platform",
            "for",
            "edge",
            "inference.",
        ]

        # Stream tokens one per message
        for i, token in enumerate(tokens):
            msg = {"type": "token", "token": token, "index": i}
            writer.write(json.dumps(msg).encode("utf-8") + b"\n")
            await writer.drain()
            await asyncio.sleep(0.05)  # Simulate processing

        # Final response
        final = {
            "type": "done",
            "tokens_generated": len(tokens),
            "estimated_cost_j": 0.25,
            "estimated_latency_ms": len(tokens) * 50.0,
        }
        writer.write(json.dumps(final).encode("utf-8") + b"\n")
        await writer.drain()

        return None  # Streaming was handled

    async def start(self) -> None:
        """Start the mock runner listening on Unix socket."""
        # Clean up any existing socket
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass

        self.running = True
        LOGGER.info(f"Starting mock runner on {self.socket_path}")

        server = await asyncio.start_unix_server(self._handle_client, self.socket_path)

        async with server:
            LOGGER.info("Mock runner ready")
            try:
                await server.serve_forever()
            except KeyboardInterrupt:
                LOGGER.info("Shutting down...")
            finally:
                self.running = False

    def stop(self) -> None:
        """Stop the runner."""
        self.running = False


async def run_mock_runner(socket_path: str = "/tmp/kolibri_runner.sock") -> None:
    """Entry point for running the mock persistent runner.
    
    Args:
        socket_path: Path to Unix socket for listening.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    runner = MockPersistentRunner(socket_path=socket_path)

    try:
        await runner.start()
    except KeyboardInterrupt:
        LOGGER.info("Interrupted")
        runner.stop()


if __name__ == "__main__":
    import sys

    socket_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/kolibri_runner.sock"
    asyncio.run(run_mock_runner(socket_path))

