import ctypes
import os
import time

import addons.shell as shell


class SuperScreenShotter:
    def main(self):
        libx11 = ctypes.cdll.LoadLibrary('libX11.so')
        libcairo = ctypes.cdll.LoadLibrary('libcairo.so')

        display = libx11.XOpenDisplay(None)
        screen = libx11.XDefaultScreen(display)
        root_window = libx11.XDefaultRootWindow(display)

        cairo_surface = libcairo.cairo_xlib_surface_create(
            display,
            root_window,
            libx11.XDefaultVisual(display, screen),
            libx11.XDisplayWidth(display, screen),
            libx11.XDisplayHeight(display, screen),
        )

        file_name = os.path.join(shell.home(), '{}.png'.format(int(time.time())))
        libcairo.cairo_surface_write_to_png(
            cairo_surface,
            file_name.encode(),
        )

        libcairo.cairo_surface_destroy(cairo_surface)


def main():
    SuperScreenShotter().main()


if __name__ == '__main__':
    main()
