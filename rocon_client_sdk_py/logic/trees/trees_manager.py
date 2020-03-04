from .tasks_bootstrap import *
from .tasks_heart_beat import *
from .tasks_external_control import *
from .tasks_idle_status import *
from .tasks_busy_status import *
from .tasks_offline_error import *
from rocon_client_sdk_py.logic.context import Context
from .blackboard_manager import BlackboardManager
from .deco import CustomDecoBase

#from .tasks_test import *

USING_TEST_TREE = False


class BehaviorTreeManager():

    def __init__(self, context:Context):
        py_trees.logging.level = py_trees.logging.Level.DEBUG

        self._context = context
        #self._init_blackboard(context)
        self._blackboard_manager = BlackboardManager(context)

        self._root = self._create_root()
        self._tree = py_trees.trees.BehaviourTree(self._root)
        self._snapshot_visitor = py_trees.visitors.SnapshotVisitor()

        self._tree.add_pre_tick_handler(self._pre_tick_handler)
        self._tree.add_post_tick_handler(self._post_tick_handler)

        self._tree.visitors.append(self._snapshot_visitor)

        #actionDefinePaths, messageDefinePaths는 worker에서 참조해~
        self._properties = {}

        self.test_count = 0



        #TODO 제거?
        self._hooks = None

        self._task_hook_handler = None

    def _create_root(self):

        initWorker = TaskInitWorker()
        initTask = TaskInitTask()
        bootCheck = TaskBootCheck()

        bootstrapping = py_trees.composites.Sequence(
            name="bootstrapping",
            children=[initWorker, initTask, bootCheck]
        )

        is_booted = TaskIsBooted()

        bootstrap = py_trees.composites.Selector(
            name="bootstrap",
            children=[is_booted, bootstrapping]
        )

        until_success = py_trees.decorators.Condition(
            child=bootstrap,
            name="UntilSuccess"
        )

        repeater = py_trees.decorators.FailureIsRunning(
            child=self._create_node_activated(),
            #condition=self._on_repeater_check,
            name="Repeater"
        )

        if USING_TEST_TREE == False:
            root = py_trees.composites.Sequence(
                name="RootTree",
                #children=[until_success]
                #children=[repeater]
                children=[until_success, repeater]

                #children=[create_test_trees()]
            )
        else:

            root = py_trees.composites.Sequence(
                name="RootTree",
                #children = [create_test_trees()]
            )


        return root

    def _on_repeater_check(self):

        #반복 조건 확인
        #TODO 반복 조건 추가 필요 확인

        return True


    def _pre_tick_handler(self, tree):
        print("\n--------_pre_tick_handler %s--------\n" % tree.count)

    def _post_tick_handler(self, tree):

        '''
        print(
            "\n" + py_trees.display.unicode_tree(
                root=tree.root,
                visited=tree.visited,
                previously_visited=tree.previously_visited
            )
        )
        '''
        print("\n--------_post_tick_handler %s--------\n" % tree.count)

    def tick(self):
        self._tree.tick()

    def _create_node_activated(self):

        update_worker = TaskUpdateWorker()
        update_task = TaskUpdateTask()

        heart_beat = py_trees.composites.Sequence(
            name="heartBeat",
            children=[update_worker, update_task]
        )

        handle_control_message = TaskHandleControlMessage()

        external_condition = py_trees.composites.Selector(
            name="externalControl",
            children=[handle_control_message]
        )

        is_offline_status = TaskIsOfflineStatus()
        offline_status = py_trees.composites.Sequence(
            name="offlineStatus",
            children=[is_offline_status]
        )

        is_error_status = TaskIsErrorStatus()
        error_status = py_trees.composites.Sequence(
            name="errorStatus",
            children=[is_error_status]
        )

        bystatus = py_trees.composites.Sequence(
            name="byStatus",
            children=[self._create_node_idle_status(), self._create_node_busy_status(), offline_status, error_status]
        )

        activated = py_trees.composites.Sequence(
            name="activated",
            children=[heart_beat, external_condition, bystatus]
            #children=[heart_beat]
        )

        return activated

    def _create_node_idle_status(self):
        request_recommendation = TaskRequestRecommendation()
        get_ownership = TaskGetOwnership()
        fetch_new_report = py_trees.composites.Sequence(
            name="fetchNewReport",
            children=[request_recommendation, get_ownership]
        )

        initReportFromExistReport = TaskInitReportFromExistReport()

        init_report = py_trees.composites.Selector(
            name="initReport",
            children=[initReportFromExistReport, fetch_new_report]
        )

        is_idle = TaskIsIdleStatus()
        health_check = TaskHealthCheck()
        handle_first_revision = TaskHandleFirstRevision()
        start_report = TaskStartReport()

        idle_status = py_trees.composites.Sequence(
            name="idleStatus",
            children=[is_idle, health_check, init_report, handle_first_revision, start_report]
        )

        return idle_status

    def _create_node_busy_status(self):

        check_revision = TaskCheckRevision()
        process_instruction = TaskProcessInstruction()

        check_process_inst = py_trees.decorators.RunningIsFailure(
            name="checkProcessInstructin",
            child=process_instruction
        )

        check_revision_then_keep_processing = py_trees.composites.Sequence(
            name="checkRevisionThenKeepProcessing",
            children=[check_revision, check_process_inst]
        )

        rewind_when_running = DecoRewindWhenRunning(
            child=check_revision_then_keep_processing,
            name="RewindWhenRunning"
        )

        is_busy = TaskIsBusyStatus()
        validate_report = TaskValidateReport()
        finish_report = TaskFinishReport()

        busy_status = py_trees.composites.Sequence(
            name="busyStatus",
            children=[is_busy, validate_report, rewind_when_running, finish_report]
        )

        return busy_status

    @property
    def blackboard(self):
        return self._blackboard_manager

    @property
    def hooks(self):
        return self._hooks

    @hooks.setter
    def hooks(self, hooks):
        self._hooks = hooks

    def set_task_hook_handler(self, handler):
        self._task_hook_handler = handler

    def get_tree_id(self):
        #_tree의 id가 없으므로 고정 스트링 사용
        return "BehaviorTree by Rocon_python_sdk"

    def _get_category(self, qualified_name):
        idx = qualified_name.find('/')
        if idx != -1:
            return qualified_name[:idx]
        else:
            return qualified_name

    def _get_node_info(self, node:py_trees.behaviour.Behaviour):

        data = {
            'id': str(node.id),
            'category': self._get_category(node.qualified_name),
            'type': self._get_category(node.qualified_name),
            'name': node.name,
            'description': '',
            'properties':{}
        }

        children_leng = len(node.children)
        if children_leng > 1:
            data['children'] = []
            for child in node.children:
                data['children'].append(self._get_node_info(child))
        elif children_leng == 1:
            data['child'] = self._get_node_info(node.children[0])
        else:
            data['child'] = None

        return data


    def get_trees_info(self):
        dic_data = self._get_node_info(self._tree.root)
        return dic_data


    def _get_node_status(self, node:py_trees.behaviour.Behaviour, dic_data):

        is_open = self.check_visited(node.id)
        dic_data[str(node.id)]={
            'isOpen': is_open,
            'runningChild': len(node.children),
            'lastStatus': node.status.value
        }

        for child in node.children:
            dic_data = self._get_node_status(child, dic_data)

        return dic_data

    def get_trees_status(self):
        dic_data = {}
        dic_data = self._get_node_status(self._tree.root, dic_data)
        return dic_data

    def display_unicode_tree(self):
        print(
            py_trees.display.unicode_tree(
                self._root,
                visited=self._snapshot_visitor.visited,
                previously_visited=self._snapshot_visitor.visited
            )
        )

    def check_visited(self, node_id):
        visited=self._snapshot_visitor.visited
        result = node_id in visited
        return result


class DecoRewindWhenRunning(CustomDecoBase):

    def update(self):

        status = self.context.blackboard.get('NowProcessInstructionStatus')
        if status is None:
            status = py_trees.common.Status.RUNNING
        elif status is py_trees.common.Status.SUCCESS:
            pass
            print('success')

        return status