# pip install aiohttp

import aiohttp
import asyncio

async def send_request(session, url, headers):
    async with session.get(url, headers=headers) as response:
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
    # url = "http://localhost:8000/api/v1/ajax/autosave_list"   # 자동저장 목록
    # url = "http://localhost:8000/api/v1/ajax/autosave_count"   # 자동저장글 개수
    # url = "http://localhost:8000/api/v1/ajax/autosave_load/2024042312594840"   # 자동저장글 불러오기
    # url = "http://localhost:8000/api/v1/board_new/new"   # 최신 게시글 목록
    # url = "http://localhost:8000/api/v1/ajax/good/free/5754/good"   # 좋아요/싫어요
    # url = "http://localhost:8000/board/delete_comment/free/5650"
    # url = "http://localhost:8000/board/write/free"
    # url = "http://localhost:8000/bbs/content/company"   # 컨텐츠
    # url = "http://localhost:8000/bbs/current_connect"   # 현재 접속자
    # url = "http://localhost:8000/bbs/faq"   # faq
    # url = "http://localhost:8000/bbs/member_leave"   # 회원탈퇴 폼
    # url = "http://localhost:8000/bbs/memo"   # 메모
    # url = "http://localhost:8000/bbs/memo_view/1?kind=send"   # 메모 읽기
    # url = "http://localhost:8000/bbs/password/w/free/201"   # 비밀글 읽기 폼
    # url = "http://localhost:8000/bbs/poll_result/1"   # 설문조사 결과
    # url = "http://localhost:8000/bbs/qalist"   # qa 목록
    # url = "http://localhost:8000/bbs/search?sfl=wr_subject%7C%7Cwr_content&sop=and&stx=ab&gr_id=community"   # 템플릿 검색
    url = "http://localhost:8000/api/v1/search?sfl=wr_subject%7C%7Cwr_content&sop=and&stx=ab&gr_id=community"   # 게시판 검색 api

    # Headers you may need to send (e.g., Content-Type, Authorization)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1NjUxMzYyLCJleHAiOjE3MTU2ODU1NjJ9.8TEe6Ts59oOV3rMKIN6q-kPsLOsO8drRZVzrf9ehRiQ'
    }

    asyncio.run(main(url, headers=headers))
