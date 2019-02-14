import concurrent.futures
import grpc
import logging
import os
import sys
import time

from manager import Filesync

import filesync_pb2
import filesync_pb2_grpc

FILES_DIR = os.getenv('SYNC_DIR')
GS_URL = os.getenv('GS_URL')
PORT = os.getenv('CONTROL_PORT')
SYNC_PERIOD = os.getenv('SYNC_PERIOD')

EMPTY = filesync_pb2.Empty()


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.getLogger('sh').setLevel(logging.WARNING)
    if not (FILES_DIR and GS_URL and PORT and SYNC_PERIOD):
        print('These ENV vars must be set: FILES_DIR GS_URL PORT SYNC_PERIOD')
        sys.exit(1)
    address = '0.0.0.0:10000'
    server = make_server(address)
    server.start()
    print('filesync component serving on 0.0.0.0:%s' % PORT)

    try:
        while True:
            time.sleep(60 * 60 * 24)
    except KeyboardInterrupt:
        server.stop(0)


def make_server(address):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    filesync_pb2_grpc.add_FilesyncServicer_to_server(
        FilesyncServicer(), server)
    server.add_insecure_port(address)
    return server


class FilesyncServicer(filesync_pb2_grpc.FilesyncServicer):

    def __init__(self):
        self.fs = Filesync(GS_URL, FILES_DIR, SYNC_PERIOD)
        super(filesync_pb2_grpc.FilesyncServicer, self).__init__()
        self.fs.begin()

    def Info(self, request, context):
        return state_to_pb(self.fs.get_state())

    def Restart(self, request, context):
        self.fs.abort_timer()
        self.fs.abort_process()
        self.fs.start_process()
        return state_to_pb(self.fs.get_state())

    def Start(self, request, context):
        if self.fs.proc is None:
            self.fs.abort_timer()
            self.fs.start_process()

        return state_to_pb(self.fs.get_state())

    def Abort(self, request, context):
        if self.fs.proc is not None:
            self.fs.abort_process()
        return state_to_pb(self.fs.get_state())

    def Wait(self, request, context):
        self.fs.wait_until_next_complete()
        return state_to_pb(self.fs.get_state())

    def Watch(self, request, context):
        for line in self.fs.stream():
            yield filesync_pb2.Line(line=line.rstrip())


def state_to_pb(state):
    return filesync_pb2.FilesyncInformation(
        syncing_now=state['runningNow'],
        syncs_completed=state['runsComplete'],
        seconds_since_last_complete=state['secondsSinceLastComplete'],
        seconds_until_next_start=state['secondsUntilNextStart'],
        seconds_last_duration=state['secondsLastDuration'],
        seconds_current_duration=state['secondsCurrentDuration'],
    )

if __name__ == '__main__':
    main()
