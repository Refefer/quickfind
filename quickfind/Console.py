import os
import fcntl, termios, struct, os

def getDims():
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return
        return cr

    return ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2) or (25, 80)
