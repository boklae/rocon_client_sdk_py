import py_trees
from .constants import *
from rocon_client_sdk_py.logic.context import Context
from py_trees.decorators import Decorator


class CustomDecoBase(Decorator):

    @property
    def context(self) -> Context:
        blackboard = py_trees.blackboard.Client(name=MASTER_BLACKBOARD_NAME)
        blackboard.register_key(key=KEY_CONTEXT, access=py_trees.common.Access.READ)
        value = blackboard.get(KEY_CONTEXT)
        return value

