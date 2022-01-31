import time

global_loglevel = 0


def strftime(t):
    return "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*t)


def make_logger(name):

    # ANSI color codes
    # fmt: off
    colors = {
        "black":    "\u001b[30m",
        "red":      "\u001b[31m",
        "green":    "\u001b[32m",
        "yellow":   "\u001b[33m",
        "blue":     "\u001b[34m",
        "magenta":  "\u001b[35m",
        "cyan":     "\u001b[36m",
        "white":    "\u001b[37m",
        "grey":     "\u001b[38;5;245m",
        "reset":    "\u001b[0m",
    }
    # fmt: on

    levelnames = ["debug", "info", "warning", "error"]
    levelcolors = ["grey", "white", "yellow", "red"]

    def _logger(msg, level=1):
        # if level is too large clamp it to error
        level = min(len(levelnames), level)

        if level < global_loglevel:
            return

        print(
            "{}{} {} [{}]: {}{}".format(
                colors[levelcolors[level]],
                strftime(time.gmtime()),
                levelnames[level].upper(),
                name,
                msg,
                colors["reset"],
            )
        )

    return _logger
