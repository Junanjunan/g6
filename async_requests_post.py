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
    # url = "http://localhost:8000/api/v1/board/list_delete/free"   # 게시글 일괄 삭제
    # url = "http://localhost:8000/api/v1/board/free/5209/comment"    # 댓글 작성
    # url = "http://localhost:8000/api/v1/ajax/autosave"   # 자동저장
    # url = "http://localhost:8000/api/v1/board_new/new_delete"   # 최신 게시글 삭제 (리스트)
    # url = "http://localhost:8000/bbs/login"   # 최신 게시글 삭제 (리스트)

    # Headers you may need to send (e.g., Content-Type, Authorization)
    # headers = {
    #     'Content-Type': 'application/json',
    #     'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NTg1NjQ3LCJleHAiOjE3MTU2MTk4NDd9.KfWSzKOFAJXSywhJ60s1Y6Cz2pCDtrM97UW4sUsXUv4'
    # }

    headers = {
        # 'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NTg1NjQ3LCJleHAiOjE3MTU2MTk4NDd9.KfWSzKOFAJXSywhJ60s1Y6Cz2pCDtrM97UW4sUsXUv4'
    }

    # Data to be sent in JSON format
    # data = {
    #     "wr_ids": [1, 2, 3],
    # } # 게시글 일괄 삭제
    # data = {
    # "wr_content": "string",
    # "wr_name": "",
    # "wr_password": "",
    # "wr_option": "html1",
    # "comment_id": 0,
    # "additionalProp1": {}
    # } # 댓글 작성
    # data = {
    #     "as_uid": 2024042312573784,
    #     "as_subject": "6666",
    #     "as_content": "777",
    #     "additionalProp1": {}
    # }
    # data = {
    #     "bn_ids": [1, 2, 3]
    # }
    # data = [733, 732, 731, 730, 729]    # 최신 게시글 삭제 (리스트)
    # data = {
    #     "mb_id": "admin",
    #     "mb_password": "123",
    #     "auto_login": False,
    #     "url": "/"
    # } # 로그인 - 안됨..



    asyncio.run(main(url, data, headers))
