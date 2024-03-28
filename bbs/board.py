# 여기에서 write 와 post 는 글 한개라는 개념으로 사용합니다.
# 게시판 테이블을 write 로 사용하여 테이블명을 바꾸지 못하는 관계로
# 테이블명은 write 로, 글 한개에 대한 의미는 write 와 post 를 혼용하여 사용합니다.
import datetime
from datetime import datetime
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, Request, Form, Path, Query, File
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select, update

from core.database import db_session
from core.exception import AlertException
from core.formclass import WriteForm, WriteCommentForm
from core.models import Board, BoardGood, Group, Scrap, Member
from core.template import UserTemplates
from lib.board_lib import *
from lib.common import *
from lib.dependencies import (
    check_group_access, common_search_query_params,
    validate_captcha, validate_token, check_login_member,
    get_board, get_write, get_login_member
)
from lib.point import delete_point, insert_point
from lib.template_filters import datetime_format, number_format
from lib.template_functions import get_paging
from response_handlers.board import (
    ListPostService, CreatePostService, ReadPostService,
    UpdatePostService, DeletePostService, GroupBoardListService,
    CreateCommentService, DeleteCommentService
)


router = APIRouter()
templates = UserTemplates()
templates.env.filters["set_image_width"] = set_image_width
templates.env.filters["url_auto_link"] = url_auto_link
templates.env.globals["get_admin_type"] = get_admin_type
templates.env.globals["get_unique_id"] = get_unique_id
templates.env.globals["board_config"] = BoardConfig
templates.env.globals["get_list_thumbnail"] = get_list_thumbnail
templates.env.globals["captcha_widget"] = captcha_widget

FILE_DIRECTORY = "data/file/"


@router.get("/group/{gr_id}")
async def group_board_list(
    request: Request,
    db: db_session,
    gr_id: str = Path(...)
):
    """
    게시판그룹의 모든 게시판 목록을 보여준다.
    """
    # 게시판 그룹 정보 조회
    group_board_list_service = GroupBoardListService(
        request, db, gr_id, request.state.login_member
    )
    group = group_board_list_service.group
    group_board_list_service.check_mobile_only()
    boards = group_board_list_service.get_boards_in_group()

    context = {
        "request": request,
        "group": group,
        "boards": boards,
        "render_latest_posts": render_latest_posts
    }
    return templates.TemplateResponse("/board/group.html", context)


@router.get("/{bo_table}")
async def list_post(
    request: Request,
    db: db_session,
    bo_table: Annotated[str, Path(...)],
    board: Annotated[Board, Depends(get_board)],
    search_params: Annotated[dict, Depends(common_search_query_params)],
):
    list_post_service = ListPostService(
        request, db, bo_table, board, request.state.login_member, search_params
    )

    context = {
        "request": request,
        "categories": list_post_service.categories,
        "board": board,
        "board_config": list_post_service,
        "notice_writes": list_post_service.get_notice_writes(search_params),
        "writes": list_post_service.get_writes(search_params),
        "total_count": list_post_service.get_total_count(),
        "current_page": search_params['current_page'],
        "paging": get_paging(request, search_params['current_page'], list_post_service.get_total_count(), list_post_service.page_rows),
        "is_write": list_post_service.is_write_level(),
        "table_width": list_post_service.get_table_width,
        "gallery_width": list_post_service.gallery_width,
        "gallery_height": list_post_service.gallery_height,
        "prev_spt": list_post_service.prev_spt,
        "next_spt": list_post_service.next_spt,
    }

    return templates.TemplateResponse(f"/board/{board.bo_skin}/list_post.html", context)


@router.post("/list_delete/{bo_table}", dependencies=[Depends(validate_token)])
async def list_delete(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
    wr_ids: list = Form(..., alias="chk_wr_id[]"),
):
    """
    게시글을 일괄 삭제한다.
    """
    # 게시판 관리자 검증
    member = request.state.login_member
    mb_id = getattr(member, "mb_id", None)
    admin_type = get_admin_type(request, mb_id, board=board)
    if not admin_type:
        raise AlertException("게시판 관리자 이상 접근이 가능합니다.", 403)

    # 게시글 조회
    write_model = dynamic_create_write_table(bo_table)
    writes = db.scalars(
        select(write_model)
        .where(write_model.wr_id.in_(wr_ids))
    ).all()
    for write in writes:
        db.delete(write)
        # 원글 포인트 삭제
        if not delete_point(request, write.mb_id, board.bo_table, write.wr_id, "쓰기"):
            insert_point(request, write.mb_id, board.bo_write_point * (-1), f"{board.bo_subject} {write.wr_id} 글 삭제")
        
        # 파일 삭제
        BoardFileManager(board, write.wr_id).delete_board_files()

        # TODO: 댓글 삭제
    db.commit()

    # 최신글 캐시 삭제
    FileCache().delete_prefix(f'latest-{bo_table}')

    # TODO: 게시글 삭제시 같이 삭제해야할 것들 추가

    query_params = request.query_params
    url = f"/board/{bo_table}"
    return RedirectResponse(
        set_url_query_params(url, query_params), status_code=303)


@router.post("/move/{bo_table}")
async def move_post(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
    sw: str = Form(...),
    wr_ids: list = Form(..., alias="chk_wr_id[]"),
):
    """
    게시글 복사/이동
    """
    # 게시판 관리자 검증
    member = request.state.login_member
    mb_id = getattr(member, "mb_id", None)
    admin_type = get_admin_type(request, mb_id, board=board)
    if not admin_type:
        raise AlertException("게시판 관리자 이상 접근이 가능합니다.", 403)

    # 게시판 목록 조회
    query = select(Board).join(Group).order_by(Board.gr_id, Board.bo_order, Board.bo_table)
    # 관리자가 속한 게시판 목록만 조회
    if admin_type == "group":
        query = query.where(Group.gr_admin == mb_id)
    elif admin_type == "board":
        query = query.where(Board.bo_admin == mb_id)
    boards = db.scalars(query).all()

    context = {
        "request": request,
        "sw": sw,
        "act": "이동" if sw == "move" else "복사",
        "boards": boards,
        "current_board": board,
        "wr_ids": ','.join(wr_ids)
    }
    return templates.TemplateResponse("/board/move.html", context)


@router.post("/move_update/", dependencies=[Depends(validate_token)])
async def move_update(
    request: Request,
    db: db_session,
    origin_board: Annotated[Board, Depends(get_board)],
    origin_bo_table: str = Form(..., alias="bo_table"),
    sw: str = Form(...),
    wr_ids: str = Form(..., alias="wr_id_list"),
    target_bo_tables: list = Form(..., alias="chk_bo_table[]"),
):
    """
    게시글 복사/이동
    """
    config = request.state.config
    act = "이동" if sw == "move" else "복사"

    # 게시판관리자 검증
    member = request.state.login_member
    mb_id = getattr(member, "mb_id", None)
    admin_type = get_admin_type(request, mb_id, board=origin_board)
    if not admin_type:
        raise AlertException("게시판 관리자 이상 접근이 가능합니다.", 403)

    # 입력받은 정보를 토대로 게시글을 복사한다.
    write_model = dynamic_create_write_table(origin_bo_table)
    origin_writes = db.scalars(
        select(write_model)
        .where(write_model.wr_id.in_(wr_ids.split(',')))
    ).all()

    # 게시글 복사/이동 작업 반복
    file_cache = FileCache()
    for target_bo_table in target_bo_tables:
        for origin_write in origin_writes:
            target_write_model = dynamic_create_write_table(target_bo_table)
            target_write = target_write_model()

            # 복사/이동 로그 기록
            if not origin_write.wr_is_comment and config.cf_use_copy_log:
                nick = cut_name(request, member.mb_nick)
                log_msg = f"[이 게시물은 {nick}님에 의해 {datetime_format(datetime.now()) } {origin_board.bo_subject}에서 {act} 됨]"
                if "html" in origin_write.wr_option:
                    log_msg = f'<div class="content_{sw}">' + log_msg + '</div>'
                else:
                    log_msg = '\n' + log_msg

            # 게시글 복사
            initial_field = ["wr_id", "wr_parent"]
            for field in origin_write.__table__.columns.keys():
                if field in initial_field:
                    continue
                elif field == 'wr_content':
                    target_write.wr_content = origin_write.wr_content + log_msg
                elif field == 'wr_num':
                    target_write.wr_num = get_next_num(target_bo_table)
                else:
                    setattr(target_write, field, getattr(origin_write, field))

            if sw == "copy":
                target_write.wr_good = 0
                target_write.wr_nogood = 0
                target_write.wr_hit = 0
                target_write.wr_datetime = datetime.now()

            # 게시글 추가
            db.add(target_write)
            db.commit()
            # 부모아이디 설정
            target_write.wr_parent = target_write.wr_id
            db.commit()

            if sw == "move":
                # 최신글 이동
                db.execute(
                    update(BoardNew)
                    .where(BoardNew.bo_table == origin_board.bo_table, BoardNew.wr_id == origin_write.wr_id)
                    .values(bo_table=target_bo_table, wr_id=target_write.wr_id, wr_parent=target_write.wr_id)
                )
                # 게시글
                if not origin_write.wr_is_comment:
                    # 추천데이터 이동
                    db.execute(
                        update(BoardGood)
                        .where(BoardGood.bo_table == target_bo_table, BoardGood.wr_id == target_write.wr_id)
                        .values(bo_table=target_bo_table, wr_id=target_write.wr_id)
                    )
                    # 스크랩 이동
                    db.execute(
                        update(Scrap)
                        .where(Scrap.bo_table == target_bo_table, Scrap.wr_id == target_write.wr_id)
                        .values(bo_table=target_bo_table, wr_id=target_write.wr_id)
                    )
                # 기존 데이터 삭제
                db.delete(origin_write)
                db.commit()

            # 파일이 존재할 경우
            file_manager = BoardFileManager(origin_board, origin_write.wr_id)
            if file_manager.is_exist():
                if sw == "move":
                    file_manager.move_board_files(FILE_DIRECTORY, target_bo_table, target_write.wr_id)
                else:
                    file_manager.copy_board_files(FILE_DIRECTORY, target_bo_table, target_write.wr_id)

        # 최신글 캐시 삭제
        file_cache.delete_prefix(f'latest-{target_bo_table}')

    # 원본 게시판 최신글 캐시 삭제
    file_cache.delete_prefix(f'latest-{origin_bo_table}')

    context = {
        "request": request,
        "errors": f"해당 게시물을 선택한 게시판으로 {act} 하였습니다."
    }
    return templates.TemplateResponse("alert_close.html", context)


@router.get("/write/{bo_table}", dependencies=[Depends(check_group_access)])
async def write_form_add(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
    parent_id: int = Query(None)
):
    """
    게시글을 작성하는 form을 보여준다.
    """
    # 게시판 정보 조회
    board_config = BoardConfig(request, board)

    parent_write = None
    if parent_id:
        # 답글 작성권한 검증
        if not board_config.is_reply_level():
            raise AlertException("답변글을 작성할 권한이 없습니다.", 403)

        # 답글 생성가능여부 검증
        write_model = dynamic_create_write_table(bo_table)
        parent_write = db.get(write_model, parent_id)
        if not parent_write:
            raise AlertException("답변할 글이 존재하지 않습니다.", 404)

        generate_reply_character(board, parent_write)
    else:
        if not board_config.is_write_level():
            raise AlertException("글을 작성할 권한이 없습니다.", 403)

    # TODO: 포인트 검증

    # 게시판 제목 설정
    board.subject = board_config.subject
    # 게시판 에디터 설정
    request.state.use_editor = board.bo_use_dhtml_editor
    request.state.editor = board_config.select_editor

    # 게시판 관리자 확인
    member = request.state.login_member
    mb_id = getattr(member, "mb_id", None)
    admin_type = get_admin_type(request, mb_id, board=board)

    context = {
        "request": request,
        "categories": board_config.get_category_list(),
        "board": board,
        "write": None,
        "is_notice": True if admin_type and not parent_id else False,
        "is_html": board_config.is_html_level(),
        "is_secret": 1 if is_secret_write(parent_write) else board.bo_use_secret,
        "secret_checked": "checked" if is_secret_write(parent_write) else "",
        "is_mail": board_config.use_email,
        "recv_email_checked": "checked",
        "is_link": board_config.is_link_level(),
        "is_file": board_config.is_upload_level(),
        "is_file_content": bool(board.bo_use_file_content),
        "files": BoardFileManager(board).get_board_files_by_form(),
        "is_use_captcha": board_config.use_captcha,
        "write_min": board_config.write_min,
        "write_max": board_config.write_max,
    }
    return templates.TemplateResponse(
        f"/board/{board.bo_skin}/write_form.html", context)


@router.get("/write/{bo_table}/{wr_id}", dependencies=[Depends(check_group_access)])
async def write_form_edit(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    wr_id: int = Path(...)
):
    """
    게시글을 작성하는 form을 보여준다.
    """
    board_config = BoardConfig(request, board)

    # 게시판 관리자 확인
    member = request.state.login_member
    mb_id = getattr(member, "mb_id", None)
    admin_type = get_admin_type(request, mb_id, board=board)

    # 게시판 수정 권한
    if not board_config.is_write_level():
        raise AlertException("글을 수정할 권한이 없습니다.", 403)
    if not board_config.is_modify_by_comment(wr_id):
        raise AlertException(f"이 글과 관련된 댓글이 {board.bo_count_modify}건 이상 존재하므로 수정 할 수 없습니다.", 403)

    if not admin_type:
        # 익명 글
        if not write.mb_id:
            if not request.session.get(f"ss_edit_{bo_table}_{wr_id}"):
                query_params = request.query_params
                url = f"/bbs/password/update/{bo_table}/{write.wr_id}"
                return RedirectResponse(
                    set_url_query_params(url, query_params), status_code=303)
        # 회원 글
        elif write.mb_id and not is_owner(write, mb_id):
            raise AlertException("본인 글만 수정할 수 있습니다.", 403)

    # 게시판 제목 설정
    board.subject = board_config.subject
    # 게시판 에디터 설정
    request.state.use_editor = board.bo_use_dhtml_editor
    request.state.editor = board_config.select_editor

    # HTML 설정
    html_checked = ""
    html_value = ""
    if "html1" in write.wr_option:
        html_checked = "checked"
        html_value = "html1"
    elif "html2" in write.wr_option:
        html_checked = "checked"
        html_value = "html2"

    context = {
        "request": request,
        "categories": board_config.get_category_list(),
        "board": board,
        "write": write,
        "is_notice": True if not write.wr_reply and admin_type else False,
        "notice_checked": "checked" if board_config.is_board_notice(wr_id) else "",
        "is_html": board_config.is_html_level(),
        "html_checked": html_checked,
        "html_value": html_value,
        "is_secret": 1 if is_secret_write(write) else board.bo_use_secret,
        "secret_checked": "checked" if is_secret_write(write) else "",
        "is_mail": board_config.use_email,
        "recv_email_checked": "checked" if "mail" in write.wr_option else "",
        "is_link": board_config.is_link_level(),
        "is_file": board_config.is_upload_level(),
        "is_file_content": bool(board.bo_use_file_content),
        "files": BoardFileManager(board, wr_id).get_board_files_by_form(),
        "is_use_captcha": False,
        "write_min": board_config.write_min,
        "write_max": board_config.write_max,
    }
    return templates.TemplateResponse(
        f"/board/{board.bo_skin}/write_form.html", context)


@router.post("/write_update/{bo_table}", dependencies=[Depends(validate_token), Depends(check_group_access)])
async def create_post(
    request: Request,
    db: db_session,
    form_data: Annotated[WriteForm, Depends()],
    member: Annotated[Member, Depends(check_login_member)],
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
    parent_id: int = Form(None),
    notice: bool = Form(False),
    secret: str = Form(""),
    html: str = Form(""),
    mail: str = Form(""),
    uid: str = Form(None),
    files: List[UploadFile] = File(None, alias="bf_file[]"),
    file_content: list = Form(None, alias="bf_content[]"),
    file_dels: list = Form(None, alias="bf_file_del[]"),
    recaptcha_response: str = Form("", alias="g-recaptcha-response"),
):
    create_post_service = CreatePostService(
        request, db, bo_table, board, member
    )
    create_post_service.validate_captcha(recaptcha_response)
    create_post_service.validate_write_delay()
    create_post_service.validate_secret_board(secret, html, mail)
    create_post_service.validate_post_content(form_data.wr_subject)
    create_post_service.validate_post_content(form_data.wr_content)
    create_post_service.is_write_level()
    create_post_service.arrange_data(form_data, secret, html, mail)
    write = create_post_service.save_write(parent_id, form_data)
    insert_board_new(bo_table, write)
    create_post_service.add_point(write)
    create_post_service.send_write_mail_(write, parent_id)
    create_post_service.set_notice(write.wr_id, notice)
    set_write_delay(create_post_service.request)
    create_post_service.delete_auto_save(uid)
    create_post_service.save_secret_session(write.wr_id, secret)
    create_post_service.upload_files(write, files, file_content, file_dels)
    create_post_service.delete_cache()
    redirect_url = create_post_service.get_redirect_url(write)
    db.commit()
    return RedirectResponse(redirect_url, status_code=303)


@router.post("/write_update/{bo_table}/{wr_id}", dependencies=[Depends(validate_token), Depends(check_group_access)])
async def update_post(
    request: Request,
    db: db_session,
    member: Annotated[Member, Depends(get_login_member)],
    board: Annotated[Board, Depends(get_board)],
    bo_table: str = Path(...),
    wr_id: str = Path(...),
    notice: bool = Form(False),
    secret: str = Form(""),
    html: str = Form(""),
    mail: str = Form(""),
    form_data: WriteForm = Depends(),
    uid: str = Form(None),
    files: List[UploadFile] = File(None, alias="bf_file[]"),
    file_content: list = Form(None, alias="bf_content[]"),
    file_dels: list = Form(None, alias="bf_file_del[]"),
):
    update_post_service = UpdatePostService(
        request, db, bo_table, board, member, wr_id,
    )
    write = get_write(db, bo_table, wr_id)
    update_post_service.validate_restrict_comment_count()
    update_post_service.validate_secret_board(secret, html, mail)
    update_post_service.validate_post_content(form_data.wr_subject)
    update_post_service.validate_post_content(form_data.wr_content)
    update_post_service.arrange_data(form_data, secret, html, mail)
    update_post_service.save_secret_session(wr_id, secret)
    update_post_service.save_write(write, form_data)
    update_post_service.set_notice(write.wr_id, notice)
    update_post_service.delete_auto_save(uid)
    update_post_service.upload_files(write, files, file_content, file_dels)
    update_post_service.update_children_category(form_data)
    update_post_service.delete_cache()
    redirect_url = update_post_service.get_redirect_url(write)
    db.commit()

    return RedirectResponse(redirect_url, status_code=303)


@router.get("/{bo_table}/{wr_id}", dependencies=[Depends(check_group_access)])
async def read_post(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    member: Annotated[Member, Depends(check_login_member)],
    bo_table: str = Path(...),
    wr_id: int = Path(...),
):
    read_post_service = ReadPostService(request, db, bo_table, board, wr_id, write, member)
    read_post_service.request.state.editor = read_post_service.select_editor
    read_post_service.validate_secret_with_session()
    read_post_service.validate_repeat_with_session()
    read_post_service.block_read_comment()
    read_post_service.validate_read_level()
    read_post_service.check_scrap()
    read_post_service.check_is_good()
    prev, next = read_post_service.get_prev_next()
    db.commit()
    context = {
        "request": read_post_service.request,
        "board": board,
        "write": write,
        "write_list": read_post_service.write_list,
        "prev": prev,
        "next": next,
        "images": read_post_service.images,
        "files": read_post_service.images + read_post_service.normal_files,
        "links": read_post_service.get_links(),
        "comments": read_post_service.get_comments(),
        "is_write": read_post_service.is_write_level(),
        "is_reply": read_post_service.is_reply_level(),
        "is_comment_write": read_post_service.is_comment_level(),
    }
    return templates.TemplateResponse(f"/board/{board.bo_skin}/read_post.html", context)


# 게시글 삭제
@router.get("/delete/{bo_table}/{wr_id}", dependencies=[Depends(validate_token)])
async def delete_post(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    wr_id: int = Path(...),
):
    """
    게시글을 삭제한다.
    """
    delete_post_service = DeletePostService(
        request, db, bo_table, board, wr_id, write, request.state.login_member
    )
    delete_post_service.delete_write()
    query_params = remove_query_params(request, "token")
    return RedirectResponse(set_url_query_params(f"/board/{bo_table}", query_params), status_code=303)


@router.get("/{bo_table}/{wr_id}/download/{bf_no}", dependencies=[Depends(check_group_access)])
async def download_file(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    wr_id: int = Path(...),
    bf_no: int = Path(...),
):
    """첨부파일 다운로드

    Args:
        db (Session): DB 세션. Depends로 주입
        bo_table (str): 게시판 테이블명
        wr_id (int): 게시글 아이디
        bf_no (int): 파일 순번

    Raises:
        AlertException: 파일이 존재하지 않을 경우

    Returns:
        FileResponse: 파일 다운로드
    """
    config = request.state.config
    board_config = BoardConfig(request, board)

    if not board_config.is_download_level():
        raise AlertException("다운로드 권한이 없습니다.", 403)

    # 파일 정보 조회
    file_manager = BoardFileManager(board, wr_id)
    board_file = file_manager.get_board_file(bf_no)
    if not board_file:
        raise AlertException("파일이 존재하지 않습니다.", 404)

    # 회원 정보
    member = request.state.login_member
    mb_id = getattr(member, "mb_id", None)

    # 게시물당 포인트가 한번만 차감되도록 세션 설정
    session_name = f"ss_down_{bo_table}_{wr_id}"
    if not request.session.get(session_name):
        # 포인트 검사
        if config.cf_use_point:
            download_point = board.bo_download_point
            if not board_config.is_download_point(write):
                point = number_format(abs(download_point))
                message = f"파일 다운로드에 필요한 포인트({point})가 부족합니다."
                if not member:
                    message += f"\\n로그인 후 다시 시도해주세요."

                raise AlertException(message, 403)
            else:
                insert_point(request, mb_id, download_point, f"{board.bo_subject} {write.wr_id} 파일 다운로드", board.bo_table, write.wr_id, "다운로드")

        request.session[session_name] = True

    download_session_name = f"ss_down_{bo_table}_{wr_id}_{board_file.bf_no}"
    if not request.session.get(download_session_name):
        # 다운로드 횟수 증가
        file_manager.update_download_count(board_file)
        # 파일 다운로드 세션 설정
        request.session[download_session_name] = True

    return FileResponse(board_file.bf_file, filename=board_file.bf_source)


@router.post(
        "/write_comment_update/{bo_table}",
        dependencies=[Depends(validate_token), Depends(check_group_access)])
async def write_comment_update(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    form: WriteCommentForm = Depends(),
    recaptcha_response: str = Form("", alias="g-recaptcha-response"),
):
    """
    댓글 등록/수정
    """
    member = request.state.login_member

    create_comment_service = CreateCommentService(
        request, db, bo_table, board, member
    )

    if form.w == "c":
        #댓글 생성
        if not member:
            # 비회원은 Captcha 유효성 검사
            await validate_captcha(request, recaptcha_response)
        create_comment_service.validate_write_delay()
        create_comment_service.validate_comment_level()
        create_comment_service.validate_point()
        create_comment_service.validate_post_content(form.wr_content)
        comment = create_comment_service.save_comment(form, write)
        create_comment_service.add_point(comment)
        create_comment_service.send_write_mail_(comment, write)
        insert_board_new(bo_table, comment)
        set_write_delay(request)
    elif form.w == "cu":
        # 댓글 수정
        write_model = create_comment_service.write_model
        comment = db.get(write_model, form.comment_id)
        if not comment:
            raise AlertException(f"{form.comment_id} : 존재하지 않는 댓글입니다.", 404)

        create_comment_service.validate_post_content(form.wr_content)
        comment.wr_content = create_comment_service.get_cleaned_data(form.wr_content)
        comment.wr_option = form.wr_secret or "html1"
        comment.wr_last = create_comment_service.g5_instance.get_wr_last_now(write_model.__tablename__)
    db.commit()
    redirect_url = create_comment_service.get_redirect_url(write)
    return RedirectResponse(redirect_url, status_code=303)


@router.get("/delete_comment/{bo_table}/{wr_id}", dependencies=[Depends(validate_token)])
async def delete_comment(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    comment: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    comment_id: int = Path(..., alias="wr_id"),
):
    """
    댓글 삭제
    """
    delete_comment_service = DeleteCommentService(
        request, db, bo_table, board, comment_id, comment, request.state.login_member
    )
    delete_comment_service.check_authority()
    delete_comment_service.delete_comment()

    # request.query_params에서 token 제거
    query_params = remove_query_params(request, "token")
    url = f"/board/{bo_table}/{comment.wr_parent}"
    return RedirectResponse(
        set_url_query_params(url, query_params), status_code=303)


@router.get("/{bo_table}/{wr_id}/link/{no}")
async def link_url(
    request: Request,
    db: db_session,
    board: Annotated[Board, Depends(get_board)],
    write: Annotated[WriteBaseModel, Depends(get_write)],
    bo_table: str = Path(...),
    wr_id: int = Path(...),
    no: int = Path(...)
):
    """
    게시글에 포함된 링크이동
    """
    # 링크정보 조회
    url = getattr(write, f"wr_link{no}")
    if not url:
        raise AlertException("링크가 존재하지 않습니다.", 404)

    # 링크 세션 설정
    link_session_name = f"ss_link_{bo_table}_{wr_id}_{no}"
    if not request.session.get(link_session_name):
        # 링크 횟수 증가
        link_hit = getattr(write, f"wr_link{no}_hit", 0) + 1
        setattr(write, f"wr_link{no}_hit", link_hit)
        db.commit()
        request.session[link_session_name] = True

    # url에 http가 없으면 붙여줌
    if not url.startswith("http"):
        url = "http://" + url

    # 새 창의 외부 URL로 이동
    return RedirectResponse(url, status_code=303)