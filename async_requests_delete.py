# pip install aiohttp

import aiohttp
import asyncio

async def send_request(session, url, headers):
    async with session.delete(url, headers=headers) as response:
        return response.status, await response.text()

async def main(url, headers):
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, url, headers) for _ in range(1000)]
        responses = await asyncio.gather(*tasks)
        print(responses)

if __name__ == "__main__":
    # URL you are sending the PUT request to
    # url = "http://localhost:8000/api/v1/board/free/1"   # 게시글 삭제
    # url = "http://localhost:8000/api/v1/board/free/5209/comment/5751"   # 댓글 삭제
    url = "http://localhost:8000/api/v1/ajax/autosave/3"   # 자동저장글 삭제

    # Headers you may need to send (e.g., Content-Type, Authorization)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NTc5NDY1LCJleHAiOjE3MTU2MTM2NjV9.sYtb4JHYIxQ59erS7Ftdztqhz9tOQzHXjCNK2T69ov8'
    }

    asyncio.run(main(url, headers=headers))
