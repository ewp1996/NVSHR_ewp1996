import os

class Logger():
    def __init__(self):
        exists = os.path.exists("logfile.txt")
        if not exists:
            self.file = open("logfile.txt", 'w+')
            self.file.write("   Date        Time     Command\n")
            print("   Date        Time     Command\n")
        else:
            self.file = open("logfile.txt", "a+")
            
    def log(self, output):
        self.__init__()
        self.file.write(output)
        print(output) 

    def log_gesture(self, gesture_name, now):
        self.log(''.join((now.isoformat()[:10], "    ", now.isoformat()[12:19], 
                "    ", gesture_name ," \n")))

    def log_gesture_sequence(self, gesture_sequence, now, was_recognised):
        if was_recognised:
            ending = "] recognised"
        else:
            ending = "] not recognised"

        self.log_gesture("pattern: [" + ', '.join(gesture_sequence) + ending, now)

    def close(self):
        self.file.seek(0)
        self.file.close()
        os.remove("logfile.txt")
