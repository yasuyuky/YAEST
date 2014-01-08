from __future__ import print_function
import sublime_plugin
import sublime

transient_marks = [0]
transient_marked = False


class ToggleTransientMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global transient_marks, transient_marked
        transient_marked = not transient_marked
        transient_marks = []
        for s in self.view.sel():
            transient_marks.append(s.end())
        print("transient_marked:", transient_marked, transient_marks)


class CancelTransientMarkCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global transient_marks, transient_marked
        transient_marked = False
        new_points = []
        for s, t in zip(self.view.sel(), transient_marks):
            new_points.append(s.begin() if s.end() == t else s.end())
        self.view.sel().clear()
        for p in new_points:
            self.view.sel().add(sublime.Region(p))


class TransientMarkListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "transient_marked":
            return transient_marked
