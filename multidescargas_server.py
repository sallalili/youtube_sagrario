
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List

from mcp import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    ToolInputSchema,
    ToolResult,
)

# Intentamos importar yt_dlp como librería (distinto del binario de sistema)
try:
    from yt_dlp import YoutubeDL
except Exception as exc:  # pragma: no cover
    YoutubeDL = None  # type: ignore


@dataclass
class JobState:
    job_id: str
    kind: str  # "video" | "playlist"
    url: str
    status: str = "pending"  # pending | running | completed | error | cancelled
    progress: float = 0.0  # 0..100
    filename: Optional[str] = None
    error: Optional[str] = None
    _cancel_flag: bool = False
    _thread: Optional[threading.Thread] = field(default=None, repr=False, compare=False)


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self, kind: str, url: str) -> JobState:
        job_id = str(uuid.uuid4())
        state = JobState(job_id=job_id, kind=kind, url=url)
        with self._lock:
            self._jobs[job_id] = state
        return state

    def get(self, job_id: str) -> Optional[JobState]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_all(self) -> List[JobState]:
        with self._lock:
            return list(self._jobs.values())

    def cancel(self, job_id: str) -> bool:
        job = self.get(job_id)
        if not job:
            return False
        job._cancel_flag = True
        job.status = "cancelled" if job.status in {"pending"} else job.status
        return True


jobs = JobRegistry()
server = Server("multidescargas")


def _ensure_yt_dlp() -> None:
    if YoutubeDL is None:
        raise RuntimeError(
            "yt-dlp no está disponible como librería de Python. Instálalo con 'pip install yt-dlp'."
        )


def _run_download(job: JobState, is_playlist: bool) -> None:
    _ensure_yt_dlp()

    def hook(d: Dict[str, Any]) -> None:
        # Permitir cancelación cooperativa
        if job._cancel_flag:
            raise Exception("cancelled-by-user")
        if d.get("status") == "downloading":
            try:
                frac = float(d.get("downloaded_bytes", 0)) / float(d.get("total_bytes", d.get("total_bytes_estimate", 1)) or 1)
                job.progress = max(0.0, min(100.0, frac * 100.0))
            except Exception:
                pass
        elif d.get("status") == "finished":
            job.progress = 100.0
            job.filename = d.get("filename") or job.filename

    ydl_opts: Dict[str, Any] = {
        "outtmpl": "%(title)s.%(ext)s",
        "noplaylist": not is_playlist,
        "progress_hooks": [hook],
        "ignoreerrors": True,
        "merge_output_format": "mp4",
        "concurrent_fragment_downloads": 3,
        "quiet": True,
        "no_warnings": True,
    }

    job.status = "running"
    try:
        with YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
            ydl.download([job.url])
        if not job._cancel_flag and job.status != "cancelled":
            job.status = "completed"
    except Exception as exc:  # puede venir de cancelación o error real
        if str(exc) == "cancelled-by-user" or job._cancel_flag:
            job.status = "cancelled"
        else:
            job.status = "error"
            job.error = str(exc)


@server.tool(
    name="download_video",
    description=(
        "Start downloading a video from YouTube or other supported sites. Returns a job ID to track download progress."
    ),
    input_schema=ToolInputSchema.json_schema(
        {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Video URL"},
                "format": {
                    "type": "string",
                    "description": "yt-dlp format selector (optional)",
                    "nullable": True,
                },
            },
            "required": ["url"],
        }
    ),
)
async def download_video(url: str, format: Optional[str] = None) -> ToolResult:
    job = jobs.create("video", url)

    def target() -> None:
        # El parámetro format es opcional; si se provee, añadimos a opts
        if format:
            # Pequeña adaptación: pasamos por variable global temporal en el hilo
            def _runner() -> None:
                nonlocal job
                _ensure_yt_dlp()

                def hook(d: Dict[str, Any]) -> None:
                    if job._cancel_flag:
                        raise Exception("cancelled-by-user")
                    if d.get("status") == "downloading":
                        try:
                            frac = float(d.get("downloaded_bytes", 0)) / float(
                                d.get("total_bytes", d.get("total_bytes_estimate", 1)) or 1
                            )
                            job.progress = max(0.0, min(100.0, frac * 100.0))
                        except Exception:
                            pass
                    elif d.get("status") == "finished":
                        job.progress = 100.0
                        job.filename = d.get("filename") or job.filename

                opts = {
                    "outtmpl": "%(title)s.%(ext)s",
                    "noplaylist": True,
                    "progress_hooks": [hook],
                    "format": format,
                    "quiet": True,
                    "no_warnings": True,
                    "merge_output_format": "mp4",
                }
                job.status = "running"
                try:
                    with YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
                        ydl.download([job.url])
                    if not job._cancel_flag and job.status != "cancelled":
                        job.status = "completed"
                except Exception as exc:
                    if str(exc) == "cancelled-by-user" or job._cancel_flag:
                        job.status = "cancelled"
                    else:
                        job.status = "error"
                        job.error = str(exc)

            _runner()
        else:
            _run_download(job, is_playlist=False)

    th = threading.Thread(target=target, daemon=True)
    job._thread = th
    th.start()

    return ToolResult(content=[TextContent(type="text", text=job.job_id)])


@server.tool(
    name="download_playlist",
    description=(
        "Start downloading an entire playlist from YouTube or supported sites. Returns a job ID."
    ),
    input_schema=ToolInputSchema.json_schema(
        {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "Playlist URL"}},
            "required": ["url"],
        }
    ),
)
async def download_playlist(url: str) -> ToolResult:
    job = jobs.create("playlist", url)
    th = threading.Thread(target=lambda: _run_download(job, is_playlist=True), daemon=True)
    job._thread = th
    th.start()
    return ToolResult(content=[TextContent(type="text", text=job.job_id)])


@server.tool(
    name="get_download_status",
    description="Check the status of a download job.",
    input_schema=ToolInputSchema.json_schema(
        {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        }
    ),
)
async def get_download_status(job_id: str) -> ToolResult:
    job = jobs.get(job_id)
    if not job:
        return ToolResult(error="Job no encontrado")
    payload = {
        "job_id": job.job_id,
        "kind": job.kind,
        "url": job.url,
        "status": job.status,
        "progress": round(job.progress, 2),
        "filename": job.filename,
        "error": job.error,
    }
    return ToolResult(content=[TextContent(type="text", text=str(payload))])


@server.tool(
    name="cancel_download",
    description="Cancel a running or pending download job.",
    input_schema=ToolInputSchema.json_schema(
        {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        }
    ),
)
async def cancel_download(job_id: str) -> ToolResult:
    ok = jobs.cancel(job_id)
    return ToolResult(content=[TextContent(type="text", text="cancelled" if ok else "not-found")])


@server.tool(
    name="list_downloads",
    description="List all download jobs with their current status.",
)
async def list_downloads() -> ToolResult:
    listing = [
        {
            "job_id": j.job_id,
            "kind": j.kind,
            "url": j.url,
            "status": j.status,
            "progress": round(j.progress, 2),
            "filename": j.filename,
        }
        for j in jobs.list_all()
    ]
    return ToolResult(content=[TextContent(type="text", text=str(listing))])


@server.tool(
    name="get_video_metadata",
    description="Fetch metadata about a video without downloading it.",
    input_schema=ToolInputSchema.json_schema(
        {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        }
    ),
)
async def get_video_metadata(url: str) -> ToolResult:
    _ensure_yt_dlp()
    info: Dict[str, Any]
    with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:  # type: ignore[arg-type]
        info = ydl.extract_info(url, download=False)
    minimal = {
        "id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "webpage_url": info.get("webpage_url"),
        "thumbnails": info.get("thumbnails", [])[:3],
    }
    return ToolResult(content=[TextContent(type="text", text=str(minimal))])


async def main() -> None:
    tools: List[Tool] = await server.get_registered_tools()
    # Ejecuta el servidor MCP sobre stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
