# pip install aiohttp

import aiohttp
import asyncio

async def send_request(session, url, headers):
    async with session.post(url, headers=headers) as response:
        return response.status, await response.text()

async def main(url, headers):
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, url, headers) for _ in range(1000)]
        responses = await asyncio.gather(*tasks)
        print(responses)

if __name__ == "__main__":
    # URL you are sending the PUT request to
    # url = "http://localhost:8000/api/v1/board/move/free/copy"
    # url = "http://localhost:8000/api/v1/board/uploadfile/free/203"
    url = "http://localhost:8000/api/v1/board/free/5209/download/1"

    # Headers you may need to send (e.g., Content-Type, Authorization)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NTcxNjk2LCJleHAiOjE3MTU2MDU4OTZ9.Yhlh60vkrD2vxw399n_bzHRM9vqldBhLrPMub3rTvoM'
    }

    # Data to be sent in JSON format
    # data = {
    #     "wr_ids": [1, 2, 3],
    # }

    asyncio.run(main(url, headers))
