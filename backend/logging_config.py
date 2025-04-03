import logging

logger = None

def setup_logging(logfile_path = None):
    global logger
    if logger:
        return logger

    # Create a logger
    logger = logging.getLogger('shared_logger')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if logfile_path:
        # Create a file handler
        file_handler = logging.FileHandler(logfile_path)
        file_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the handler
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(file_handler)

    # Create a stream handler to print logs to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # Add the stream handler to the logger
    logger.addHandler(stream_handler)

    return logger