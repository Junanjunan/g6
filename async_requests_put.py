# pip install aiohttp

import aiohttp
import asyncio

async def send_request(session, url, data, headers):
    async with session.put(url, json=data, headers=headers) as response:
        return response.status, await response.text()

async def main(url, data, headers):
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, url, data, headers) for _ in range(1000)]
        responses = await asyncio.gather(*tasks)
        print(responses)

if __name__ == "__main__":
    # URL you are sending the PUT request to
    # url = "http://localhost:8000/api/v1/board/free/206"
    url = "http://localhost:8000/api/v1/board/free/5209/comment"    # 댓글 수정

    # Headers you may need to send (e.g., Content-Type, Authorization)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NTc3MDYxLCJleHAiOjE3MTU2MTEyNjF9.cxABhoSXWiL30QJyR1TS-s_ayhRCuAGsl1Wm0Avbm3c'
    }

    # Data to be sent in JSON format
    # data = {
    #     "wr_subject": "string",
    #     "wr_content": "",
    #     "wr_name": "",
    #     "wr_password": "",
    #     "wr_email": "",
    #     "wr_homepage": "",
    #     "wr_link1": "",
    #     "wr_link2": "",
    #     "wr_option": "",
    #     "html": "",
    #     "mail": "",
    #     "secret": "",
    #     "ca_name": "",
    #     "notice": "false",
    #     "parent_id": 0,
    #     "additionalProp1": {}
    # } # 게시글 수정?
    data = {
        "wr_content": "88888",
        "wr_name": "",
        "wr_password": "",
        "wr_option": "html1",
        "comment_id": 5753,
        "additionalProp1": {}
    }


    asyncio.run(main(url, data, headers))
