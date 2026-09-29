class Lamport:
    def __init__(self, logger):
        self.timestamp = 0
        self.logger = logger

    def __clockwork_increment(self):
        self.timestemp += 1

    
    def __generate_log(self, event_type, timestemp, message):
        self.logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: {message}")


    def send_message(self, message=None):

        self.__clockwork_increment()
        self.__generate_log("SEND", self.timestemp, message)
        return ProcessMsg(
            message=message,
            timestemp=self.timestemp
        )

    def receive_message(self, process_msg):
        self.timestemp = max(self.timestemp, process_msg.timestemp) + 1
        self.__generate_log("RECEIVE", self.timestemp, process_msg.message)


    def execute_event(self):
        self.__clockwork_increment()
        self.__generate_log("EXEC", self.timestemp, "Internal event")