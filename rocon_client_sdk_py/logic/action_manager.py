import ast
import os
import importlib.util
import glob, pathlib, sys

class ActionManager():
    def __init__(self, context, logger=None):
        self._context = context

        act_path = context.worker.act_def_paths
        self._act_path = act_path
        self._act_instances = self._dynamic_load_actions(act_path)


    def _dynamic_load_actions(self, act_path):
        """
            주어진 절대경로 act_path로 부터 action 클래스 인스턴스를 동적 생성한다.
            경로내의 action 정의 파일은 'action_xxx.py'의 규칙을 가져야한다.

        """
        act_instances = {}

        #TODO needs exeption handling

        sys.path.append(act_path)
        py_files = glob.glob(os.path.join(act_path, 'action_*.py'))
        for py_file in py_files:
            module_name = pathlib.Path(py_file).stem
            module = importlib.import_module(module_name)

            # path_name으로 부터 선언된 클래스 찾기 (내부 유일 클래스로 가정)
            act_class = None
            #path_name = act_path + '/' + filename
            with open(py_file, "rb") as src_stream:
                p = ast.parse(src_stream.read())
                classnames = [node.name for node in ast.walk(p) if isinstance(node, ast.ClassDef)]
                act_class = classnames[0]

            class_instance = getattr(module, act_class)
            act = class_instance()
            act_instances[act.name] = act
            print(act.name)


        return act_instances

    async def build_task(self, options={}):
        concert_task = {}

        print(options['name'])

        concert_task['name'] = options['name'] if options['name'] is not None else 'ConcertTask'
        concert_task['description'] = options['description'] if options['description'] is not None else 'Concert Task'
        concert_task['actions'] = []


        for act_key in self._act_instances:
            concert_task['actions'].append(await self._act_instances[act_key].on_define(self._context))

        return concert_task

    def find_action(self, func_name):
        """
        func_name (string)으로 action instance 찾아 리턴
        :return:
        """

        act = None
        for act_key in self._act_instances:
            if self._act_instances[act_key].func_name == func_name:
                return self._act_instances[act_key]

        return None

    async def run_func(self, func_name, args):
        act = self.find_action(func_name)
        result = await act.on_perform(self._context, args)
        return result