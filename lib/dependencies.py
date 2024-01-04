import os
from typing_extensions import Annotated

from fastapi import Depends, Form, Path, Query, Request
from sqlalchemy import exists, inspect, select

from core.database import DBConnect
from core.exception import AlertException
from core.models import Auth, Board, GroupMember
from lib.common import (
    ENV_PATH, check_token,
    get_current_admin_menu_id, get_current_captcha_cls
)
from lib.member_lib import get_admin_type, is_admin

async def get_variety_tokens(
    token_form: Annotated[str, Form(alias="token")] = None,
    token_query: Annotated[str, Query(alias="token")] = None
):
    """
    요청 매개변수의 유형별 토큰을 수신, 하나의 토큰만 반환
    - 함수의 매개변수 순서대로 우선순위를 가짐
    """
    return token_form or token_query


async def validate_token(
    request: Request,
    token: Annotated[str, Depends(get_variety_tokens)]
):
    """토큰 유효성 검사"""
    if not check_token(request, token):
        raise AlertException("토큰이 유효하지 않습니다", 403)


async def validate_captcha(
    request: Request,
    response: Annotated[str, Form(alias="g-recaptcha-response")] = None
):
    """구글 reCAPTCHA 유효성 검사"""
    config = request.state.config
    captcha_cls = get_current_captcha_cls(config)

    if captcha_cls:
        captcha = captcha_cls(config)
        if captcha and (not await captcha.verify(response)):
            raise AlertException("캡차가 올바르지 않습니다.", 400)


async def validate_install():
    """설치 여부 검사"""

    db_connect = DBConnect()
    engine = db_connect.engine
    prefix = db_connect.table_prefix

    if (os.path.exists(ENV_PATH)
            and inspect(engine).has_table(prefix + "config")):
        raise AlertException(
            "이미 설치가 완료되었습니다.\\n재설치하시려면 .env파일을 삭제 후 다시 시도해주세요.", 400, "/")


async def check_group_access(
        request: Request,
        bo_table: Annotated[str, Path(...)]):
    """그룹 접근권한 체크"""

    with DBConnect().sessionLocal() as db:
        board = db.get(Board, bo_table)
        group = board.group
        member = request.state.login_member

        # 그룹 접근 사용할때만 체크
        if group.gr_use_access:
            if not member:
                raise AlertException(
                    f"비회원은 이 게시판에 접근할 권한이 없습니다.\
                    \\n\\n회원이시라면 로그인 후 이용해 보십시오.", 403)

            # 최고관리자 또는 그룹관리자는 접근권한 체크 안함
            if not get_admin_type(request, member.mb_id, group=group):
                exists_group_member = db.scalar(
                    exists(GroupMember)
                    .where(GroupMember.gr_id == group.gr_id, GroupMember.mb_id == member.mb_id).select()
                )
                if not exists_group_member:
                    raise AlertException(
                        f"`{board.bo_subject}` 게시판에 대한 접근 권한이 없습니다.\
                        \\n\\n궁금하신 사항은 관리자에게 문의 바랍니다.", 403)


async def check_admin_access(request: Request):
    """관리자페이지 접근권한 체크"""
    db = DBConnect().sessionLocal()
    path = request.url.path
    ss_mb_id = request.session.get("ss_mb_id", "")

    # 관리자페이지 접근 권한 체크
    if not ss_mb_id:
        raise AlertException("로그인이 필요합니다.", 302, url="/bbs/login?url=" + path)
    elif not is_admin(request):
        method = request.method
        admin_menu_id = get_current_admin_menu_id(request)

        # 관리자 메뉴에 대한 권한 체크
        if admin_menu_id:
            au_auth = db.scalar(
                select(Auth.au_auth)
                .where(Auth.mb_id == ss_mb_id, Auth.au_menu == admin_menu_id)
            ) or ""
            # 각 요청 별 권한 체크
            # delete 요청은 GET 요청으로 처리되므로, 요청에 "delete"를 포함하는지 확인하여 처리
            if ("delete" in path and not "d" in au_auth):
                raise AlertException("삭제 권한이 없습니다.", 302, url="/")
            elif (method == "POST" and not "w" in au_auth):
                raise AlertException("수정 권한이 없습니다.", 302, url="/")
            elif (method == "GET" and not "r" in au_auth):
                raise AlertException("읽기 권한이 없습니다.", 302, url="/")
        # 관리자메인은 메뉴ID가 없으므로, 다른 메뉴의 권한이 있는지 확인
        else:
            exists_auth = db.scalar(
                exists(Auth)
                .where(Auth.mb_id == ss_mb_id).select()
            )
            if not exists_auth:
                raise AlertException(
                    "최고관리자 또는 관리권한이 있는 회원만 접근 가능합니다.", 302, url="/")


def common_search_query_params(
        sst: str = Query(default=""),
        sod: str = Query(default=""),
        sfl: str = Query(default=""),
        stx: str = Query(default=""),
        sca: str = Query(default=""),
        current_page: str = Query(default="1", alias="page")):
    """공통으로 사용하는 Query String 파라미터를 받는 함수"""
    try:
        current_page = int(current_page)
    except ValueError:
        # current_page가 정수로 변환할 수 없는 경우 기본값으로 1을 사용하도록 설정
        current_page = 1
    return {"sst": sst, "sod": sod, "sfl": sfl, "stx": stx, "sca": sca, "current_page": current_page}
