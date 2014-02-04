from __future__ import print_function

import signal
import subprocess
import sys
from datetime import datetime
from threading import Thread
from Queue import Queue, Empty


#
# This code comes from Honcho.  Didn't need the whole Honcho
#   setup, so I just swiped this part which is what the build
#   pack utils library needs.
#
#  https://github.com/nickstenning/honcho
#
# I've modified parts to fit better with this module.
#


def _enqueue_output(proc, queue):
    if not proc.quiet:
        for line in iter(proc.stdout.readline, b''):
            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError as e:
                queue.put((proc, e))
                continue
            if not line.endswith('\n'):
                line += '\n'
            queue.put((proc, line))
        proc.stdout.close()


class Process(subprocess.Popen):
    def __init__(self, cmd, name=None, quiet=False, *args, **kwargs):
        self.name = name
        self.quiet = quiet
        self.reader = None
        self.printer = None
        self.dead = False

        if self.quiet:
            self.name = "{0} (quiet)".format(self.name)

        defaults = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'shell': True,
            'bufsize': 1,
            'close_fds': True
        }
        defaults.update(kwargs)

        super(Process, self).__init__(cmd, *args, **defaults)


class ProcessManager(object):
    """
    Here's where the business happens. The ProcessManager multiplexes and
    pretty-prints the output from a number of Process objects, typically added
    using the add_process() method.

    Example:

        pm = ProcessManager()
        pm.add_process('name', 'ruby server.rb')
        pm.add_process('name', 'python worker.py')

        pm.loop()
    """
    def __init__(self):
        self.processes = []
        self.queue = Queue()
        self.system_printer = Printer(sys.stdout, name='system')
        self.returncode = None
        self._terminating = False

    def add_process(self, name, cmd, quiet=False):
        """
        Add a process to this manager instance:

        Arguments:

        name        - a human-readable identifier for the process
                      (e.g. 'worker'/'server')
        cmd         - the command-line used to run the process
                      (e.g. 'python run.py')
        """
        self.processes.append(Process(cmd, name=name, quiet=quiet))

    def loop(self):
        """
        Enter the main loop of the program. This will print the multiplexed
        output of all the processes in this ProcessManager to sys.stdout, and
        will block until all the processes have completed.

        If one process terminates, all the others will be terminated 
        and loop() will return.

        Returns: the returncode of the first process to exit, or 130 if
        interrupted with Ctrl-C (SIGINT)
        """
        self._init_readers()
        self._init_printers()

        for proc in self.processes:
            print("started with pid {0}".format(proc.pid), file=proc.printer)

        while True:
            try:
                proc, line = self.queue.get(timeout=0.1)
            except Empty:
                pass
            except KeyboardInterrupt:
                print("SIGINT received", file=sys.stderr)
                self.returncode = 130
                self.terminate()
            else:
                self._print_line(proc, line)

            for proc in self.processes:
                if not proc.dead and proc.poll() is not None:
                    print('process terminated', file=proc.printer)
                    proc.dead = True

                    # Set the returncode of the ProcessManager instance if not
                    # already set.
                    if self.returncode is None:
                        self.returncode = proc.returncode

                    self.terminate()

            if not self._process_count() > 0:
                break

        while True:
            try:
                proc, line = self.queue.get(timeout=0.1)
            except Empty:
                break
            else:
                self._print_line(proc, line)

        return self.returncode

    def terminate(self):
        """

        Terminate all the child processes of this ProcessManager, bringing the
        loop() to an end.

        """
        if self._terminating:
            return False

        self._terminating = True

        print("sending SIGTERM to all processes", file=self.system_printer)
        for proc in self.processes:
            if proc.poll() is None:
                print("sending SIGTERM to pid {0:d}".format(proc.pid), file=self.system_printer)
                proc.terminate()

        def kill(signum, frame):
            # If anything is still alive, SIGKILL it
            for proc in self.processes:
                if proc.poll() is None:
                    print("sending SIGKILL to pid {0:d}".format(proc.pid), file=self.system_printer)
                    proc.kill()

        signal.signal(signal.SIGALRM, kill)  # @UndefinedVariable
        signal.alarm(5)  # @UndefinedVariable

    def _process_count(self):
        return [p.poll() for p in self.processes].count(None)

    def _init_readers(self):
        for proc in self.processes:
            t = Thread(target=_enqueue_output, args=(proc, self.queue))
            t.daemon = True  # thread dies with the program
            t.start()

    def _init_printers(self):
        width = max(len(p.name) for p in filter(lambda x: not x.quiet, self.processes))
        width = max(width, len(self.system_printer.name))

        self.system_printer.width = width

        for proc in self.processes:
            proc.printer = Printer(sys.stdout,
                                   name=proc.name,
                                   width=width)

    def _print_line(self, proc, line):
        if isinstance(line, UnicodeDecodeError):
            print("UnicodeDecodeError while decoding line from process {0:s}".format(proc.name), file=self.system_printer)
        else:
            print(line, end='', file=proc.printer)


class Printer(object):
    def __init__(self, output=sys.stdout, name='unknown', width=0):
        self.output = output
        self.name = name
        self.width = width

        self._write_prefix = True

    def write(self, *args, **kwargs):
        new_args = []

        for arg in args:
            lines = arg.split('\n')
            lines = [self._prefix() + l if l else l for l in lines]
            new_args.append('\n'.join(lines))

        self.output.write(*new_args, **kwargs)

    def _prefix(self):
        time = datetime.now().strftime('%H:%M:%S')
        name = self.name.ljust(self.width)
        prefix = '{time} {name} | '.format(time=time, name=name)
        return prefix