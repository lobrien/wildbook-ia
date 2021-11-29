# -*- coding: utf-8 -*-
# Autogenerated on 13:37:34 2015/12/30
# flake8: noqa
import logging
from wbia.algo import Config
from wbia.algo import detect
from wbia.algo import hots
from wbia.algo import smk
from wbia.algo import preproc
import utool

print, rrr, profile = utool.inject2(__name__, '[wbia.algo]')
logger = logging.getLogger('wbia')


def reassign_submodule_attributes(verbose=True):
    """
    why reloading all the modules doesnt do this I don't know
    """
    import sys

    if verbose and '--quiet' not in sys.argv:
        print('dev reimport')
    # Self import
    import wbia.algo

    # Implicit reassignment.
    seen_ = set([])
    for tup in IMPORT_TUPLES:
        if len(tup) > 2 and tup[2]:
            continue  # dont import package names
        submodname, fromimports = tup[0:2]
        submod = getattr(wbia.algo, submodname)
        for attr in dir(submod):
            if attr.startswith('_'):
                continue
            if attr in seen_:
                # This just holds off bad behavior
                # but it does mimic normal util_import behavior
                # which is good
                continue
            seen_.add(attr)
            setattr(wbia.algo, attr, getattr(submod, attr))


def reload_subs(verbose=True):
    """Reloads wbia.algo and submodules"""
    if verbose:
        print('Reloading submodules')
    rrr(verbose=verbose)

    def wrap_fbrrr(mod):
        def fbrrr(*args, **kwargs):
            """fallback reload"""
            if verbose:
                print('Trying fallback relaod for mod=%r' % (mod,))
            import imp

            imp.reload(mod)

        return fbrrr

    def get_rrr(mod):
        if hasattr(mod, 'rrr'):
            return mod.rrr
        else:
            return wrap_fbrrr(mod)

    def get_reload_subs(mod):
        return getattr(mod, 'reload_subs', wrap_fbrrr(mod))

    get_rrr(Config)(verbose=verbose)
    get_reload_subs(detect)(verbose=verbose)
    get_reload_subs(hots)(verbose=verbose)
    get_reload_subs(preproc)(verbose=verbose)
    rrr(verbose=verbose)
    try:
        # hackish way of propogating up the new reloaded submodule attributes
        reassign_submodule_attributes(verbose=verbose)
    except Exception as ex:
        print(ex)


rrrr = reload_subs

IMPORT_TUPLES = [
    ('Config', None, False),
    ('detect', None, True),
    ('hots', None, True),
    ('smk', None, True),
    ('preproc', None, True),
]
"""
Regen Command:
    cd /home/joncrall/code/wbia/wbia/algo
    makeinit.py --modname=wbia.algo
"""
