import logging
import os
import sh
import threading
import time

OUTPUT_FILE_NAME = 'sync-output.log'

log = logging.getLogger('filesync')


class Filesync(object):

    def __init__(self, gs_url, workdir, period):
        self.gs_url = gs_url
        self.period = int(period)
        self.workdir = workdir
        self.outfile = os.path.join(workdir, OUTPUT_FILE_NAME)
        self.setup_cmd = sh.Command('bin/setup.sh').bake(
            _cwd=workdir,
        )
        self.sync_cmd = sh.Command('bin/sync.sh').bake(
            gs_url,
            _cwd=workdir,
            _iter=True,
            _done=self.proc_done,
            _err_to_out=True,
            _no_pipe=True,
            _bg=True,
        )

        self.lock = threading.RLock()
        self.runs_complete = 0
        self.proc = None
        self.timer = None

        self.time_last_start = None
        self.time_last_done = None
        self.time_current_start = None
        self.time_next_start = None

    def get_state(self):
        with self.lock:
            now = time.time()
            t_next = t_last = t_ldur = t_cdur = None
            if self.time_next_start:
                t_next = int(self.time_next_start - now)
            if self.time_last_done:
                t_last = int(now - self.time_last_done)
            if self.time_last_start and self.time_last_done:
                t_ldur = int(self.time_last_done - self.time_last_start)
            if self.time_current_start:
                t_cdur = int(now - self.time_current_start)
            return {
                'runsComplete': self.runs_complete,
                'runningNow': self.proc is not None,
                'secondsUntilNextStart': t_next,
                'secondsSinceLastComplete': t_last,
                'secondsLastDuration': t_ldur,
                'secondsCurrentDuration': t_cdur,
            }

    def begin(self):
        log.info('Starting Filesync management')
        if not os.path.exists(self.workdir):
            log.info('Creating working directory %r', self.workdir)
            os.makedirs(self.workdir)
        self.setup_cmd()
        self.start_process()

    def wait_until_next_complete(self):
        current_run = self.runs_complete
        while self.runs_complete == current_run:
            time.sleep(0.25)

    def stream(self):
        current_run = self.runs_complete
        while not os.path.exists(self.outfile):
            time.sleep(0.25)

        with open(self.outfile, 'r') as f:
            while True:
                if self.runs_complete != current_run:
                    break
                line = f.readline()
                if line:
                    yield line
                else:
                    time.sleep(0.25)

        yield '<END OF STREAM>\n'

    def start_process(self):
        log.info('Starting sync of %s', self.gs_url)
        with self.lock:
            self.time_current_start = time.time()
        self.proc = self.sync_cmd()

    def proc_done(self, _cmd, _success, _exit_code):
        log.info('Sync complete')
        with self.lock:
            self.time_last_done = time.time()
            self.time_last_start = self.time_current_start
            self.time_current_start = None
            self.runs_complete += 1
            self.proc = None
            os.remove(self.outfile)

        self.start_timer()

    def start_timer(self):
        now = time.time()
        time_to_next_sync = self.period - (now % self.period)
        log.info('Starting timer for %s seconds', int(time_to_next_sync))
        with self.lock:
            self.timer = threading.Timer(time_to_next_sync, self.timer_done)
            self.timer.start()
            self.time_next_start = now + time_to_next_sync

    def timer_done(self):
        log.info('Timer done')
        with self.lock:
            self.timer = None
            self.time_next_start = None
        self.start_process()

    def abort_process(self):
        with self.lock:
            if self.proc is not None:
                log.info('Aborting sync')
                self.proc.kill()
                log.warning(
                    "There may now be a stacktrace for"
                    " SignalException_SIGKILL. This is fine, there's"
                    " just no way easy to hide it. Move along.")

    def abort_timer(self):
        with self.lock:
            if self.timer is not None:
                log.info('Aborting timer')
                self.timer.cancel()
                self.timer = None
