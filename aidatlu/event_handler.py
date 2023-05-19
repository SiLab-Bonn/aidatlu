def event_handler(self, raw_data: list) -> list:
    """ #TODO data format for now array with size 7 first 6 entries are from fifo and last is timestamp.
        #TODO Except for status updates during run all calculations should be after the run to minimize calculation time in while true loop.
        but pob. not so important I dont have huge np arrays.
    Args:
        raw_data (list): _description_

    Returns:
        list: _description_
    """
    self.log.info("Event handler")
    
    #loop/slice through data

    raw_data[:,6] = raw_data[:,6]*25/1000000000 # Transform timestamp to seconds.
    self.log.success("Done")
    return raw_data

def run_header(self, stuff) -> list:
    #creates makro list of run number.. 
    #timestamp
    pass