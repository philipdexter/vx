import vx.args
import logging

if vx.parsed_args.log:
    logging.basicConfig(filename='log', format='%(levelname)s:%(message)s', level=logging.DEBUG)

debug = logging.debug
info = logging.info
warning = logging.warning
error = logging.error
