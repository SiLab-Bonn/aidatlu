# Parse *.ini file and provide some methods to access data

class ConfigParser(object):
    def __init__(self, filename):
        with open(filename, "r") as in_file:
            parsed_cfg = {}
            for line in in_file.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                
                if line[0] == "[":
                    section = line[1:-1]
                    parsed_cfg[section] = {}
                elif line[0] != "#":
                    key = line.split("=")[0].strip()
                    value = line.split("=")[1].strip()
                    parsed_cfg[section][key] = value

        self.conf = parsed_cfg

    def get(self, section, key):
        return self.conf[section][key]

    def getint(self, section, key):
        return int(self.get(section, key))

    def getfloat(self, section, key):
        return float(self.get(section, key))
