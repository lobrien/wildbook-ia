from __future__ import division, print_function


def _on_ctrl_c(signal, frame):
    import sys
    print('Caught ctrl+c')
    sys.exit(0)

#-----------------------
# private init functions


def _init_signals():
    import signal
    signal.signal(signal.SIGINT, _on_ctrl_c)


def _reset_signals():
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # reset ctrl+c behavior


def _parse_args(**kwargs):
    from ibeis.dev import params
    params.parse_args(**kwargs)


def _init_gui():
    from ibeis.view import guitool, guiback
    print('[main] _init_gui()')
    guitool.init_qtapp()
    back = guiback.MainWindowBackend()
    back.show()
    return back


def _init_ibeis():
    print('[main] _init_ibeis()')
    from ibeis.control import IBEISControl
    ibs = IBEISControl.IBEISControl()
    return ibs


#-----------------------
# private loop functions


def _guitool_loop(main_locals):
    from ibeis.view import guitool
    from ibeis.dev import params
    back = main_locals['back']
    loop_freq = params.args.loop_freq
    guitool.qtapp_loop(back=back, frequency=loop_freq)
    return True


def _ipython_loop(main_locals):
    from ibeis.util import util_dbg
    embedded = util_dbg.inIPython()
    if not embedded:
        util_dbg.embed(parent_locals=main_locals)
        return True
    return False


def main(**kwargs):
    print('[main] ibeis.main_api.main()')
    from ibeis.util.util_inject import _inject_colored_exception_hook
    from ibeis.dev import params
    _inject_colored_exception_hook()
    _parse_args(**kwargs)
    _init_signals()
    if not params.args.nogui:
        back = _init_gui()
    ibs = _init_ibeis()
    main_locals = locals()
    return main_locals


def main_loop(main_locals):
    print('[main] ibeis.main_api.main_loop()')
    import sys
    from ibeis.dev import params
    exit_bit = True
    # Choose a main loop depending on params.args
    if params.args.cmd:
        exit_bit = _ipython_loop(main_locals)
    if exit_bit and not params.args.nogui:
        exit_bit = _guitool_loop(main_locals)
    _reset_signals()
    if exit_bit:
        # Exit cleanly if a main loop ran
        print('[main] ibeis clean exit')
        sys.exit(0)
    else:
        # Something else happened
        print('[main] ibeis unclean exit')
