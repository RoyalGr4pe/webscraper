from datetime import datetime
from inspect import getframeinfo, stack
from datetime import datetime
from .colours import colour
import inspect


class LogClass(object):
    def __init__(self):
        """
        Initilize so object can use self
        """
        self.line_break = "|\n"
        self.top = f"\n{colour.BOLD}{colour.WHITE}-------------------------------------------------------------------------\n"
        self.bottom = f"{colour.BOLD}{colour.WHITE}-------------------------------------------------------------------------"


    @staticmethod
    def staticmethod():
        print("""
        config
        ------
        file: file you want your logs in
        date_fmt: set the format of the date and time you want to be displayed in the log
        ptt: print to terminal. Set to true if you want logs in terminal
        clear_log: set to true if you want the log file to be erased before running
        _________________________________________________________________________________
        
        log
        ---
        msg: The message you want to display
        log_type: The custom name of your log
        _____________________________________        
        """)


    def config(
            self, 
            file: str = "logging.log", 
            date_fmt: str = "%H:%M:%S %d-%m-%Y", 
            ptt: bool = False, 
            clear_log: bool = False,
            colours: bool = False,
            keep_only_1000_logs = False
            ):
        """
        Configure logger with some settings
        """
        self.file = file
        self.ptt = ptt
        self.date_fmt = date_fmt
        self.keep_only_1000_logs = keep_only_1000_logs
        
        if clear_log:
            self.__clear_log()

        if not colours:
            colour.WHITE = ""
            colour.PURPLE = ""
            colour.CYAN = ""
            colour.DARKCYAN = ""
            colour.BLUE = ""
            colour.GREEN = ""
            colour.YELLOW = ""
            colour.RED = ""
            colour.MAGENTA = ""
            colour.BOLD = ""
            colour.UNDERLINE = ""
            colour.END = ""


    def __clear_log(self):
        """
        Clear the log file
        """
        with open(self.file, 'w') as file:
            file.truncate()

    
    def __main_log(self, caller, msg, items, log_type, log_colour, error):
        now = datetime.today()
        time = now.strftime(self.date_fmt)

        if self.ptt:
            print_log_message = self.__print_layout(caller=caller, error_colour=log_colour, log_type=log_type, message=msg, items=items, time=time, error=error)
            print(print_log_message)

        log_file_message = self.__log_file_layout(caller=caller, log_type=log_type, message=msg, time=time, items=items, error=error)
        with open(self.file, 'a') as file:
            file.write(log_file_message) 

        if self.keep_only_1000_logs:
           self.__delete_logs(start_line=2, end_line=1002)

    
    def __delete_logs(self, start_line, end_line):
        with open(self.file, "r+") as file:
            lines = file.readlines()

            # Ensure start_line and end_line are within the valid range
            num_lines = len(lines)

            if num_lines >= end_line + 1 - start_line:

                # Adjust start_line and end_line to be zero-indexed
                start_line -= 1
                end_line -= 1

                # Remove lines within the specified range
                del lines[start_line:start_line+1]

                file.seek(0)
                file.truncate()
                file.write("".join(lines))


    def __print_layout(self, caller, error_colour, log_type, message, items, time, error):     

        if items:
            item_info = f"| Items: {error_colour}"
            for index, item in enumerate(items):
                item_info += list(item.keys())[0] + f"{colour.WHITE}={error_colour}" + list(item.values())[0] + f"{colour.WHITE}"
                if index != len(items) - 1:
                    item_info += f", {error_colour}"
                else:
                    item_info += f"\n"
        else:
            item_info = ""

        error_names =   f"| [{error_colour}{log_type}{colour.WHITE}]"
        log_info =      f"| Log Info: {error_colour}{message}{colour.WHITE}\n"
        file_location = f"| [{colour.BLUE}{caller.filename}{colour.WHITE}:{colour.PURPLE}{caller.lineno}{colour.WHITE}]\n"
        time =          f"| [{colour.GREEN}{time}{colour.WHITE}]\n"
        
        if error:
            error_names += f"[{error_colour}{type(error).__name__}{colour.WHITE}]\n"
            error_info =   f"| Error: {error_colour}{error}{colour.WHITE}\n"
            return self.top + error_names + self.line_break + log_info + error_info + item_info + self.line_break + file_location + time + self.bottom
        else:
            error_names += "\n"
            return self.top + error_names + self.line_break + log_info + item_info + self.line_break + file_location + time + self.bottom


    def __log_file_layout(self, caller, log_type, message, time, items, error):
        if log_type == "ERROR" or log_type == "CRITICAL":
            message = f"[{time}] | {caller.filename}:{caller.lineno} | [{log_type}][{type(error).__name__}] | {message} | {error}"
        else:   
            message = f"[{time}] | {caller.filename}:{caller.lineno} | [{log_type}] | {message} |"
        for index, item in enumerate(items):
            message += f"{list(item.keys())[index]}: {list(item.values())[index]}, "

        
        return message + "\n"


    def log(self, msg, log_type, items = [], log_colour = colour.PURPLE, error = None):
        """
        Custom log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type=log_type, log_colour=log_colour, error=error)     


    def info(self, msg, items = [], error = None):
        """
        Info Log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type="INFO", log_colour=colour.CYAN, error=error)


    def debug(self, msg, items = [], error = None):
        """
        Debug Log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type="DEBUG", log_colour=colour.DARKCYAN, error=error)


    def warning(self, msg, items = [], error = None):
        """
        Warning Log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type="WARNING", log_colour=colour.YELLOW, error=error)


    def error(self, msg, items = [], error = None):
        """
        Error Log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type="ERROR", log_colour=colour.RED, error=error)


    def critical(self, msg, items = [], error = None):
        """
        Critical Log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type="CRITICAL", log_colour=colour.MAGENTA, error=error)


    def success(self, msg, items = [], error = None):
        """
        Success Log
        """
        caller = getframeinfo(stack()[1][0])
        self.__main_log(caller=caller, msg=msg, items=items, log_type="SUCCESS", log_colour=colour.GREEN, error=error)


logger = LogClass()