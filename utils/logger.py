import logging


def get_logger(
        log_format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        log_name='',
        log_file_info='info.log',
        log_file_error ='error.log',
        datefmt='%Y-%m-%d %H:%M:%S'):

    log = logging.getLogger(log_name)
    log_formatter = logging.Formatter(log_format, datefmt=datefmt)

    # comment this to suppress console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    log.addHandler(stream_handler)

    file_handler_info = logging.FileHandler(log_file_info, mode='a')
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    log.addHandler(file_handler_info)

    file_handler_error = logging.FileHandler(log_file_error, mode='a')
    file_handler_error.setFormatter(log_formatter)
    file_handler_error.setLevel(logging.ERROR)
    log.addHandler(file_handler_error)

    log.setLevel(logging.INFO)

    return log


logger = get_logger()




