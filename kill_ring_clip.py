import sublime_plugin, sublime
import sys

PY2 = sys.version_info < (3, 0)
if not PY2: xrange = range

class KillRing:
    def __init__(self):
        self.limit = 16
        self.buffer = [None for i in xrange(self.limit)]
        self.head = 0
        self.len = 0
        self.kill_points = []
        self.kill_id = 0

    def top(self):
        return self.buffer[self.head]

    def seal(self):
        self.kill_points = []
        self.kill_id = 0

    def push(self, text):
        self.head = (self.head + 1) % self.limit
        self.buffer[self.head] = text
        if self.len < self.limit:
            self.len += 1

    def add(self, view_id, text, regions, forward):
        if view_id != self.kill_id:
            # view has changed, ensure the last kill ring entry will not be
            # appended to
            self.seal()

        begin_points = []
        end_points = []
        for r in regions:
            begin_points.append(r.begin())
            end_points.append(r.end())

        if forward:
            compare_points = begin_points
        else:
            compare_points = end_points

        if compare_points == self.kill_points:
            # Selection hasn't moved since the last kill, append/prepend the
            # text to the current entry
            if forward:
                self.buffer[self.head] = self.buffer[self.head] + text
            else:
                self.buffer[self.head] = text + self.buffer[self.head]
        else:
            # Create a new entry in the kill ring for this text
            self.push(text)

        self.kill_points = begin_points
        self.kill_id = view_id

    def get(self, index):
        return self.buffer[(self.head + index) % self.limit]

    def __len__(self):
        return self.len

kill_ring = KillRing()

class YankAnotherCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        kill_ring.seal()
        text = kill_ring.top()

        lines = text.splitlines()

        regions = [r for r in self.view.sel()]
        regions.reverse()

        if len(regions) > 1 and len(regions) == len(lines):
            # insert one line from the top of the kill ring at each
            # corresponding selection
            lines.reverse()
            for i in xrange(len(regions)):
                s = regions[i]
                line = lines[i]
                num = self.view.insert(edit, s.begin(), line)
                self.view.erase(edit, sublime.Region(s.begin() + num,
                    s.end() + num))
        else:
            # insert the top of the kill ring at each selection
            for s in regions:
                num = self.view.insert(edit, s.begin(), text)
                self.view.erase(edit, sublime.Region(s.begin() + num,
                    s.end() + num))

    def is_enabled(self):
        return len(kill_ring) > 0

last_clip=''

class AddToKillRingClipCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward):
        global last_clip
        delta = 1
        if not forward:
            delta = -1

        text = []
        regions = []
        for s in self.view.sel():
            if s.empty():
                s = sublime.Region(s.a, s.a + delta)
            text.append(self.view.substr(s))
            regions.append(s)

        clip = '\n'.join(text)
        kill_ring.add(self.view.id(), clip, regions, forward)
        sublime.set_clipboard(clip)
        last_clip = kill_ring.top()

class ClipboardListener(sublime_plugin.EventListener):

    def on_selection_modified(self, view):
        global last_clip
        clip = sublime.get_clipboard()
        if clip != last_clip:
            print("kill ring overridden", clip)
            kill_ring.add(view.id(), clip, view.sel(), 1)
            last_clip = clip
