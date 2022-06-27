# This is a sample commands.py.  You can add your own commands here.
#
# Please refer to commands_full.py for all the default commands and a complete
# documentation.  Do NOT add them all here, or you may end up with defunct
# commands when upgrading ranger.

# A simple command for demonstration purposes follows.
# -----------------------------------------------------------------------------

from __future__ import (absolute_import, division, print_function)

import os
import re
from ranger.api.commands import Command
from threading import Thread

# Trash fix
# Source: https://github.com/ranger/ranger/blob/391f061cb0b0cfa8266c0651f2a6d948f22e01dd/ranger/config/commands.py#L776
class trash(Command):
    """:trash
    Tries to move the selection or the files passed in arguments (if any) to
    the trash, using rifle rules with label "trash".
    The arguments use a shell-like escaping.
    "Selection" is defined as all the "marked files" (by default, you
    can mark files with space or v). If there are no marked files,
    use the "current file" (where the cursor is)
    When attempting to trash non-empty directories or multiple
    marked files, it will require a confirmation.
    """

    allow_abbrev = False
    escape_macros_for_shell = True

    def execute(self):
        import shlex
        from functools import partial

        def is_directory_with_files(path):
            return os.path.isdir(path) and not os.path.islink(path) and len(os.listdir(path)) > 0

        if self.rest(1):
            file_names = shlex.split(self.rest(1))
            files = self.fm.get_filesystem_objects(file_names)
            if files is None:
                return
            many_files = (len(files) > 1 or is_directory_with_files(files[0].path))
        else:
            cwd = self.fm.thisdir
            tfile = self.fm.thisfile
            if not cwd or not tfile:
                self.fm.notify("Error: no file selected for deletion!", bad=True)
                return

            files = self.fm.thistab.get_selection()
            # relative_path used for a user-friendly output in the confirmation.
            file_names = [f.relative_path for f in files]
            many_files = (cwd.marked_items or is_directory_with_files(tfile.path))

        confirm = self.fm.settings.confirm_on_delete
        if confirm != 'never' and (confirm != 'multiple' or many_files):
            self.fm.ui.console.ask(
                "Confirm deletion of: %s (y/N)" % ', '.join(file_names),
                partial(self._question_callback, files),
                ('n', 'N', 'y', 'Y'),
            )
        else:
            # no need for a confirmation, just delete
            self._trash_files_catch_arg_list_error(files)

    def tab(self, tabnum):
        return self._tab_directory_content()

    def _question_callback(self, files, answer):
        if answer.lower() == 'y':
            self._trash_files_catch_arg_list_error(files)

    def _trash_files_catch_arg_list_error(self, files):
        """
        Executes the fm.execute_file method but catches the OSError ("Argument list too long")
        that occurs when moving too many files to trash (and would otherwise crash ranger).
        """
        try:
            self.fm.execute_file(files, label='trash')
        except OSError as err:
            if err.errno == 7:
                self.fm.notify("Error: Command too long (try passing less files at once)",
                               bad=True)
            else:
                raise
class empty(Command):
    """:empty
    Delete trash permanently
    """

    def execute(self):
        self.fm.run("rm -rf /home/adhiwena/.local/share/Trash/;rm -rf /home/data/.Trash-1000/")
        #  self.fm.run("rm -rf /home/data/.Trash-1000/")

class dragon(Command):
    """:dragon
    Drag and drop
    """
    
    def execute(self):
        th = Thread(target=self.dragondaemon, daemon=True)
        th.start()
        th.join()

    def dragondaemon(self):
        arguments = 'urxvtc -name dragon-term -e dragon-daemon {}'.format(" ".join(self.args[1:]))
        self.fm.execute_command(arguments)

# class quitall_custom(Command):
#     """:quitall_custom
#     quitall_custom
#     """

#     def _exit_no_work(self):
#         if self.fm.loader.has_work():
#             self.fm.notify('Not quitting: Tasks in progress: Use `quitall!` to force quit')
#         else:
#             # mytabs = str(self.fm.tabs)

#             if re.search('None', str(self.fm.tabs)):
#                 for tab in self.fm.tabs:
#                     self.fm.execute_console("tab_move 1")

#             mt = re.findall(r'\'(.*?)\'', str(self.fm.tabs))
#             # f = open("/home/adhiwena/.config/ranger/session", "w")
#             f = open("/home/adhiwena/out.txt", "w")
#             f.write(" ".join(mt))
#             f.close()
#             self.fm.exit()

#     def execute(self):
#         self._exit_no_work()
        
class quitall(Command):
    """:quitall

    Quits if there are no tasks in progress.
    """
    def _exit_with_save(self):
        self._exit_no_work()
                
    def _exit_no_work(self):
        if self.fm.loader.has_work():
            self.fm.notify('Not quitting: Tasks in progress: Use `quitall!` to force quit')
        else:
            self.fm.exit()

    def execute(self):
        self.fm.execute_console("save_tabs")
        self._exit_no_work()

class quit(Command):  # pylint: disable=redefined-builtin
    """:quit

    Closes the current tab, if there's more than one tab.
    Otherwise quits if there are no tasks in progress.
    """
    def _exit_no_work(self):
        if self.fm.loader.has_work():
            self.fm.notify('Not quitting: Tasks in progress: Use `quit!` to force quit')
        else:
            self.fm.exit()

    def execute(self):
        if len(self.fm.tabs) >= 2:
            self.fm.tab_close()
        else:
            self.fm.execute_console("quitall")
            # self._exit_no_work()

class save_tabs(Command):
    """:save_tabs
    """
    def execute(self):
        with open(self.fm.datapath('tabs'), 'w', encoding="utf-8") as fobj:
            fobj.write('\0'.join(v.path for t, v in self.fm.tabs.items()) + '\0\0')
        # self.fm.notify('Tabs saved!')