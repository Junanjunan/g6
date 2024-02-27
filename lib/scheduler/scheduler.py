import os
import time
from typing import Set, List, Tuple
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from .scheduled_jobs import cron_jobs, interval_jobs, date_jobs


class Scheduler:
    """
    예약 작업을 관리할 스케줄러 생성
    https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html

    lib/scheduler/scheduled_jobs의 
    cron_schedules.py, interval_schedules.py, date_schedules.py에 작업을 등록합니다.
      cron_schedules.py에는 매일 특정 시간에 반복할 작업을 등록합니다.
      interval_schedules.py에는 일정 간격으로 반복할 작업을 등록합니다.
      date_schedules.py에는 특정 날짜와 시간에 한 번만 실행할 작업을 등록합니다.
    """
    TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Seoul")
    is_scheduler_paused = False
    job_ids = set()
    job_ids_file_path = "data/job_ids.txt"
    total_trigger_jobs = {
        "cron": cron_jobs,
        "interval": interval_jobs,
        "date": date_jobs,
    }

    def __init__(self) -> None:
        """
        스케줄러를 생성하고 시작합니다.
        기본적으로 BackgroundScheduler를 사용합니다.
        """
        self.background_scheduler = BackgroundScheduler(timezone=Scheduler.TIME_ZONE)
        self.background_scheduler.start()

    def add_jobs(self, trigger_type: str, scheduler_type: str = "background") -> None:
        """
        트리거별 작업을 스케줄러에 등록합니다.
        """
        if scheduler_type == "background":
            scheduler = self.background_scheduler
        trigger_jobs = Scheduler.total_trigger_jobs[trigger_type]

        for job_info in trigger_jobs:
            job_id, job_func, expression = job_info.values()
            scheduler.add_job(trigger=trigger_type, func=job_func, **expression)
            Scheduler.job_ids.add(job_id)

    def add_all_jobs(self) -> None:
        """
        모든 트리거들의 작업을 스케줄러에 모두 등록합니다.
        """
        for trigger_type in Scheduler.total_trigger_jobs.keys():
            self.add_jobs(trigger_type=trigger_type)

    def remove_all_background_jobs(self) -> None:
        """
        백그라운드 스케줄러의 등록된 작업을 삭제합니다.
        """
        self.background_scheduler.remove_all_jobs()

    def pause_background_scheduler(self) -> None:
        """
        백그라운드 스케줄러를 일시 정지합니다.
        """
        self.background_scheduler.pause()
        Scheduler.is_scheduler_paused = True

    def resume_background_scheduler(self) -> None:
        """
        일시 정지된 백그라운드 스케줄러를 재시작합니다.
        """
        self.background_scheduler.resume()
        Scheduler.is_scheduler_paused = False

    def get_job_status_list(self) -> Tuple[List, List]:
        """
        예약 중인 작업과 일시 정지된 작업 리스트를 반환합니다.
        """
        all_jobs = self.background_scheduler.get_jobs()
        running_jobs, paused_jobs = [], []
        for job in all_jobs:
            if job.next_run_time:
                running_jobs.append(job)
            else:
                paused_jobs.append(job)
        return running_jobs, paused_jobs

    @staticmethod
    def read_file_job_ids() -> Set[str]:
        """
        파일에 저장된 job_ids를 읽어옵니다.
        """
        if os.path.exists(Scheduler.job_ids_file_path):
            with open(Scheduler.job_ids_file_path, 'r') as file:
                Scheduler.job_ids = {line.strip() for line in file}
        return Scheduler.job_ids

    @staticmethod
    def write_file_job_ids(job_ids: Set) -> None:
        """
        job_ids를 파일에 저장합니다.
        """
        with open(Scheduler.job_ids_file_path, 'w') as file:
            for job_id in job_ids:
                file.write(job_id + '\n')

    @staticmethod
    def remove_file_job_ids() -> None:
        """
        job_ids 파일을 삭제합니다.
        """
        if os.path.exists(Scheduler.job_ids_file_path):
            os.remove(Scheduler.job_ids_file_path)

    def run_scheduler(self) -> None:
        """
        - 스케줄러를 실행합니다.
        - --workers 옵션으로 여러 프로세스 실행시 
          예약 작업이 중복 등록되는 것을 방지하기 위해 등록된 작업 id를 임시 파일로 저장합니다.
          임시 파일 생성 여부를 확인하여 작업 등록 여부를 결정합니다.
        - 서버 실행후 모든 작업을 등록하고 설정한 시간(30초) 후에 임시 파일을 삭제합니다.
        """
        time.sleep(0.1)
        file_job_ids = Scheduler.read_file_job_ids()
        if file_job_ids:
            return

        run_date = datetime.now() + timedelta(seconds=30)
        self.add_all_jobs()
        self.background_scheduler.add_job(
            trigger="date", func=Scheduler.remove_file_job_ids, run_date=run_date
        )
        Scheduler.write_file_job_ids(Scheduler.job_ids)