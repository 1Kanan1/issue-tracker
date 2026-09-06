class NotFoundError(Exception):
    def __init__(self, entity: str, entity_id):
        super().__init__(f"{entity} with id {entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id

class AlreadyExistsError(Exception):
    def __init__(self, entity: str, entity_id):
        super().__init__(f"{entity} with id {entity_id} already exists")
        self.entity = entity
        self.entity_id = entity_id

class ForbiddenError(Exception):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(detail)
