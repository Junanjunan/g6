- 오류 수정
    postgresql: visit table 관련 오류 (백그라운드에서 오류 발생)
    엑셀에 일부 남은 오류 수정
- DB 호환성 테스트 (PostgreSQL 및 5버전 MySQL - 변경된 사항들에 주기적으로 실행)

* 게시글의 첨부파일이 서버에서 지워져서 없는 경우 파일 다운로드시 오류 발생 - 링크로 직접 연결되어 있는 상태. 그냥 두어도 될지?


https://sir.kr/g6_pythonista/41
    import 에러


visit 테이블 자동 입력하는 오류?
    (psycopg2.errors.UndefinedFunction) operator does not exist: text < timestamp without time zone
    LINE 1: ...E concat(g6_visit.vi_date, ' ', g6_visit.vi_time) < '2023-07...
                                                                ^
    HINT:  No operator matches the given name and argument types. You might need to add explicit type casts.

    [SQL: DELETE FROM g6_visit WHERE concat(g6_visit.vi_date, %(concat_1)s, g6_visit.vi_time) < %(concat_2)s RETURNING g6_visit.vi_id]
    [parameters: {'concat_1': ' ', 'concat_2': datetime.datetime(2023, 7, 26, 10, 0, 0, 13353)}]
    (Background on this error at: https://sqlalche.me/e/20/f405)


is_prohibit_email
    cannot import name 'is_prohibit_email' from partially initialized module 'bbs.member_profile' (most likely due to a circular import) (/workspace/g6/bbs/member_profile.py)

    File "/workspace/g6/bbs/register.py", line 7, 
       in <module> from bbs.member_profile import ( File "/workspace/g6/main.py", line 49, in <module> from bbs.register import router as register_router File "/workspace/g6/bbs/member_profile.py", line 21, in <module> from main import app File "/workspace/g6/bbs/social.py", line 9, in <module> from bbs.member_profile import validate_nickname, validate_userid File "/workspace/g6/admin/admin_member.py", line 9, in <module> from bbs.social import SocialAuthService File "/workspace/g6/admin/admin.py", line 14, in <module> from admin.admin_member import router as admin_member_router File "/workspace/g6/main.py", line 45, in <module> from admin.admin import router as admin_router ImportError: cannot import name 'is_prohibit_email' from partially initialized module 'bbs.member_profile' (most likely due to a circular import) (/workspace/g6/bbs/member_profile.py)

  정의: bss/member_profile.py

  문제
    main.py > admin.py  > admin_member.py > bbs/social.py > bbs/member_profile.py > main

    결국 bbs/member_profile.py에서 main을 다시 불러온다...


 ** member_confirm 이라는 메소드가 없음... url_path_for("member_confirm")에서, member_confirm이 정의된 함수가 없음. 있다 없어진 건지 확인 필요 -> member_password?



https://wnsghks.gnupy.com/bbs/memo  ??
    File "templates/taeho/memo/memo_list.html", line 29, in block 'content'
        {% set is_read=(False if is_none_datetime(memo.me_read_datetime) else True) %}
    File "/home/ubuntu/gnu6/lib/common.py", line 844, in is_none_datetime
        if input_date.strftime("%Y")[:2] == "00":
    AttributeError: 'NoneType' object has no attribute 'strftime'





Then, Is that right?
MySQL database closed connection, so they have recovered all connection pools that before connected  that wait_timeout reached.
And The FastAPI SqlAlchemy didn't know, so the current overflow


https://stackoverflow.com/questions/29755228/sqlalchemy-mysql-lost-connection-to-mysql-server-during-query
first: pool_pre_ping=True... 이게 먹는것 같기도 하고...