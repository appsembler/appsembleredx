from celery.task import task
from celery.utils.log import get_task_logger


LOGGER = get_task_logger(__name__)


# @task()
# def sample_task(sample_parameter):
#     #do stuff here
#     pass
