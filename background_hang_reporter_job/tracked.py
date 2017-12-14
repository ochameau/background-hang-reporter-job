class AllHangs(object):
    title = "All Hangs"

    @staticmethod
    def matches_hang(_):
        return True

class DevtoolsHangs(object):
    title = "Devtools Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "devtools/" in frame
                                         for lib, frame in stack)

class ToolboxHangs(object):
    title = "Toolbox Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "toolbox.js" in frame
                                         for lib, frame in stack)

class NetmonitorHangs(object):
    title = "Netmonitor Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "/netmonitor/" in frame
                                         for lib, frame in stack)

class NetmonitoriBatchingHangs(object):
    title = "Netmonitor Batching Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "netmonitor/src/middleware/batching" in frame
                                         for lib, frame in stack)

class NetmonitoriSelectorsHangs(object):
    title = "Netmonitor Selectors Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "netmonitor/src/selectors" in frame
                                         for lib, frame in stack)

class NetmonitoriComponentsHangs(object):
    title = "Netmonitor Components Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "netmonitor/src/components" in frame
                                         for lib, frame in stack)

class NetmonitorBackendHangs(object):
    title = "Netmonitor backend Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "/network-monitor.js" in frame
                                         for lib, frame in stack)

class ReactHangs(object):
    title = "React Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "devtools/" in frame and "vendor/react" in frame
                                         for lib, frame in stack)

class ImmutableHangs(object):
    title = "Immutable Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "devtools/" in frame and "vendor/immutable" in frame
                                         for lib, frame in stack)

class InspectorHangs(object):
    title = "Inspector Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "/inspector/" in frame
                                         for lib, frame in stack)

class ConsoleHangs(object):
    title = "Console Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "/webconsole/" in frame
                                         for lib, frame in stack)

class DebuggerHangs(object):
    title = "Debugger Hangs"

    @staticmethod
    def matches_hang(hang):
        #pylint: disable=unused-variable
        stack, duration, thread, runnable, process, annotations, build_date, platform = hang
        return stack is not None and any(frame is not None and "/debugger/" in frame
                                         for lib, frame in stack)

def get_tracked_stats():
    return [AllHangs, DevtoolsHangs, ToolboxHangs, NetmonitorHangs, NetmonitoriBatchingHangs, NetmonitoriSelectorsHangs, NetmonitoriComponentsHangs, NetmonitorBackendHangs, ReactHangs, ImmutableHangs, InspectorHangs, ConsoleHangs, DebuggerHangs]
