# pip install aiohttp

import aiohttp
import asyncio

async def send_request(session, url, data, headers):
    async with session.post(url, json=data, headers=headers) as response:
        return response.status, await response.text()

async def main(url, data, headers):
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, url, data, headers) for _ in range(1)]
        responses = await asyncio.gather(*tasks)
        print(responses)

if __name__ == "__main__":
    # URL you are sending the PUT request to
    url = "http://localhost:8000/api/v1/board_new/new_delete"   # 최신 게시글 삭제 (리스트)

    # Headers you may need to send (e.g., Content-Type, Authorization)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NTgxMTk5LCJleHAiOjE3MTU2MTUzOTl9.o8hWQYxN1qu2JFmmwjvh83QXtjL2G3p2cIOPaDqDCc8'
    }

    # data = [11]
    # asyncio.run(main(url, data, headers))

    for i in range(300, 600):
        asyncio.run(main(url, [i], headers))
