class CacheClass:
    
    def __init__(self, status, progress,result = "", error = "", message = "",processed_count = 1,total_count = 1):
        self.__status = status
        self.__progress = progress
        self.__result = result
        self.__error = error
        self.__message = message
        self.__processed_count = processed_count
        self.__total_count = total_count
        # self.__task_status = {"status":status,
        #                     "progress":progress,
        #                     "resule":result,
        #                     "error":error,
        #                     "message":message}
    
    def getStatus(self):
        return self.__status
    def getProgress(self):
        return self.__progress
    def getResult(self):
        return self.__result
    def getError(self):
        return self.__error
    def getMessage(self):
        return self.__message
    def getTotalCount(self):
        return self.__total_count
    def getProcessedCount(self):
        return self.__processed_count
    
    
    def setStatus(self, status):
        self.__status = status
    
    def setProgress(self, progress):
        self.__progress = progress
    
    def setResult(self, result):
        self.__result = result
    
    def setError(self, error):
        self.__error = error
        
    def setMessage(self, message):
        self.__message = message
        
    def setTotalCount(self, total_count):
        self.__total_count = total_count
        
    def setProcessedCount(self, processed_count):
        self.__processed_count = processed_count