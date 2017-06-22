import sublime_plugin
import sublime
import subprocess
from .diff_match_patch import diff_match_patch
import json

class RufoPluginListener(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    settings = sublime.load_settings('Rufo.sublime-settings')
    if settings.get('auto_format') == None or settings.get('auto_format') == True:
      view.run_command('rufo_format')

class RufoFormatCommand(sublime_plugin.TextCommand):
  def is_enabled(self):
    caret = self.view.sel()[0].a
    syntax_name = self.view.scope_name(caret)
    return "source.ruby" in syntax_name

  def has_redo(self):
    cmd, args, repeat = self.view.command_history(1)
    return cmd != ''

  def run(self, edit):
    vsize = self.view.size()
    region = sublime.Region(0, vsize)
    src = self.view.substr(region)
    window = self.view.window()

    settings = sublime.load_settings('Rufo.sublime-settings')
    rufo_cmd = settings.get("rufo_cmd") or "rufo"
    with subprocess.Popen([rufo_cmd], stdin = subprocess.PIPE, stdout = subprocess.PIPE) as proc:
      proc.stdin.write(bytes(src, 'UTF-8'))
      proc.stdin.close()
      output = proc.stdout.read().decode('UTF-8')
      exit = proc.wait()

    pos = 0
    if exit == 0:
      if not self.has_redo():
        for op, text in diff_match_patch().diff_main(src, output):
          if op == diff_match_patch.DIFF_DELETE:
            self.view.erase(edit, sublime.Region(pos, pos + len(text)))
          if op == diff_match_patch.DIFF_INSERT:
            self.view.insert(edit, pos, text)
            pos += len(text)
          if op == diff_match_patch.DIFF_EQUAL:
            pos += len(text)