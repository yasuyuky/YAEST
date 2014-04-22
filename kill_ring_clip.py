import sublime_plugin, sublime
import sys

PY2 = sys.version_info < (3, 0)
if not PY2: xrange = range

class KillRing:
    def __init__(self):
        self.limit = 16
        self.buffer = []
        self.sealed = True
        self.blocker = 0

    def top(self):
        return self.buffer[-1] if self.buffer else ''

    def seal(self):
        if self.blocker == 0:
            self.sealed = True
        else:
            self.blocker -= 1

    def increment_brocker(self):
        self.blocker += 1

    def push(self, texts):
        self.buffer.append(texts)
        if len(self.buffer) > self.limit: del self.buffer[0]
        self.sealed = False
        sublime.set_clipboard('\n'.join(texts))

    def put(self, texts, forward):
        if self.sealed or not self.buffer:
            self.push(texts)
        else:
            self.update(texts, forward)

    def update(self,texts,forward):
        concat = lambda t:t[0]+(t[1] or '') if forward else (t[1] or '') + t[0]
        new_texts = [concat(t) for t in zip(self.buffer[-1],texts)]
        del self.buffer[-1]
        self.push(new_texts)

    def __len__(self):
        return len(self.buffer)


kill_ring = KillRing()


class YankAnotherCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        kill_ring.seal()
        texts = kill_ring.top()
        regions = [r for r in self.view.sel()]
        if len(texts) == len(regions):
            for r,t in reversed(zip(regions,texts)):
                num = self.view.insert(edit, r.begin(), t)
                self.view.erase(edit, sublime.Region(r.begin()+num, r.end()+num))
        else:
            t = '\n'.join(texts)
            for r in reversed(regions):
                num = self.view.insert(edit, r.begin(), t)
                self.view.erase(edit, sublime.Region(r.begin()+num, r.end()+num))

    def is_enabled(self):
        return len(kill_ring) > 0


class AddToKillRingClipCommand(sublime_plugin.TextCommand):
    def run(self, edit, forward):
        delta = 1
        if not forward:
            delta = -1
        texts = []
        regions = []
        for s in self.view.sel():
            if s.empty(): s = sublime.Region(s.a, s.a + delta)
            texts.append(self.view.substr(s))

        clip = '\n'.join(texts)
        kill_ring.put(texts, forward)


class BlockSealingCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for _ in self.view.sel():
            kill_ring.increment_brocker()


class CursorListener(sublime_plugin.EventListener):
    def on_selection_modified(self, view):
        kill_ring.seal()


class ClipboardListener(sublime_plugin.EventListener):
    def on_activated(self, view):
        clip = sublime.get_clipboard()
        if '\n'.join(kill_ring.top()) != clip:
            kill_ring.push([clip])
            print("kill ring overridden", clip)

