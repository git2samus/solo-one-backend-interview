from services.base import BaseService, ConflictError, ForbiddenError, NotFoundError, ServiceError
from services.meetings import MeetingService
from services.notes import NoteService
from services.tasks import TaskService
from services.users import UserService

SERVICE_CLASSES = (UserService, MeetingService, NoteService, TaskService)
