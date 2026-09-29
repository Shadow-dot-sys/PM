#
# Copyright (C) 2021-2022 by TheAloneteam@Github
#

import asyncio
import os
import re
import json
import logging
import urllib.parse
import time
from typing import Union

import httpx
import yt_dlp


API_URL = os.getenv(
    "API_URL",
    "https://api.riteshyt.in"
).rstrip("/")

# Existing configured key is kept as fallback.
# Prefer setting API_KEY in the environment.
API_KEY = os.getenv(
    "API_KEY",
    "YOUR_EXISTING_API_KEY"
)


try:
    from pyrogram.enums import MessageEntityType
    from pyrogram.types import Message
except ImportError:
    class MessageEntityType:
        URL = "url"
        TEXT_LINK = "text_link"

    class Message:
        pass


try:
    from youtubesearchpython.__future__ import VideosSearch, Playlist
except ImportError:
    VideosSearch = None
    Playlist = None


try:
    from AloneMusic.utils.database import is_on_off
except ImportError:
    async def is_on_off(*args, **kwargs):
        return True


try:
    from AloneMusic.utils.formatters import time_to_seconds
except ImportError:
    def time_to_seconds(time_str: str) -> int:
        if not time_str:
            return 0

        try:
            parts = list(map(int, time_str.split(":")))

            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]

            if len(parts) == 2:
                return parts[0] * 60 + parts[1]

            if len(parts) == 1:
                return parts[0]

        except Exception:
            pass

        return 0


def extract_vidid(query: str) -> str:
    if not query:
        return None

    if re.match(r"^[a-zA-Z0-9_-]{11}$", str(query)):
        return query

    regex = (
        r"(?:youtube\.com\/(?:[^\/]+\/.+\/|"
        r"(?:v|e(?:mbed)?)\/|shorts\/|.*[?&]v=)|"
        r"youtu\.be\/)([^\"&?\/\s]{11})"
    )

    match = re.search(regex, str(query))

    return match.group(1) if match else None


async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            print(stderr.decode(errors="ignore"))
            return None

        try:
            return json.loads(stdout.decode())
        except Exception:
            return None

    info = await get_format_info(link)

    if not info:
        return None

    formats = info.get("formats", [])

    total_size = 0

    for fmt in formats:
        if fmt.get("filesize"):
            total_size += fmt["filesize"]

    return total_size


class YouTubeAPI:

    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"

        self._client = None
        self._recent_prefetches = {}

    async def get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    600.0,
                    connect=15.0
                ),
                follow_redirects=True,
            )

        return self._client

    async def exists(
        self,
        link: str,
        videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link

        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message):
        messages = [message_1]

        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:

            if getattr(message, "entities", None):

                for entity in message.entities:

                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption

                        return text[
                            entity.offset:
                            entity.offset + entity.length
                        ]

            elif getattr(message, "caption_entities", None):

                for entity in message.caption_entities:

                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url

        return None

    def _clean_link(self, link):

        if not link:
            return ""

        link = str(link)

        if "&" in link:
            link = link.split("&")[0]

        if "?si=" in link:
            link = link.split("?si=")[0]

        elif "&si=" in link:
            link = link.split("&si=")[0]

        return link

    async def _fetch_details(self, link):

        link = self._clean_link(link)

        client = await self.get_client()

        params = {
            "link": link
        }

        if API_KEY:
            params["api_key"] = API_KEY

        try:

            response = await client.get(
                f"{API_URL}/details",
                params=params
            )

            if response.status_code == 200:
                return response.json()

            logging.warning(
                f"API details returned {response.status_code}"
            )

        except Exception as e:

            logging.warning(
                f"API details error: {e}"
            )

        return None

    async def details(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        link = self._clean_link(link)

        data = await self._fetch_details(link)

        if data:

            return (
                data.get("title"),
                data.get("duration_min"),
                data.get("duration_sec", 0),
                data.get("thumbnail"),
                data.get("vidid"),
            )

        if VideosSearch:

            try:

                results = VideosSearch(
                    link,
                    limit=1
                )

                res = await results.next()

                if res and res.get("result"):

                    result = res["result"][0]

                    duration = result.get("duration")

                    return (
                        result.get("title"),
                        duration,
                        time_to_seconds(duration),
                        result["thumbnails"][0]["url"].split("?")[0],
                        result["id"],
                    )

            except Exception as e:

                logging.warning(
                    f"VideosSearch details fallback: {e}"
                )

        return None, None, 0, None, None

    async def title(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        data = await self._fetch_details(
            self._clean_link(link)
        )

        if data:
            return data.get("title")

        return None

    async def duration(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        data = await self._fetch_details(
            self._clean_link(link)
        )

        if data:
            return data.get("duration_min")

        return None

    async def thumbnail(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        data = await self._fetch_details(
            self._clean_link(link)
        )

        if data:
            return data.get("thumbnail")

        return None

    async def video(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        link = self._clean_link(link)

        result = await self.download(
            link,
            None,
            video=True
        )

        if result and isinstance(result, tuple):
            return 1, result[0]

        return 0, None

    async def playlist(
        self,
        link,
        limit,
        user_id,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.listbase + link

        link = self._clean_link(link)

        client = await self.get_client()

        params = {
            "link": link,
            "limit": limit,
        }

        if API_KEY:
            params["api_key"] = API_KEY

        try:

            response = await client.get(
                f"{API_URL}/playlist",
                params=params
            )

            if response.status_code == 200:

                data = response.json()

                return data.get("videos")

            logging.warning(
                f"Playlist API status: {response.status_code}"
            )

        except Exception as e:

            logging.warning(
                f"Playlist API error: {e}"
            )

        return None

    async def track(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        link = self._clean_link(link)

        data = await self._fetch_details(link)

        if data:

            vidid = data.get("vidid")

            if not vidid:
                vidid = extract_vidid(link)

            if not vidid:
                logging.warning(
                    f"Invalid video ID from API: {link}"
                )
                return None, None

            track_details = {
                "title": data.get("title"),
                "link": data.get("link") or link,
                "vidid": vidid,
                "duration_min": data.get("duration_min"),
                "thumb": data.get("thumbnail"),
            }

            return track_details, vidid

        return None, None

    async def formats(
        self,
        link,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        link = self._clean_link(link)

        client = await self.get_client()

        params = {
            "link": link
        }

        if API_KEY:
            params["api_key"] = API_KEY

        try:

            response = await client.get(
                f"{API_URL}/formats",
                params=params
            )

            if response.status_code == 200:

                data = response.json()

                formats = data.get(
                    "formats",
                    []
                )

                for fmt in formats:
                    fmt["yturl"] = link

                return formats, link

        except Exception as e:

            logging.warning(
                f"Formats API error: {e}"
            )

        return [], link

    async def slider(
        self,
        link,
        query_type,
        videoid: Union[bool, str] = None
    ):

        if videoid:
            link = self.base + link

        link = self._clean_link(link)

        client = await self.get_client()

        params = {
            "query": link,
            "limit": 10,
        }

        if API_KEY:
            params["api_key"] = API_KEY

        try:

            response = await client.get(
                f"{API_URL}/search",
                params=params
            )

            if response.status_code == 200:

                data = response.json()

                results = data.get(
                    "result",
                    []
                )

                if len(results) > query_type:

                    target = results[query_type]

                    thumbnails = target.get(
                        "thumbnails"
                    ) or []

                    thumbnail = (
                        thumbnails[0]["url"].split("?")[0]
                        if thumbnails
                        else None
                    )

                    return (
                        target.get("title"),
                        target.get("duration"),
                        thumbnail,
                        target.get("id"),
                    )

        except Exception as e:

            logging.warning(
                f"Search API error: {e}"
            )

        return None, None, None, None

    async def prefetch(
        self,
        link,
        video=False
    ):

        if not API_URL:
            return False

        link = self._clean_link(link)

        dl_type = (
            "video"
            if video
            else "audio"
        )

        vidid = extract_vidid(link) or link

        cache_key = f"{vidid}_{dl_type}"

        now = time.time()

        if cache_key in self._recent_prefetches:

            if (
                now -
                self._recent_prefetches[cache_key]
                < 30
            ):
                return True

        self._recent_prefetches[cache_key] = now

        params = {
            "query": vidid,
            "dl_type": dl_type,
            "prefetch": "true",
        }

        if API_KEY:
            params["api_key"] = API_KEY

        try:

            client = await self.get_client()

            response = await client.get(
                f"{API_URL}/download",
                params=params,
            )

            return response.status_code in (
                200,
                202,
                204,
                307,
            )

        except Exception as e:

            logging.warning(
                f"Prefetch failed: {e}"
            )

        return False

    async def prefetch_queue(
        self,
        queries,
        video=False
    ):

        if not API_URL or not queries:
            return False

        dl_type = (
            "video"
            if video
            else "audio"
        )

        payload = {
            "queries": queries,
            "dl_type": dl_type,
        }

        params = {}

        if API_KEY:
            params["api_key"] = API_KEY

        try:

            client = await self.get_client()

            response = await client.post(
                f"{API_URL}/prefetch_bulk",
                json=payload,
                params=params,
            )

            return response.status_code < 400

        except Exception as e:

            logging.warning(
                f"Bulk prefetch failed: {e}"
            )

        return False

    async def _api_download(
        self,
        link,
        dl_type,
        filepath
    ):

        if not API_URL:
            return False

        vidid = (
            extract_vidid(link)
            or link
        )

        params = {
            "query": vidid,
            "dl_type": dl_type,
        }

        if API_KEY:
            params["api_key"] = API_KEY

        os.makedirs(
            os.path.dirname(filepath),
            exist_ok=True
        )

        temp_file = filepath + ".part"

        try:

            if os.path.exists(temp_file):
                os.remove(temp_file)

            logging.info(
                f"API DOWNLOAD START: {vidid} [{dl_type}]"
            )

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    600.0,
                    connect=20.0
                ),
                follow_redirects=True,
            ) as client:

                async with client.stream(
                    "GET",
                    f"{API_URL}/download",
                    params=params,
                ) as response:

                    logging.info(
                        f"API DOWNLOAD STATUS: "
                        f"{response.status_code}"
                    )

                    if response.status_code != 200:

                        body = await response.aread()

                        logging.error(
                            f"API DOWNLOAD FAILED: "
                            f"{body[:300]!r}"
                        )

                        return False

                    content_type = (
                        response.headers.get(
                            "content-type",
                            ""
                        ).lower()
                    )

                    total = 0

                    with open(
                        temp_file,
                        "wb"
                    ) as file:

                        async for chunk in response.aiter_bytes(
                            1024 * 128
                        ):

                            if not chunk:
                                continue

                            file.write(chunk)
                            total += len(chunk)

                    if total <= 1000:

                        logging.error(
                            f"API returned invalid "
                            f"file size: {total}"
                        )

                        return False

                    os.replace(
                        temp_file,
                        filepath
                    )

                    logging.info(
                        f"API DOWNLOAD SUCCESS: "
                        f"{filepath} "
                        f"({total} bytes, {content_type})"
                    )

                    return True

        except Exception as e:

            logging.exception(
                f"API DOWNLOAD ERROR "
                f"{vidid}: {e}"
            )

            try:

                if os.path.exists(temp_file):
                    os.remove(temp_file)

            except Exception:
                pass

            return False

    async def download(
        self,
        link,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ):

        if videoid:
            link = self.base + link

        link = self._clean_link(link)

        vidid = extract_vidid(link) or link

        # =========================================================
        # API AUDIO / VIDEO DOWNLOAD
        # =========================================================

        if API_URL:

            dl_type = (
                "video"
                if (video or songvideo)
                else "audio"
            )

            # -----------------------------------------------------
            # AUDIO
            # -----------------------------------------------------

            if dl_type == "audio":

                # API response in your test is ISO/MP4 container
                # despite content-type saying audio/mpeg.
                # Use .m4a so downstream ffmpeg can identify it.
                fpath = (
                    f"downloads/{vidid}.m4a"
                )

                # Warm API cache, but do not wait for it.
                asyncio.create_task(
                    self.prefetch(
                        link,
                        video=False
                    )
                )

                success = await self._api_download(
                    link,
                    "audio",
                    fpath
                )

                if success:

                    return fpath, True

                # IMPORTANT:
                # Do NOT fallback to yt-dlp for audio.
                # YouTube on this VPS is returning bot-check.
                logging.error(
                    f"API audio download failed "
                    f"for {vidid}; yt-dlp fallback disabled."
                )

                return None

            # -----------------------------------------------------
            # VIDEO
            # -----------------------------------------------------

            fpath = (
                f"downloads/{vidid}.mp4"
            )

            success = await self._api_download(
                link,
                "video",
                fpath
            )

            if success:
                return fpath, True

            logging.warning(
                f"API video download failed "
                f"for {vidid}; trying yt-dlp fallback."
            )

        # =========================================================
        # LOCAL YT-DLP FALLBACK
        # Only reached for VIDEO now.
        # =========================================================

        loop = asyncio.get_running_loop()

        def video_dl():

            opts = {
                "format": (
                    "(bestvideo[height<=720]"
                    "[width<=1280][ext=mp4])"
                    "+(bestaudio[ext=m4a])"
                ),
                "outtmpl": (
                    "downloads/%(id)s.%(ext)s"
                ),
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
            }

            ydl = yt_dlp.YoutubeDL(opts)

            info = ydl.extract_info(
                link,
                download=False
            )

            path = os.path.join(
                "downloads",
                f"{info['id']}.{info['ext']}"
            )

            if os.path.exists(path):
                return path

            ydl.download([link])

            return path

        if video:

            try:

                downloaded_file = (
                    await loop.run_in_executor(
                        None,
                        video_dl
                    )
                )

                return downloaded_file, True

            except Exception as e:

                logging.error(
                    f"Video download failed: {e}"
                )

                return None

        # Safety fallback:
        # Never call yt-dlp for normal audio.
        return None

    async def close(self):

        if (
            self._client
            and not self._client.is_closed
        ):
            await self._client.aclose()


YouTube = YouTubeAPI()
